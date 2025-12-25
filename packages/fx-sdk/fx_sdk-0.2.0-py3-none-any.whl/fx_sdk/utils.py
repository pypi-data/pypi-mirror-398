from decimal import Decimal
from typing import Union
from web3 import Web3

def wei_to_decimal(value: int, decimals: int = 18) -> Decimal:
    """
    Convert a Wei value to a human-readable Decimal.
    
    Args:
        value: The value in Wei.
        decimals: The number of decimals for the token (default 18).
        
    Returns:
        Decimal: The human-readable value.
    """
    return Decimal(value) / Decimal(10**decimals)

def decimal_to_wei(value: Union[int, float, Decimal, str], decimals: int = 18) -> int:
    """
    Convert a human-readable value to Wei.
    
    Args:
        value: The human-readable value.
        decimals: The number of decimals for the token (default 18).
        
    Returns:
        int: The value in Wei.
    """
    return int(Decimal(str(value)) * Decimal(10**decimals))

def format_balance(value: Decimal, symbol: str = "") -> str:
    """
    Format a decimal balance for display.
    
    Args:
        value: The decimal balance.
        symbol: Optional token symbol to append.
        
    Returns:
        str: Formatted string (e.g., "1.2345 ETH").
    """
    formatted = f"{value:,.4f}"
    return f"{formatted} {symbol}".strip() if symbol else formatted

def to_checksum_address(address: str) -> str:
    """
    Convert an address to checksum format.
    """
    try:
        # Web3 v6+
        return Web3.to_checksum_address(address)
    except AttributeError:
        # Web3 v5
        return Web3.toChecksumAddress(address)

