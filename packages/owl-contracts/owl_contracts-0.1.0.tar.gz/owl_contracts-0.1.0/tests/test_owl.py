"""
Unit tests for Owl library.

Run with: python -m pytest tests/ -v
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock

# Import owl components
import owl
from owl.exceptions import (
    OwlConfigurationError,
    ContractNotFoundError,
    ABINotFoundError,
    FunctionNotFoundError,
    InvalidInputError,
    DateRangeError,
)
from owl.utils import (
    parse_date,
    normalize_address,
    format_solidity_type,
    validate_date_range,
)


# Sample ABI for testing
SAMPLE_ABI = [
    {
        "name": "balanceOf",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "name": "transfer",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "outputs": [{"name": "", "type": "bool"}],
    },
    {
        "name": "totalSupply",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
]


class TestConfiguration:
    """Test configuration management."""
    
    def setup_method(self):
        """Reset config before each test."""
        owl.reset_config()
    
    def test_configure_with_all_params(self):
        """Test full configuration."""
        config = owl.configure(
            etherscan_api_key="test_key",
            rpc_url="https://test.rpc",
            chain="ethereum",
        )
        assert config.etherscan_api_key == "test_key"
        assert config.rpc_url == "https://test.rpc"
        assert config.chain == "ethereum"
    
    def test_configure_missing_api_key(self):
        """Test error when API key is missing."""
        with pytest.raises(OwlConfigurationError) as exc_info:
            owl.configure(rpc_url="https://test.rpc")
        assert "etherscan_api_key" in str(exc_info.value)
    
    def test_configure_unsupported_chain(self):
        """Test error for unsupported chain."""
        with pytest.raises(OwlConfigurationError) as exc_info:
            owl.configure(
                etherscan_api_key="key",
                rpc_url="https://test.rpc",
                chain="unsupported_chain"
            )
        assert "Unsupported chain" in str(exc_info.value)


class TestUtils:
    """Test utility functions."""
    
    def test_parse_date_valid(self):
        """Test valid date parsing."""
        dt = parse_date("2024-01-15")
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15
    
    def test_parse_date_with_time(self):
        """Test date with time parsing."""
        dt = parse_date("2024-01-15 14:30:00")
        assert dt.hour == 14
        assert dt.minute == 30
    
    def test_parse_date_invalid(self):
        """Test invalid date raises error."""
        with pytest.raises(DateRangeError):
            parse_date("not-a-date")
    
    def test_normalize_address_valid(self):
        """Test valid address normalization."""
        addr = normalize_address("0xdac17f958d2ee523a2206206994597c13d831ec7")
        assert addr.startswith("0x")
        assert len(addr) == 42
    
    def test_normalize_address_without_prefix(self):
        """Test address without 0x prefix."""
        addr = normalize_address("dac17f958d2ee523a2206206994597c13d831ec7")
        assert addr.startswith("0x")
    
    def test_normalize_address_invalid(self):
        """Test invalid address raises error."""
        with pytest.raises(ValueError):
            normalize_address("invalid")
    
    def test_format_solidity_type_basic(self):
        """Test basic type formatting."""
        assert "256-bit" in format_solidity_type("uint256")
        assert "address" in format_solidity_type("address").lower()
    
    def test_format_solidity_type_array(self):
        """Test array type formatting."""
        result = format_solidity_type("uint256[]")
        assert "Array" in result
    
    def test_validate_date_range_valid(self):
        """Test valid date range."""
        start, end = validate_date_range("2024-01-01", "2024-06-30")
        assert start < end
    
    def test_validate_date_range_invalid_order(self):
        """Test error when start > end."""
        with pytest.raises(DateRangeError):
            validate_date_range("2024-12-01", "2024-01-01")


class TestGetFunctions:
    """Test get_functions functionality."""
    
    def setup_method(self):
        owl.reset_config()
        owl.configure(
            etherscan_api_key="test_key",
            rpc_url="https://test.rpc",
        )
    
    def test_get_functions_with_provided_abi(self):
        """Test getting functions with provided ABI."""
        functions = owl.get_functions(
            "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            abi=SAMPLE_ABI
        )
        assert len(functions) == 3
        
        names = [f["name"] for f in functions]
        assert "balanceOf" in names
        assert "transfer" in names
        assert "totalSupply" in names
    
    def test_get_functions_only_view(self):
        """Test filtering to only view functions."""
        functions = owl.get_functions(
            "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            abi=SAMPLE_ABI,
            only_view=True
        )
        # balanceOf and totalSupply are view, transfer is not
        assert len(functions) == 2
        names = [f["name"] for f in functions]
        assert "balanceOf" in names
        assert "totalSupply" in names
        assert "transfer" not in names
    
    def test_get_functions_includes_metadata(self):
        """Test that function metadata is complete."""
        functions = owl.get_functions(
            "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            abi=SAMPLE_ABI
        )
        
        balance_of = next(f for f in functions if f["name"] == "balanceOf")
        assert balance_of["is_view"] is True
        assert len(balance_of["inputs"]) == 1
        assert balance_of["inputs"][0]["type"] == "address"
        assert len(balance_of["outputs"]) == 1
        assert balance_of["outputs"][0]["type"] == "uint256"


class TestExceptions:
    """Test exception messages and attributes."""
    
    def test_function_not_found_error(self):
        """Test FunctionNotFoundError has helpful message."""
        err = FunctionNotFoundError(
            "unknownFunc",
            "0x123",
            ["balanceOf", "transfer", "approve"]
        )
        assert "unknownFunc" in str(err)
        assert "balanceOf" in str(err)
    
    def test_invalid_input_error(self):
        """Test InvalidInputError has details."""
        err = InvalidInputError(
            "transfer",
            [{"name": "to", "type": "address"}],
            ["0x123", 100, "extra"],
        )
        assert "transfer" in str(err)
        assert "address" in str(err)
    
    def test_contract_not_found_error(self):
        """Test ContractNotFoundError."""
        err = ContractNotFoundError("0xinvalid", "ethereum")
        assert "0xinvalid" in str(err)
        assert "ethereum" in str(err)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
