"""
Owl Library - Configuration Management

Handles API keys, RPC endpoints, and chain-specific settings.
Configuration can be set programmatically or via environment variables.
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from .exceptions import OwlConfigurationError


# Etherscan V2 unified API endpoint
ETHERSCAN_V2_API = "https://api.etherscan.io/v2/api"

# Chain IDs for Etherscan V2 API
CHAIN_IDS = {
    "ethereum": 1,
    "goerli": 5,
    "sepolia": 11155111,
    "polygon": 137,
    "bsc": 56,
    "arbitrum": 42161,
    "optimism": 10,
    "avalanche": 43114,
    "fantom": 250,
    "base": 8453,
}

# Default public RPC endpoints (rate-limited, for testing only)
DEFAULT_RPC_URLS = {
    "ethereum": "https://ethereum.publicnode.com",
    "polygon": "https://polygon-bor-rpc.publicnode.com",
    "bsc": "https://bsc-rpc.publicnode.com",
    "arbitrum": "https://arbitrum-one-rpc.publicnode.com",
    "optimism": "https://optimism-rpc.publicnode.com",
    "avalanche": "https://avalanche-c-chain-rpc.publicnode.com",
    "fantom": "https://fantom-rpc.publicnode.com",
    "base": "https://base-rpc.publicnode.com",
}


@dataclass
class OwlConfig:
    """Configuration container for Owl library."""
    
    etherscan_api_key: Optional[str] = None
    rpc_url: Optional[str] = None
    chain: str = "ethereum"
    cache_abi: bool = True
    timeout: int = 30
    _is_configured: bool = field(default=False, repr=False)
    
    def __post_init__(self):
        # Load from environment variables if not set
        if self.etherscan_api_key is None:
            self.etherscan_api_key = os.environ.get("OWL_ETHERSCAN_API_KEY")
        
        if self.rpc_url is None:
            self.rpc_url = os.environ.get("OWL_RPC_URL")
        
        chain_from_env = os.environ.get("OWL_CHAIN")
        if chain_from_env:
            self.chain = chain_from_env.lower()
        
        self._is_configured = bool(self.etherscan_api_key and self.rpc_url)
    
    @property
    def explorer_api_url(self) -> str:
        """Get the Etherscan V2 API URL."""
        return ETHERSCAN_V2_API
    
    @property
    def chain_id(self) -> int:
        """Get the chain ID for the configured chain."""
        chain = self.chain.lower()
        if chain not in CHAIN_IDS:
            raise OwlConfigurationError(
                f"Unsupported chain: '{chain}'. Supported chains: {', '.join(CHAIN_IDS.keys())}"
            )
        return CHAIN_IDS[chain]
    
    def validate(self) -> None:
        """Validate that all required configuration is present."""
        if not self.etherscan_api_key:
            raise OwlConfigurationError(missing_key="etherscan_api_key")
        # RPC is optional for get_functions, only needed for get_data
        if self.chain.lower() not in CHAIN_IDS:
            raise OwlConfigurationError(
                f"Unsupported chain: '{self.chain}'. Supported chains: {', '.join(CHAIN_IDS.keys())}"
            )
    
    def get_default_rpc(self) -> Optional[str]:
        """Get a default public RPC URL for the chain (for testing only)."""
        return DEFAULT_RPC_URLS.get(self.chain.lower())


# Global configuration instance
_config: Optional[OwlConfig] = None


def configure(
    etherscan_api_key: Optional[str] = None,
    rpc_url: Optional[str] = None,
    chain: str = "ethereum",
    cache_abi: bool = True,
    timeout: int = 30,
) -> OwlConfig:
    """
    Configure the Owl library.
    
    Args:
        etherscan_api_key: API key for Etherscan (or compatible explorer).
                          Can also be set via OWL_ETHERSCAN_API_KEY env var.
        rpc_url: Web3 RPC endpoint URL (e.g., Infura, Alchemy).
                Can also be set via OWL_RPC_URL env var.
        chain: Blockchain network (default: "ethereum").
               Supported: ethereum, polygon, bsc, arbitrum, optimism, avalanche, fantom, base
        cache_abi: Whether to cache fetched ABIs locally (default: True).
        timeout: Request timeout in seconds (default: 30).
    
    Returns:
        OwlConfig: The configuration object.
    
    Raises:
        OwlConfigurationError: If required configuration is missing.
    
    Example:
        >>> import owl
        >>> owl.configure(
        ...     etherscan_api_key="YOUR_KEY",
        ...     rpc_url="https://mainnet.infura.io/v3/YOUR_PROJECT",
        ...     chain="ethereum"
        ... )
    """
    global _config
    
    _config = OwlConfig(
        etherscan_api_key=etherscan_api_key,
        rpc_url=rpc_url,
        chain=chain,
        cache_abi=cache_abi,
        timeout=timeout,
    )
    
    # Try to use default RPC if not provided
    if not _config.rpc_url:
        default_rpc = _config.get_default_rpc()
        if default_rpc:
            _config.rpc_url = default_rpc
            import warnings
            warnings.warn(
                f"Using public RPC endpoint for {chain}. This is rate-limited and for testing only. "
                f"Please set a dedicated RPC URL for production use.",
                UserWarning
            )
    
    _config.validate()
    _config._is_configured = True
    
    return _config


def get_config() -> OwlConfig:
    """
    Get the current configuration.
    
    Returns:
        OwlConfig: The current configuration object.
    
    Raises:
        OwlConfigurationError: If the library hasn't been configured.
    """
    global _config
    
    if _config is None:
        # Try to auto-configure from environment
        _config = OwlConfig()
        if _config._is_configured:
            _config.validate()
        else:
            raise OwlConfigurationError(
                "Owl library is not configured. Please call owl.configure() first or "
                "set OWL_ETHERSCAN_API_KEY and OWL_RPC_URL environment variables."
            )
    
    return _config


def reset_config() -> None:
    """Reset the configuration (useful for testing)."""
    global _config
    _config = None
