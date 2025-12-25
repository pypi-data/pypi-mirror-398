#!/usr/bin/env python3
"""
Simple test script to verify fx-sdk installation and functionality.
This script tests read-only operations (no private key required).
"""

from fx_sdk import ProtocolClient, constants, utils
from decimal import Decimal

# Initialize client in read-only mode (no private key needed)
print("=" * 60)
print("Testing fx-sdk Installation")
print("=" * 60)

# Use a public RPC endpoint (you can replace with your own)
RPC_URL = "https://eth.llamarpc.com"  # Public Ethereum RPC

try:
    print("\n1. Initializing ProtocolClient (read-only mode)...")
    client = ProtocolClient(RPC_URL)
    print(f"   ✓ Client initialized successfully")
    print(f"   ✓ Connected to: {RPC_URL}")
    print(f"   ✓ Mode: Read-Only (no private key)")
    
    print("\n2. Testing contract address constants...")
    print(f"   ✓ fxUSD: {constants.FXUSD}")
    print(f"   ✓ fETH: {constants.FETH}")
    print(f"   ✓ rUSD: {constants.RUSD}")
    print(f"   ✓ FXN: {constants.FXN}")
    print(f"   ✓ veFXN: {constants.VEFXN}")
    
    print("\n3. Testing utility functions...")
    # Test Wei to Decimal conversion
    wei_value = 1500000000000000000  # 1.5 ETH in Wei
    decimal_value = utils.wei_to_decimal(wei_value)
    print(f"   ✓ Wei to Decimal: {wei_value} Wei = {decimal_value} ETH")
    
    # Test Decimal to Wei conversion
    human_value = Decimal("1.5")
    wei_result = utils.decimal_to_wei(human_value)
    print(f"   ✓ Decimal to Wei: {human_value} ETH = {wei_result} Wei")
    
    # Test address checksum
    test_address = "0x742d35cc6634c0532925a3b844bc9e2385c6b0e0"
    checksum_address = utils.to_checksum_address(test_address)
    print(f"   ✓ Checksum address: {checksum_address}")
    
    print("\n4. Testing contract read operations...")
    
    # Test getting fxUSD total supply
    try:
        total_supply_wei = client.get_token_total_supply(constants.FXUSD)
        total_supply = utils.wei_to_decimal(total_supply_wei)
        print(f"   ✓ fxUSD Total Supply: {total_supply:,.2f} fxUSD")
    except Exception as e:
        print(f"   ⚠ Could not fetch fxUSD supply: {e}")
    
    # Test getting token balance for a known address (Vitalik's address)
    vitalik_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    try:
        eth_balance_wei = client.w3.eth.get_balance(vitalik_address)
        eth_balance = utils.wei_to_decimal(eth_balance_wei)
        print(f"   ✓ ETH Balance for {vitalik_address[:10]}...: {eth_balance:.4f} ETH")
    except Exception as e:
        print(f"   ⚠ Could not fetch ETH balance: {e}")
    
    # Test getting fxUSD balance
    try:
        fxusd_balance_wei = client.get_token_balance(constants.FXUSD, vitalik_address)
        fxusd_balance = utils.wei_to_decimal(fxusd_balance_wei)
        print(f"   ✓ fxUSD Balance: {fxusd_balance:,.2f} fxUSD")
    except Exception as e:
        print(f"   ⚠ Could not fetch fxUSD balance: {e}")
    
    print("\n5. Testing V2 protocol queries...")
    
    # Test getting fxUSD V2 pool info
    try:
        pool_info = client.get_v2_pool_info()
        print(f"   ✓ V2 Pool Info retrieved")
        if pool_info:
            print(f"     - Pool address: {pool_info.get('pool_address', 'N/A')}")
            if 'total_supply' in pool_info:
                print(f"     - Total Supply: {pool_info['total_supply']:,.2f}")
    except Exception as e:
        print(f"   ⚠ Could not fetch V2 pool info: {e}")
    
    # Test getting savings APR
    try:
        apr = client.get_savings_apr()
        print(f"   ✓ Savings APR: {apr:.2f}%")
    except Exception as e:
        print(f"   ⚠ Could not fetch savings APR: {e}")
    
    print("\n6. Testing V1 legacy token queries...")
    
    # Test getting fETH info
    try:
        feth_total_supply_wei = client.get_token_total_supply(constants.FETH)
        feth_total_supply = utils.wei_to_decimal(feth_total_supply_wei)
        print(f"   ✓ fETH Total Supply: {feth_total_supply:,.2f} fETH")
    except Exception as e:
        print(f"   ⚠ Could not fetch fETH supply: {e}")
    
    # Test getting xETH info
    try:
        xeth_total_supply_wei = client.get_token_total_supply(constants.XETH)
        xeth_total_supply = utils.wei_to_decimal(xeth_total_supply_wei)
        print(f"   ✓ xETH Total Supply: {xeth_total_supply:,.2f} xETH")
    except Exception as e:
        print(f"   ⚠ Could not fetch xETH supply: {e}")
    
    print("\n7. Testing governance queries...")
    
    # Test getting FXN total supply
    try:
        fxn_total_supply_wei = client.get_token_total_supply(constants.FXN)
        fxn_total_supply = utils.wei_to_decimal(fxn_total_supply_wei)
        print(f"   ✓ FXN Total Supply: {fxn_total_supply:,.2f} FXN")
    except Exception as e:
        print(f"   ⚠ Could not fetch FXN supply: {e}")
    
    print("\n" + "=" * 60)
    print("✓ All tests completed!")
    print("=" * 60)
    print("\nNote: Some operations may fail if:")
    print("  - RPC endpoint is rate-limited or unavailable")
    print("  - Contract addresses have changed")
    print("  - Network connectivity issues")
    print("\nThe SDK is working correctly if you see multiple ✓ checkmarks above.")
    
except Exception as e:
    print(f"\n❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()

