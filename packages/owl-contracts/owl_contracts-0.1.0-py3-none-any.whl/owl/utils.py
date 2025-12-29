"""
Owl Library - Utility Functions

Helper functions for date conversion, type formatting, and ABI parsing.
"""

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

from web3 import Web3

from .exceptions import DateRangeError, HistoricalDataUnavailableError


def parse_date(date_str: str) -> datetime:
    """
    Parse a date string into a datetime object.
    
    Supports formats:
        - YYYY-MM-DD (e.g., "2024-01-15")
        - YYYY-MM-DD HH:MM:SS (e.g., "2024-01-15 14:30:00")
        - ISO 8601 (e.g., "2024-01-15T14:30:00Z")
    
    Args:
        date_str: Date string to parse.
    
    Returns:
        datetime: Parsed datetime object (UTC).
    
    Raises:
        DateRangeError: If the date format is invalid.
    """
    if not date_str:
        raise DateRangeError("Date string cannot be empty.")
    
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            # Ensure UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    
    raise DateRangeError(
        f"Invalid date format: '{date_str}'. "
        f"Please use YYYY-MM-DD format (e.g., '2024-01-15')."
    )


def validate_date_range(start_date: Optional[str], end_date: Optional[str]) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Validate and parse a date range.
    
    Args:
        start_date: Start date string (optional).
        end_date: End date string (optional).
    
    Returns:
        Tuple of parsed datetime objects (or None if not provided).
    
    Raises:
        DateRangeError: If the range is invalid.
    """
    start_dt = parse_date(start_date) if start_date else None
    end_dt = parse_date(end_date) if end_date else None
    
    if start_dt and end_dt and start_dt > end_dt:
        raise DateRangeError(
            f"start_date ({start_date}) cannot be after end_date ({end_date}).",
            start_date=start_date,
            end_date=end_date
        )
    
    now = datetime.now(timezone.utc)
    if end_dt and end_dt > now:
        raise DateRangeError(
            f"end_date ({end_date}) cannot be in the future.",
            end_date=end_date
        )
    
    return start_dt, end_dt


def estimate_block_from_timestamp(w3: Web3, target_timestamp: int) -> int:
    """
    Estimate the block number closest to a given timestamp.
    Uses fast calculation based on average block time (~12 seconds for Ethereum).
    
    Args:
        w3: Web3 instance.
        target_timestamp: Unix timestamp to find block for.
    
    Returns:
        int: Estimated block number.
    
    Raises:
        HistoricalDataUnavailableError: If block data cannot be retrieved.
    """
    try:
        latest_block = w3.eth.get_block('latest')
        latest_number = latest_block['number']
        latest_timestamp = latest_block['timestamp']
        
        if target_timestamp >= latest_timestamp:
            return latest_number
        
        # Fast estimation: assume ~12 second block time for Ethereum
        seconds_ago = latest_timestamp - target_timestamp
        blocks_ago = seconds_ago // 12  # Ethereum averages ~12 second blocks
        
        estimated_block = max(0, latest_number - blocks_ago)
        return estimated_block
    
    except Exception as e:
        raise HistoricalDataUnavailableError(
            message=f"Failed to estimate block from timestamp: {str(e)}"
        )


def datetime_to_block(w3: Web3, dt: datetime) -> int:
    """
    Convert a datetime to a block number.
    
    Args:
        w3: Web3 instance.
        dt: Datetime object.
    
    Returns:
        int: Block number.
    """
    timestamp = int(dt.timestamp())
    return estimate_block_from_timestamp(w3, timestamp)


def format_solidity_type(solidity_type: str) -> str:
    """
    Format a Solidity type into a more readable description.
    
    Args:
        solidity_type: Solidity type string (e.g., "uint256", "address[]").
    
    Returns:
        str: Human-readable description.
    """
    type_descriptions = {
        "address": "Ethereum address (20 bytes)",
        "bool": "Boolean (true/false)",
        "string": "UTF-8 string",
        "bytes": "Dynamic byte array",
        "uint8": "Unsigned integer (0-255)",
        "uint16": "Unsigned integer (0-65535)",
        "uint32": "Unsigned integer (0-4294967295)",
        "uint64": "Unsigned integer (0-18446744073709551615)",
        "uint128": "Unsigned 128-bit integer",
        "uint256": "Unsigned 256-bit integer (most common for amounts)",
        "int8": "Signed integer (-128 to 127)",
        "int16": "Signed integer (-32768 to 32767)",
        "int32": "Signed integer",
        "int64": "Signed integer",
        "int128": "Signed 128-bit integer",
        "int256": "Signed 256-bit integer",
    }
    
    # Handle arrays
    if solidity_type.endswith("[]"):
        base_type = solidity_type[:-2]
        base_desc = type_descriptions.get(base_type, base_type)
        return f"Array of {base_desc}"
    
    # Handle fixed-size arrays
    if "[" in solidity_type and "]" in solidity_type:
        match = re.match(r"(.+)\[(\d+)\]", solidity_type)
        if match:
            base_type, size = match.groups()
            base_desc = type_descriptions.get(base_type, base_type)
            return f"Fixed array of {size} {base_desc}"
    
    # Handle bytes with size
    if solidity_type.startswith("bytes") and solidity_type[5:].isdigit():
        size = solidity_type[5:]
        return f"Fixed byte array ({size} bytes)"
    
    return type_descriptions.get(solidity_type, solidity_type)


def normalize_address(address: str) -> str:
    """
    Normalize an Ethereum address to checksum format.
    
    Args:
        address: Ethereum address string.
    
    Returns:
        str: Checksummed address.
    
    Raises:
        ValueError: If the address is invalid.
    """
    if not address:
        raise ValueError("Address cannot be empty.")
    
    address = address.strip()
    
    if not address.startswith("0x"):
        address = "0x" + address
    
    if len(address) != 42:
        raise ValueError(f"Invalid address length: {len(address)} (expected 42).")
    
    try:
        return Web3.to_checksum_address(address)
    except Exception as e:
        raise ValueError(f"Invalid Ethereum address: {address}. {str(e)}")


def format_function_info(abi_item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format an ABI function item into a clean, readable structure.
    
    Args:
        abi_item: ABI item dictionary.
    
    Returns:
        dict: Formatted function information.
    """
    inputs = []
    for inp in abi_item.get("inputs", []):
        inputs.append({
            "name": inp.get("name", ""),
            "type": inp.get("type", ""),
            "type_description": format_solidity_type(inp.get("type", "")),
        })
    
    outputs = []
    for out in abi_item.get("outputs", []):
        outputs.append({
            "name": out.get("name", ""),
            "type": out.get("type", ""),
            "type_description": format_solidity_type(out.get("type", "")),
        })
    
    return {
        "name": abi_item.get("name", ""),
        "type": abi_item.get("type", "function"),
        "stateMutability": abi_item.get("stateMutability", "nonpayable"),
        "inputs": inputs,
        "outputs": outputs,
        "is_view": abi_item.get("stateMutability") in ("view", "pure"),
        "is_payable": abi_item.get("stateMutability") == "payable",
    }
