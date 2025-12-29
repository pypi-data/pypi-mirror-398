"""
Owl Library - Contract Interface

Core functionality for interacting with smart contracts:
- get_functions(): Retrieve function metadata from ABI
- get_data(): Call contract functions with optional time range
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from web3 import Web3
from web3.exceptions import ContractLogicError, BadFunctionCallOutput

from .config import get_config
from .abi_fetcher import fetch_abi
from .utils import (
    normalize_address,
    format_function_info,
    validate_date_range,
    datetime_to_block,
    parse_date,
)
from .exceptions import (
    FunctionNotFoundError,
    InvalidInputError,
    HistoricalDataUnavailableError,
    NetworkError,
    ContractNotFoundError,
)


def get_functions(
    contract_address: str,
    abi: Optional[List[Dict[str, Any]]] = None,
    include_events: bool = False,
    only_view: bool = False,
) -> List[Dict[str, Any]]:
    """
    Get all functions from a smart contract.
    
    Args:
        contract_address: The contract address (e.g., "0x...").
        abi: Optional ABI to use (fetched from explorer if not provided).
        include_events: Include events in the output (default: False).
        only_view: Only return view/pure functions (default: False).
    
    Returns:
        List of function definitions with their signatures, inputs, and outputs.
    
    Raises:
        ContractNotFoundError: If the contract address is invalid.
        ABINotFoundError: If the contract is not verified.
        OwlConfigurationError: If the library is not configured.
    
    Example:
        >>> import owl
        >>> owl.configure(etherscan_api_key="YOUR_KEY", rpc_url="...")
        >>> functions = owl.get_functions("0xdAC17F958D2ee523a2206206994597C13D831ec7")
        >>> for fn in functions:
        ...     print(f"{fn['name']}: {fn['inputs']} -> {fn['outputs']}")
    """
    # Normalize address
    try:
        contract_address = normalize_address(contract_address)
    except ValueError as e:
        raise ContractNotFoundError(contract_address, get_config().chain) from e
    
    # Fetch ABI if not provided
    if abi is None:
        abi = fetch_abi(contract_address)
    
    # Parse functions from ABI
    functions = []
    
    for item in abi:
        item_type = item.get("type", "")
        
        # Filter by type
        if item_type == "function":
            func_info = format_function_info(item)
            
            # Apply view filter if requested
            if only_view and not func_info["is_view"]:
                continue
            
            functions.append(func_info)
        
        elif item_type == "event" and include_events:
            functions.append({
                "name": item.get("name", ""),
                "type": "event",
                "inputs": [
                    {
                        "name": inp.get("name", ""),
                        "type": inp.get("type", ""),
                        "indexed": inp.get("indexed", False),
                    }
                    for inp in item.get("inputs", [])
                ],
            })
    
    # Warn if no functions found
    if not functions and not abi:
        import warnings
        warnings.warn(
            f"No ABI found for contract {contract_address}. "
            f"The contract may not be verified on Etherscan.",
            UserWarning
        )
    elif not functions:
        import warnings
        warnings.warn(
            f"No functions found in ABI for contract {contract_address}. "
            f"The ABI may only contain events, errors, or other non-function items.",
            UserWarning
        )
    
    return functions


def get_data(
    contract_address: str,
    function_name: str,
    inputs: Optional[List[Any]] = None,
    start: Optional[Union[str, int]] = None,
    end: Optional[Union[str, int]] = None,
    block_number: Optional[int] = None,
    abi: Optional[List[Dict[str, Any]]] = None,
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Call a contract function and get the result.
    
    Args:
        contract_address: The contract address (e.g., "0x...").
        function_name: Name of the function to call.
        inputs: List of input arguments for the function (default: []).
        start: Start of range - can be:
            - Block number (int): e.g., 21000000
            - Date string (str): e.g., "2025-12-01" or "2025-12-01 14:30:00"
        end: End of range - can be:
            - Block number (int): e.g., 21100000
            - Date string (str): e.g., "2025-12-02"
        block_number: Specific block number to query (single point, not range).
        abi: Optional ABI to use (fetched from explorer if not provided).
    
    Returns:
        - If no range: Single result dict with "result", "block", and "timestamp" keys.
        - If range: List of result dicts with "result", "block", and "timestamp" keys.
    
    Raises:
        ContractNotFoundError: If the contract address is invalid.
        FunctionNotFoundError: If the function doesn't exist in the ABI.
        InvalidInputError: If inputs don't match the function signature.
        HistoricalDataUnavailableError: If historical data requires an archive node.
        DateRangeError: If date format/range is invalid.
    
    Example:
        >>> # Current state
        >>> result = owl.get_data("0x...", "balanceOf", ["0xabc..."])
        
        >>> # With date range
        >>> results = owl.get_data("0x...", "balanceOf", ["0xabc..."],
        ...     start="2024-01-01", end="2024-06-30")
        
        >>> # With block range
        >>> results = owl.get_data("0x...", "balanceOf", ["0xabc..."],
        ...     start=21000000, end=21100000)
    """
    config = get_config()
    inputs = inputs or []
    
    # Normalize address
    try:
        contract_address = normalize_address(contract_address)
    except ValueError as e:
        raise ContractNotFoundError(contract_address, config.chain) from e
    
    # Fetch ABI if not provided
    if abi is None:
        abi = fetch_abi(contract_address)
    
    # Find the function in ABI
    function_abi = None
    available_functions = []
    
    for item in abi:
        if item.get("type") == "function":
            fn_name = item.get("name", "")
            available_functions.append(fn_name)
            if fn_name == function_name:
                function_abi = item
                break
    
    if function_abi is None:
        raise FunctionNotFoundError(function_name, contract_address, available_functions)
    
    # Validate inputs
    expected_inputs = function_abi.get("inputs", [])
    if len(inputs) != len(expected_inputs):
        raise InvalidInputError(function_name, expected_inputs, inputs)
    
    # Connect to Web3
    try:
        w3 = Web3(Web3.HTTPProvider(config.rpc_url, request_kwargs={"timeout": config.timeout}))
        if not w3.is_connected():
            raise NetworkError(f"Failed to connect to RPC endpoint: {config.rpc_url}")
    except Exception as e:
        raise NetworkError(f"Web3 connection error: {str(e)}")
    
    # Create contract instance
    contract = w3.eth.contract(address=contract_address, abi=abi)
    
    # Get the contract function
    try:
        contract_function = getattr(contract.functions, function_name)
    except AttributeError:
        raise FunctionNotFoundError(function_name, contract_address, available_functions)
    
    # Determine blocks to query
    if start is not None or end is not None:
        # Range query - convert start/end to block numbers
        return _query_range(w3, contract_function, inputs, start, end)
    elif block_number is not None:
        # Query specific block
        return _query_single_block(w3, contract_function, inputs, block_number)
    else:
        # Query latest block
        return _query_single_block(w3, contract_function, inputs, "latest")


def _query_single_block(
    w3: Web3,
    contract_function,
    inputs: List[Any],
    block_identifier: Union[int, str],
) -> Dict[str, Any]:
    """Query a contract function at a specific block."""
    try:
        if inputs:
            result = contract_function(*inputs).call(block_identifier=block_identifier)
        else:
            result = contract_function().call(block_identifier=block_identifier)
        
        # Get block info
        if block_identifier == "latest":
            block = w3.eth.get_block("latest")
            block_number = block["number"]
            timestamp = datetime.fromtimestamp(block["timestamp"], tz=timezone.utc).isoformat()
        else:
            block = w3.eth.get_block(block_identifier)
            block_number = block_identifier
            timestamp = datetime.fromtimestamp(block["timestamp"], tz=timezone.utc).isoformat()
        
        return {
            "result": _format_result(result),
            "block": block_number,
            "timestamp": timestamp,
        }
    
    except ContractLogicError as e:
        raise InvalidInputError(
            function_name="(contract call)",
            expected=[],
            received=inputs,
            details=f"Contract reverted: {str(e)}"
        )
    except BadFunctionCallOutput as e:
        raise InvalidInputError(
            function_name="(contract call)",
            expected=[],
            received=inputs,
            details=f"Bad function output: {str(e)}"
        )
    except Exception as e:
        error_msg = str(e).lower()
        if "missing trie node" in error_msg or "pruned" in error_msg:
            raise HistoricalDataUnavailableError(
                block_number=block_identifier if isinstance(block_identifier, int) else None
            )
        raise NetworkError(f"Contract call failed: {str(e)}")


def _query_range(
    w3: Web3,
    contract_function,
    inputs: List[Any],
    start: Optional[Union[str, int]],
    end: Optional[Union[str, int]],
) -> List[Dict[str, Any]]:
    """Query a contract function over a block or date range."""
    
    # Convert start to block number
    if start is None:
        start_block = 0
    elif isinstance(start, int):
        # Already a block number
        start_block = start
    else:
        # Date string - convert to block
        start_dt = parse_date(start)
        start_block = datetime_to_block(w3, start_dt)
    
    # Convert end to block number
    if end is None:
        end_block = w3.eth.block_number
    elif isinstance(end, int):
        # Already a block number
        end_block = end
    else:
        # Date string - convert to block
        end_dt = parse_date(end)
        end_block = datetime_to_block(w3, end_dt)
    
    # Sample blocks in the range (max 10 data points for speed)
    total_blocks = end_block - start_block
    if total_blocks <= 0:
        # Just query the end block
        return [_query_single_block(w3, contract_function, inputs, end_block)]
    
    # Calculate sample interval (10 samples = fast, add samples param if needed)
    max_samples = 10
    interval = max(1, total_blocks // max_samples)
    
    results = []
    current_block = start_block
    
    while current_block <= end_block:
        try:
            result = _query_single_block(w3, contract_function, inputs, current_block)
            results.append(result)
        except HistoricalDataUnavailableError:
            # Skip blocks that are unavailable (not an archive node)
            import warnings
            warnings.warn(
                f"Block {current_block} unavailable (archive node may be required). Skipping.",
                UserWarning
            )
        
        current_block += interval
    
    # Always include the end block if not already included
    if results and results[-1]["block"] != end_block:
        try:
            result = _query_single_block(w3, contract_function, inputs, end_block)
            results.append(result)
        except HistoricalDataUnavailableError:
            pass
    
    if not results:
        raise HistoricalDataUnavailableError(
            message="No historical data available for the specified date range. "
            "Please use an archive node RPC endpoint."
        )
    
    return results


def _format_result(result: Any) -> Any:
    """Format contract call result for JSON serialization."""
    if isinstance(result, bytes):
        return result.hex()
    elif isinstance(result, (list, tuple)):
        return [_format_result(item) for item in result]
    elif isinstance(result, dict):
        return {k: _format_result(v) for k, v in result.items()}
    elif hasattr(result, '__int__'):
        # Handle large integers (Web3 uses int for uint256)
        return int(result)
    else:
        return result
