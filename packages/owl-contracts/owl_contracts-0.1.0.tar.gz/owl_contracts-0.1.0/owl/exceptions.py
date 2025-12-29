"""
Owl Library - Custom Exceptions

All exceptions inherit from OwlError for easy catching of library-specific errors.
"""


class OwlError(Exception):
    """Base exception for all Owl library errors."""
    pass


class OwlConfigurationError(OwlError):
    """Raised when the library is not properly configured."""
    
    def __init__(self, message: str = None, missing_key: str = None):
        if missing_key:
            message = (
                f"Missing configuration: '{missing_key}'. "
                f"Please call owl.configure({missing_key}='...') or set the "
                f"OWL_{missing_key.upper()} environment variable."
            )
        super().__init__(message or "Owl library is not configured properly.")
        self.missing_key = missing_key


class ContractNotFoundError(OwlError):
    """Raised when a contract address is invalid or not found on the blockchain."""
    
    def __init__(self, address: str, chain: str = "ethereum"):
        self.address = address
        self.chain = chain
        super().__init__(
            f"No contract found at address '{address}' on {chain}. "
            f"This address may be a wallet (EOA) instead of a smart contract, "
            f"or the contract is not deployed on this chain. "
            f"Please verify you're using a valid smart contract address."
        )


class ABINotFoundError(OwlError):
    """Raised when the contract ABI cannot be retrieved (contract not verified)."""
    
    def __init__(self, address: str, chain: str = "ethereum"):
        self.address = address
        self.chain = chain
        super().__init__(
            f"ABI not found for contract '{address}' on {chain}. "
            f"The contract may not be verified on the block explorer. "
            f"You can manually provide an ABI using owl.get_functions(address, abi=[...])."
        )


class FunctionNotFoundError(OwlError):
    """Raised when the requested function is not found in the contract ABI."""
    
    def __init__(self, function_name: str, address: str, available_functions: list = None):
        self.function_name = function_name
        self.address = address
        self.available_functions = available_functions or []
        
        msg = f"Function '{function_name}' not found in contract '{address}'."
        if self.available_functions:
            suggestions = ", ".join(self.available_functions[:5])
            msg += f" Available functions: {suggestions}"
            if len(self.available_functions) > 5:
                msg += f" ... and {len(self.available_functions) - 5} more."
        super().__init__(msg)


class InvalidInputError(OwlError):
    """Raised when input parameters don't match the function signature."""
    
    def __init__(self, function_name: str, expected: list, received: list, details: str = None):
        self.function_name = function_name
        self.expected = expected
        self.received = received
        
        expected_str = ", ".join([f"{p['name']}: {p['type']}" for p in expected]) if expected else "none"
        received_count = len(received) if received else 0
        
        msg = (
            f"Invalid inputs for function '{function_name}'. "
            f"Expected ({expected_str}), received {received_count} argument(s)."
        )
        if details:
            msg += f" Details: {details}"
        super().__init__(msg)


class HistoricalDataUnavailableError(OwlError):
    """Raised when historical data cannot be retrieved (archive node required)."""
    
    def __init__(self, block_number: int = None, message: str = None):
        self.block_number = block_number
        if message is None:
            message = (
                "Historical data is unavailable. This typically means you need an archive node "
                "to query data older than ~128 blocks. Please configure an archive node RPC URL "
                "or omit the date parameters to query current state."
            )
            if block_number:
                message = f"Cannot retrieve data for block {block_number}. " + message
        super().__init__(message)


class DateRangeError(OwlError):
    """Raised when date parameters are invalid."""
    
    def __init__(self, message: str = None, start_date: str = None, end_date: str = None):
        self.start_date = start_date
        self.end_date = end_date
        
        if message is None:
            if start_date and end_date:
                message = f"Invalid date range: start_date='{start_date}', end_date='{end_date}'."
            else:
                message = "Invalid date format. Please use YYYY-MM-DD format (e.g., '2024-01-15')."
        super().__init__(message)


class NetworkError(OwlError):
    """Raised when there's a network-related error communicating with the blockchain or API."""
    
    def __init__(self, message: str, original_error: Exception = None):
        self.original_error = original_error
        super().__init__(message)


class RateLimitError(OwlError):
    """Raised when API rate limits are exceeded."""
    
    def __init__(self, service: str = "Etherscan"):
        self.service = service
        super().__init__(
            f"Rate limit exceeded for {service} API. "
            f"Please wait a moment before retrying or upgrade your API plan."
        )
