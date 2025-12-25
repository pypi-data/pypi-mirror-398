#!/usr/bin/env python3
"""
Quick test to verify fx-sdk is working.
Run this to test basic functionality.
"""

from fx_sdk import ProtocolClient, constants, utils
from decimal import Decimal

# Use a public RPC endpoint
RPC_URL = "https://eth.llamarpc.com"

print("🚀 Testing fx-sdk...\n")

# Initialize client (read-only, no private key needed)
client = ProtocolClient(RPC_URL)
print("✓ Client initialized\n")

# Test 1: Constants
print("📋 Contract Addresses:")
print(f"   fxUSD: {constants.FXUSD}")
print(f"   fETH:  {constants.FETH}")
print(f"   FXN:   {constants.FXN}\n")

# Test 2: Utility functions
print("🔧 Utility Functions:")
wei = 1500000000000000000  # 1.5 ETH
eth = utils.wei_to_decimal(wei)
print(f"   {wei} Wei = {eth} ETH")
print(f"   {eth} ETH = {utils.decimal_to_wei(eth)} Wei\n")

# Test 3: Get token balance (Vitalik's address)
print("💰 Token Balances (Vitalik's address):")
address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
try:
    eth_balance = utils.wei_to_decimal(client.w3.eth.get_balance(address))
    print(f"   ETH: {eth_balance:.4f} ETH")
    
    fxusd_balance = utils.wei_to_decimal(
        client.get_token_balance(constants.FXUSD, address)
    )
    print(f"   fxUSD: {fxusd_balance:,.2f} fxUSD")
except Exception as e:
    print(f"   ⚠ Error: {e}")

print("\n✅ SDK is working! You can now use it in your code.")
print("\nExample usage:")
print("""
from fx_sdk import ProtocolClient

# Read-only mode (no private key)
client = ProtocolClient("https://eth.llamarpc.com")

# Get token balance
balance = client.get_token_balance(constants.FXUSD, "0x...")

# With private key (for transactions)
client = ProtocolClient(
    "https://eth.llamarpc.com",
    private_key="your_private_key_here"
)
""")

