"""
Owl Library - ABI Fetcher

Retrieves contract ABIs from Etherscan-compatible block explorers.
Implements caching to avoid repeated API calls.
"""

import json
import os
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests

from .config import get_config
from .exceptions import (
    ABINotFoundError,
    NetworkError,
    RateLimitError,
    ContractNotFoundError,
)
from .utils import normalize_address


# Cache directory for ABIs
CACHE_DIR = Path.home() / ".owl" / "abi_cache"


def _get_cache_path(address: str, chain: str) -> Path:
    """Get the cache file path for a contract ABI."""
    address = address.lower()
    filename = f"{chain}_{address}.json"
    return CACHE_DIR / filename


def _load_from_cache(address: str, chain: str) -> Optional[List[Dict[str, Any]]]:
    """Load ABI from local cache if available."""
    cache_path = _get_cache_path(address, chain)
    if cache_path.exists():
        try:
            with open(cache_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    return None


def _save_to_cache(address: str, chain: str, abi: List[Dict[str, Any]]) -> None:
    """Save ABI to local cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = _get_cache_path(address, chain)
    try:
        with open(cache_path, "w") as f:
            json.dump(abi, f)
    except IOError:
        pass  # Cache write failure is not critical


def _is_contract(address: str, w3=None) -> bool:
    """
    Check if an address is a contract by checking its bytecode.
    Returns True if it's a contract, False if it's an EOA (wallet).
    """
    try:
        from web3 import Web3
        from .config import get_config
        
        if w3 is None:
            config = get_config()
            w3 = Web3(Web3.HTTPProvider(config.rpc_url, request_kwargs={"timeout": 10}))
        
        code = w3.eth.get_code(Web3.to_checksum_address(address))
        # If code length > 2 (0x), it's a contract
        return len(code) > 2
    except Exception:
        # If we can't check, assume it might be a contract
        return True


# EIP-1967 storage slot for implementation address
EIP1967_IMPL_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"


def _get_proxy_implementation(address: str, w3=None) -> Optional[str]:
    """
    Check if the address is a proxy contract and get its implementation address.
    Uses EIP-1967 standard storage slot.
    
    Returns:
        Implementation address if it's a proxy, None otherwise.
    """
    try:
        from web3 import Web3
        from .config import get_config
        
        if w3 is None:
            config = get_config()
            w3 = Web3(Web3.HTTPProvider(config.rpc_url, request_kwargs={"timeout": 10}))
        
        checksum_addr = Web3.to_checksum_address(address)
        
        # Read the EIP-1967 implementation slot
        impl_bytes = w3.eth.get_storage_at(checksum_addr, EIP1967_IMPL_SLOT)
        
        # Convert to address (last 20 bytes of 32-byte value)
        impl_address = "0x" + impl_bytes.hex()[-40:]
        
        # Check if it's a valid address (not zero address)
        if impl_address != "0x" + "0" * 40:
            return Web3.to_checksum_address(impl_address)
        
        return None
    except Exception:
        return None


def fetch_abi(
    address: str,
    chain: Optional[str] = None,
    use_cache: bool = True,
) -> List[Dict[str, Any]]:
    """
    Fetch the ABI for a contract from the block explorer.
    
    Args:
        address: Contract address.
        chain: Blockchain network (uses configured chain if not specified).
        use_cache: Whether to use cached ABI if available (default: True).
    
    Returns:
        List[Dict]: The contract ABI as a list of dictionaries.
    
    Raises:
        ABINotFoundError: If the contract is not verified.
        NetworkError: If there's a network error.
        RateLimitError: If the API rate limit is exceeded.
        ContractNotFoundError: If the address is invalid.
    """
    config = get_config()
    chain = chain or config.chain
    
    # Normalize address
    try:
        address = normalize_address(address)
    except ValueError as e:
        raise ContractNotFoundError(address, chain) from e
    
    # Check cache first
    if use_cache and config.cache_abi:
        cached_abi = _load_from_cache(address, chain)
        if cached_abi is not None:
            return cached_abi
    
    # Fetch from explorer API (Etherscan V2) using getsourcecode
    # This gives us both ABI AND proxy implementation info
    api_url = config.explorer_api_url
    params = {
        "chainid": config.chain_id,
        "module": "contract",
        "action": "getsourcecode",
        "address": address,
        "apikey": config.etherscan_api_key,
    }
    
    try:
        response = requests.get(api_url, params=params, timeout=config.timeout)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise NetworkError(f"Request to {chain} explorer timed out.")
    except requests.exceptions.ConnectionError:
        raise NetworkError(f"Failed to connect to {chain} explorer.")
    except requests.exceptions.RequestException as e:
        raise NetworkError(f"Network error: {str(e)}", original_error=e)
    
    try:
        data = response.json()
    except json.JSONDecodeError:
        raise NetworkError(f"Invalid response from {chain} explorer.")
    
    # Handle API response
    status = data.get("status", "0")
    message = data.get("message", "")
    result = data.get("result", "")
    
    if status == "0":
        # Error response - check specific error messages
        result_lower = str(result).lower()
        message_lower = message.lower()
        
        # Invalid API key
        if "invalid api" in result_lower or "invalid api" in message_lower:
            from .exceptions import OwlConfigurationError
            raise OwlConfigurationError(
                f"Invalid Etherscan API key. Please get a valid key at https://etherscan.io/apis"
            )
        
        # Rate limit exceeded
        if "rate limit" in message_lower or "rate limit" in result_lower or "max rate limit" in result_lower:
            raise RateLimitError(f"{chain.title()}scan")
        
        # Contract not verified
        if "not verified" in result_lower or "contract source code not verified" in result_lower:
            raise ABINotFoundError(address, chain)
        
        # Invalid address
        if "invalid address" in result_lower:
            raise ContractNotFoundError(address, chain)
        
        # NOTOK message - likely API key issue
        if message == "NOTOK":
            from .exceptions import OwlConfigurationError
            raise OwlConfigurationError(
                f"Etherscan API error: {result}. Check your API key is valid."
            )
        
        # Generic error
        raise ABINotFoundError(address, chain)
    
    # Parse getsourcecode response (result is a list with one item)
    if not isinstance(result, list) or len(result) == 0:
        raise ABINotFoundError(address, chain)
    
    source_info = result[0]
    abi_string = source_info.get("ABI", "")
    implementation = source_info.get("Implementation", "")
    
    # Check if this is a proxy contract
    if implementation and implementation != address and implementation.startswith("0x"):
        # It's a proxy - fetch the implementation's ABI instead
        try:
            impl_abi = fetch_abi(implementation, chain, use_cache)
            # Cache under the proxy address too
            if use_cache and config.cache_abi:
                _save_to_cache(address, chain, impl_abi)
            return impl_abi
        except ABINotFoundError:
            pass  # Fall through to try the proxy's own ABI
    
    # Parse the ABI string
    # Handle "Contract source code not verified" and "Similar Match" cases
    if not abi_string:
        raise ABINotFoundError(address, chain)
    
    if abi_string == "Contract source code not verified":
        # Check if there's a similar contract match in the SourceCode field
        source_code = source_info.get("SourceCode", "")
        if not source_code:
            raise ABINotFoundError(address, chain)
        # Still no direct ABI, raise error
        raise ABINotFoundError(address, chain)
    
    try:
        abi = json.loads(abi_string)
    except json.JSONDecodeError:
        raise ABINotFoundError(address, chain)
    
    if not isinstance(abi, list):
        raise ABINotFoundError(address, chain)
    
    # Cache the ABI
    if use_cache and config.cache_abi:
        _save_to_cache(address, chain, abi)
    
    return abi


def clear_cache(address: Optional[str] = None, chain: Optional[str] = None) -> int:
    """
    Clear cached ABIs.
    
    Args:
        address: Specific address to clear (clears all if not specified).
        chain: Specific chain to clear (clears all if not specified).
    
    Returns:
        int: Number of cache entries cleared.
    """
    if not CACHE_DIR.exists():
        return 0
    
    count = 0
    
    if address:
        # Clear specific address
        config = get_config()
        chain = chain or config.chain
        cache_path = _get_cache_path(address, chain)
        if cache_path.exists():
            cache_path.unlink()
            count = 1
    else:
        # Clear all
        for cache_file in CACHE_DIR.glob("*.json"):
            if chain:
                if cache_file.name.startswith(f"{chain}_"):
                    cache_file.unlink()
                    count += 1
            else:
                cache_file.unlink()
                count += 1
    
    return count
