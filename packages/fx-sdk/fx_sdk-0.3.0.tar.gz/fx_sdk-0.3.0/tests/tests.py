import unittest
import sys
import os
from unittest.mock import MagicMock, patch
from decimal import Decimal

# Add parent directory to path to use local development code
# Must be first to override installed package
local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if local_path not in sys.path:
    sys.path.insert(0, local_path)

# Remove fx_sdk from cache if already imported (to force reload from local code)
if 'fx_sdk' in sys.modules:
    del sys.modules['fx_sdk']
if 'fx_sdk.client' in sys.modules:
    del sys.modules['fx_sdk.client']
if 'fx_sdk.constants' in sys.modules:
    del sys.modules['fx_sdk.constants']
if 'fx_sdk.exceptions' in sys.modules:
    del sys.modules['fx_sdk.exceptions']
if 'fx_sdk.utils' in sys.modules:
    del sys.modules['fx_sdk.utils']

from fx_sdk.client import ProtocolClient
from fx_sdk import utils
from fx_sdk.exceptions import ConfigurationError, TransactionFailedError, ContractCallError

class TestFXProtocolSDK(unittest.TestCase):
    """Test suite for the f(x) Protocol Python SDK."""

    def setUp(self):
        """Set up a client with mocked internals."""
        self.rpc_url = "http://localhost:8545"
        self.private_key = "0x" + "1" * 64
        
        # Patch Web3 inside the client module to avoid validation errors
        with patch('fx_sdk.client.Web3') as MockWeb3:
            self.mock_w3 = MockWeb3.return_value
            self.mock_w3.is_connected.return_value = True
            self.mock_w3.isConnected.return_value = True
            
            self.mock_w3.eth = MagicMock()
            self.mock_w3.eth.get_transaction_count.return_value = 0
            self.mock_w3.eth.gas_price = 20000000000 
            self.mock_w3.eth.wait_for_transaction_receipt.return_value = MagicMock(status=1)
            
            self.mock_w3.eth.account = MagicMock()
            self.mock_w3.eth.account.sign_transaction.return_value = MagicMock(
                rawTransaction=b"signed_tx_data"
            )
            self.mock_w3.eth.send_raw_transaction.return_value = MagicMock(
                hex=lambda: "0x" + "a" * 64
            )

            self.client = ProtocolClient(
                rpc_url=self.rpc_url,
                private_key=self.private_key
            )

    def test_unit_conversions(self):
        """Test the utility conversion functions."""
        print("\n🧪 Testing Unit Conversions...")
        wei = utils.decimal_to_wei(1.5, 18)
        print(f"  - 1.5 ETH -> {wei} Wei")
        self.assertEqual(wei, 1500000000000000000)
        
        dec = utils.wei_to_decimal(1500000000000000000, 18)
        print(f"  - {wei} Wei -> {dec} ETH")
        self.assertEqual(dec, Decimal("1.5"))

    def test_client_initialization(self):
        """Test client setup and address parsing."""
        print("\n🧪 Testing Client Initialization...")
        expected_addr = "0x19E7E376E7C213B7E7e7e46cc70A5dD086DAff2A"
        print(f"  - Derived Address: {self.client.address}")
        self.assertEqual(self.client.address, expected_addr)

    def test_read_balance(self):
        """Test reading balance with mocked contract."""
        print("\n🧪 Testing Balance Fetching...")
        mock_contract = MagicMock()
        mock_contract.functions.balanceOf.return_value.call.return_value = 100 * 10**18
        mock_contract.functions.decimals.return_value.call.return_value = 18
        
        with patch.object(self.mock_w3.eth, 'contract', return_value=mock_contract):
            balance = self.client.get_fxusd_balance()
            print(f"  - Mocked fxUSD Balance: {balance}")
            self.assertEqual(balance, Decimal("100"))

    def test_multi_output_parsing(self):
        """Test methods that return dictionaries parsed from contract tuples."""
        print("\n🧪 Testing Multi-Output Tuple Parsing...")
        
        # 1. Test Pool Manager Info
        mock_pool_manager = MagicMock()
        # Returns (collateralCapacity, collateralBalance, debtCapacity, debtBalance)
        mock_pool_manager.functions.getPoolInfo.return_value.call.return_value = [
            1000 * 10**18, 500 * 10**18, 2000 * 10**18, 100 * 10**18
        ]
        
        with patch.object(self.client, '_get_contract', return_value=mock_pool_manager):
            info = self.client.get_pool_manager_info("0x" + "5" * 40)
            print(f"  - Pool Info Parsed: {info}")
            self.assertEqual(info['collateral_capacity'], Decimal("1000"))
            self.assertEqual(info['debt_balance'], Decimal("100"))

        # 2. Test veFXN Locked Info
        # Returns (amount, end)
        self.client.vefxn.functions.locked.return_value.call.return_value = [50 * 10**18, 1734652800]
        lock_info = self.client.get_vefxn_locked_info()
        print(f"  - veFXN Lock Info Parsed: {lock_info}")
        self.assertEqual(lock_info['amount'], Decimal("50"))
        self.assertEqual(lock_info['end'], 1734652800)

    def test_aggregation_logic(self):
        """Test the balance aggregator across multiple tokens."""
        print("\n🧪 Testing Balance Aggregator (get_all_balances)...")
        
        # Mock get_token_balance to return varying amounts
        with patch.object(self.client, 'get_token_balance') as mock_balance:
            mock_balance.side_effect = lambda addr, acc: Decimal("10.0")
            
            balances = self.client.get_all_balances()
            print(f"  - Aggregated {len(balances)} tokens")
            self.assertIn("fxUSD", balances)
            self.assertEqual(balances["fxUSD"], Decimal("10.0"))

    def test_complex_swap_params(self):
        """Test the swap method parameter handling."""
        print("\n🧪 Testing Complex Swap Parameter Passing...")
        
        with patch.object(self.client, '_build_and_send_transaction', return_value="0xswaphash") as mock_send:
            # MultiPathConverter.convert(token_in, amount_in, encoding, routes)
            tx_hash = self.client.swap(
                token_in="0x" + "a" * 40,
                amount_in=1.5,
                encoding=123,
                routes=[1, 2, 3]
            )
            print(f"  - Swap Transaction Hash: {tx_hash}")
            self.assertEqual(tx_hash, "0xswaphash")
            mock_send.assert_called_once()

    def test_mint_f_token_via_gateway(self):
        """Test minting fToken via Gateway renaming."""
        print("\n🧪 Testing stETH Gateway (mint_f_token_via_gateway)...")
        with patch.object(self.client, '_build_and_send_transaction', return_value="0xgatewayhash") as mock_send:
            tx_hash = self.client.mint_f_token_via_gateway(1.0)
            print(f"  - Gateway Tx Hash: {tx_hash}")
            self.assertEqual(tx_hash, "0xgatewayhash")
            mock_send.assert_called_once()

    def test_position_and_peg_discovery(self):
        """Test V2 position and peg keeper info fetching."""
        print("\n🧪 Testing V2 Position & Peg Keeper Discovery...")
        
        # Mock Position Info
        mock_pm = MagicMock()
        mock_pm.functions.getPosition.return_value.call.return_value = [self.client.address, 100 * 10**18, 50 * 10**18]
        
        # Mock Peg Keeper
        mock_pk = MagicMock()
        mock_pk.functions.isActive.return_value.call.return_value = True
        mock_pk.functions.debtCeiling.return_value.call.return_value = 1000000 * 10**18
        mock_pk.functions.totalDebt.return_value.call.return_value = 500000 * 10**18

        def mock_get_contract_side_effect(name, address):
            if name == "pool_manager": return mock_pm
            if name == "peg_keeper": return mock_pk
            return MagicMock()

        with patch.object(self.client, '_get_contract', side_effect=mock_get_contract_side_effect):
            pos = self.client.get_position_info(123)
            print(f"  - Position 123: {pos}")
            self.assertEqual(pos['collateral'], Decimal("100"))
            
            peg = self.client.get_peg_keeper_info()
            print(f"  - Peg Keeper Status: {peg}")
            self.assertTrue(peg['is_active'])

    def test_write_transaction(self):
        """Test building and sending a transaction."""
        print("\n🧪 Testing Transaction Lifecycle (Build/Sign/Send)...")
        mock_func = MagicMock()
        mock_func.estimate_gas.return_value = 200000
        
        built_tx = {'gas': 200000, 'nonce': 0}
        mock_func.build_transaction.return_value = built_tx
        mock_func.buildTransaction.return_value = built_tx
            
        tx_hash = self.client._build_and_send_transaction(mock_func)
        print(f"  - Generated Tx Hash: {tx_hash}")
        self.assertTrue(tx_hash.startswith("0x"))

    def test_rebalance_pool_deposit(self):
        """Test rebalance pool deposit flow."""
        print("\n🧪 Testing Rebalance Pool Flow...")
        with patch.object(self.client, '_build_and_send_transaction', return_value="0xhash") as mock_send:
            tx_hash = self.client.deposit_to_rebalance_pool(
                pool_address="0x" + "2" * 40,
                amount=10.5
            )
            print(f"  - Rebalance Deposit Hash: {tx_hash}")
            self.assertEqual(tx_hash, "0xhash")
            mock_send.assert_called_once()

    def test_configuration_error(self):
        """Test that write operations fail without a private key."""
        print("\n🧪 Testing Safety Checks (Read-Only Mode)...")
        with patch('fx_sdk.client.Web3') as MockWeb3:
            MockWeb3.return_value.is_connected.return_value = True
            MockWeb3.return_value.isConnected.return_value = True
            
            ro_client = ProtocolClient(rpc_url=self.rpc_url)
            with self.assertRaises(ConfigurationError):
                print("  - Attempting write operation without key (expecting error)...")
                ro_client._build_and_send_transaction(MagicMock())
            print("  - Caught expected ConfigurationError ✅")

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 STARTING f(x) PROTOCOL SDK PRODUCTION TEST SUITE")
    print("="*50)
    unittest.main()
