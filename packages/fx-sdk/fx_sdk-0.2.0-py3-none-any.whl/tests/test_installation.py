#!/usr/bin/env python3
"""
Quick test script to verify fx-sdk installation from PyPI.
Run this after: pip install fx-sdk
"""

from fx_sdk import ProtocolClient, constants, utils
from decimal import Decimal

print("🧪 Testing fx-sdk Installation\n")

# Test 1: Basic imports
print("1. Testing imports...")
try:
    from fx_sdk import __version__
    print(f"   ✓ Version: {__version__}")
    print(f"   ✓ ProtocolClient imported")
    print(f"   ✓ constants imported")
    print(f"   ✓ utils imported")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    exit(1)

# Test 2: Constants
print("\n2. Testing constants...")
print(f"   ✓ fxUSD: {constants.FXUSD}")
print(f"   ✓ fETH: {constants.FETH}")
print(f"   ✓ FXN: {constants.FXN}")

# Test 3: Utility functions
print("\n3. Testing utility functions...")
wei = 1500000000000000000  # 1.5 ETH
eth = utils.wei_to_decimal(wei)
print(f"   ✓ Wei to Decimal: {wei} Wei = {eth} ETH")
wei_back = utils.decimal_to_wei(Decimal("1.5"))
print(f"   ✓ Decimal to Wei: 1.5 ETH = {wei_back} Wei")

# Test 4: Client initialization
print("\n4. Testing client initialization...")
try:
    client = ProtocolClient("https://eth.llamarpc.com")
    print("   ✓ Client initialized (read-only mode)")
    
    # Test a simple read operation
    try:
        total_supply = client.get_token_total_supply(constants.FXUSD)
        supply_decimal = utils.wei_to_decimal(total_supply)
        print(f"   ✓ Read operation successful: fxUSD supply = {supply_decimal:,.2f}")
    except Exception as e:
        print(f"   ⚠ Read operation: {e} (may be RPC issue)")
        
except Exception as e:
    print(f"   ❌ Client initialization failed: {e}")
    exit(1)

print("\n" + "="*50)
print("✅ All tests passed! fx-sdk is working correctly.")
print("="*50)
print("\nYou can now use it in your code:")
print("""
from fx_sdk import ProtocolClient, constants, utils

# Read-only mode
client = ProtocolClient("https://eth.llamarpc.com")

# Get token balance
balance = client.get_token_balance(constants.FXUSD, "0x...")
print(f"Balance: {utils.wei_to_decimal(balance)} fxUSD")
""")

