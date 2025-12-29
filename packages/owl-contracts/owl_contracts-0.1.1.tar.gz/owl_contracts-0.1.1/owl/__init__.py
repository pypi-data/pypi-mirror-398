"""
Owl - Smart Contract Data Retrieval Library

A Python library to easily retrieve function metadata and data from any
smart contract on EVM-compatible blockchains.

Example:
    >>> import owl
    >>> owl.configure(
    ...     etherscan_api_key="YOUR_KEY",
    ...     rpc_url="https://eth.public-rpc.com"
    ... )
    >>> 
    >>> # Get all functions from a contract
    >>> functions = owl.get_functions("0xdAC17F958D2ee523a2206206994597C13D831ec7")
    >>> 
    >>> # Call a function and get data
    >>> result = owl.get_data("0x...", "balanceOf", ["0xabc..."])
"""

__version__ = "0.1.0"
__author__ = "Owl Contributors"

# Core configuration
from .config import configure, get_config, reset_config

# Main API functions
from .contract import get_functions, get_data

# ABI utilities
from .abi_fetcher import fetch_abi, clear_cache

# All exceptions
from .exceptions import (
    OwlError,
    OwlConfigurationError,
    ContractNotFoundError,
    ABINotFoundError,
    FunctionNotFoundError,
    InvalidInputError,
    HistoricalDataUnavailableError,
    DateRangeError,
    NetworkError,
    RateLimitError,
)


def show_functions(functions):
    """
    Pretty print the functions list in a readable format.
    
    Args:
        functions: List of function dicts from get_functions()
    """
    if not functions:
        print("No functions found.")
        return
    
    print(f"\n{'='*60}")
    print(f"  Found {len(functions)} functions")
    print(f"{'='*60}\n")
    
    for fn in functions:
        # Function header
        mutability = fn.get('stateMutability', 'unknown')
        emoji = "📖" if fn.get('is_view') else "✏️"
        print(f"{emoji} {fn['name']} [{mutability}]")
        
        # Inputs
        inputs = fn.get('inputs', [])
        if inputs:
            print(f"   📥 Inputs:")
            for inp in inputs:
                print(f"      • {inp['name'] or '(unnamed)'}: {inp['type']}")
        else:
            print(f"   📥 Inputs: none")
        
        # Outputs  
        outputs = fn.get('outputs', [])
        if outputs:
            print(f"   📤 Returns:")
            for out in outputs:
                print(f"      • {out['name'] or '(unnamed)'}: {out['type']}")
        
        print()


def list_functions(contract_address):
    """
    Quick helper to get and print all function names from a contract.
    
    Args:
        contract_address: The contract address
    
    Returns:
        List of function names (strings)
    """
    functions = get_functions(contract_address)
    names = [f['name'] for f in functions]
    
    print(f"\nFunctions in {contract_address[:10]}...{contract_address[-6:]}:")
    for name in names:
        print(f"  • {name}")
    print(f"\nTotal: {len(names)} functions\n")
    
    return names

# All exceptions
from .exceptions import (
    OwlError,
    OwlConfigurationError,
    ContractNotFoundError,
    ABINotFoundError,
    FunctionNotFoundError,
    InvalidInputError,
    HistoricalDataUnavailableError,
    DateRangeError,
    NetworkError,
    RateLimitError,
)

__all__ = [
    # Version
    "__version__",
    # Configuration
    "configure",
    "get_config",
    "reset_config",
    # Main API
    "get_functions",
    "get_data",
    # Helper functions
    "show_functions",
    "list_functions",
    # ABI utilities
    "fetch_abi",
    "clear_cache",
    # Exceptions
    "OwlError",
    "OwlConfigurationError",
    "ContractNotFoundError",
    "ABINotFoundError",
    "FunctionNotFoundError",
    "InvalidInputError",
    "HistoricalDataUnavailableError",
    "DateRangeError",
    "NetworkError",
    "RateLimitError",
]
