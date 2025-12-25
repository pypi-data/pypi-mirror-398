"""
Test suite for Curve Finance integration.

This test suite validates all Curve Finance methods in the ProtocolClient.
Tests use mocking to avoid requiring actual blockchain connections.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from decimal import Decimal
import sys
import os
from web3 import Web3

# Add parent directory to path to import local development code
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

from fx_sdk.client import ProtocolClient
from fx_sdk import constants
from fx_sdk.exceptions import ContractCallError, FXProtocolError


class TestCurveIntegration(unittest.TestCase):
    """Test suite for Curve Finance integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.rpc_url = "https://eth.llamarpc.com"
        self.private_key = "0x" + "1" * 64  # Dummy private key for testing
        
        # Mock Web3 instance
        self.mock_w3 = Mock(spec=Web3)
        self.mock_w3.is_address = Mock(return_value=True)
        self.mock_w3.eth = MagicMock()
        self.mock_w3.eth.contract = MagicMock()
        self.mock_w3.eth.wait_for_transaction_receipt = MagicMock()
        self.mock_w3.eth.get_transaction_receipt = MagicMock()
        
        # Mock account
        self.mock_account = MagicMock()
        self.mock_account.address = "0x7E5F4552091A69125d5DfCb7b8C2659029395Bdf"
        
        # Patch Web3 class to bypass provider validation
        with patch('fx_sdk.client.Web3', return_value=self.mock_w3):
            with patch('fx_sdk.client.Account.from_key', return_value=self.mock_account):
                self.client = ProtocolClient(
                    rpc_url=self.rpc_url,
                    private_key=self.private_key
                )
        
        # Test addresses
        self.pool_address = "0xE06A65e09Ae18096B99770A809BA175FA05960e2"  # ETH/FXN pool
        self.gauge_address = "0xA5250C540914E012E22e623275E290c4dC993D11"  # ETH/FXN gauge
        self.lp_token = "0xE06A65e09Ae18096B99770A809BA175FA05960e2"
        self.token_in = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"  # ETH placeholder
        self.token_out = constants.FXN
        self.user_address = "0x7E5F4552091A69125d5DfCb7b8C2659029395Bdf"
    
    def test_get_curve_pool_info(self):
        """Test getting Curve pool information."""
        # Mock pool contract
        mock_pool = MagicMock()
        mock_pool.functions.token.return_value.call.return_value = self.lp_token
        mock_pool.functions.coins.return_value.call.side_effect = [
            self.token_in,
            self.token_out
        ]
        mock_pool.functions.balances.return_value.call.side_effect = [
            10**18,  # 1 ETH
            100 * 10**18  # 100 FXN
        ]
        mock_pool.functions.get_virtual_price.return_value.call.return_value = 10**18
        mock_pool.functions.A.return_value.call.return_value = 100
        mock_pool.functions.fee.return_value.call.return_value = 3000000  # 0.03%
        
        # Mock ERC20 contracts for decimals
        mock_token_contract = MagicMock()
        mock_token_contract.functions.decimals.return_value.call.return_value = 18
        mock_lp_token_contract = MagicMock()
        mock_lp_token_contract.functions.decimals.return_value.call.return_value = 18
        
        def get_contract_side_effect(name, addr):
            if name == "curve_pool":
                return mock_pool
            elif name == "erc20":
                if addr == self.lp_token:
                    return mock_lp_token_contract
                else:
                    return mock_token_contract
            return mock_pool
        
        self.client._get_contract = MagicMock(side_effect=get_contract_side_effect)
        
        result = self.client.get_curve_pool_info(self.pool_address)
        
        self.assertIn("pool_address", result)
        self.assertIn("coins", result)
        self.assertIn("balances", result)
        self.assertIn("lp_token", result)
        self.assertEqual(result["lp_token"], self.lp_token)
        self.assertEqual(len(result["coins"]), 2)
    
    def test_get_curve_pool_balances(self):
        """Test getting Curve pool balances."""
        # Mock pool info
        with patch.object(self.client, 'get_curve_pool_info', return_value={
            "balances_decimal": [1.0, 100.0]
        }):
            balances = self.client.get_curve_pool_balances(self.pool_address)
            
            self.assertEqual(len(balances), 2)
            self.assertEqual(balances[0], Decimal("1.0"))
            self.assertEqual(balances[1], Decimal("100.0"))
    
    def test_get_curve_pool_virtual_price(self):
        """Test getting Curve pool virtual price."""
        # Mock pool contract
        mock_pool = MagicMock()
        mock_pool.functions.get_virtual_price.return_value.call.return_value = 10**18
        mock_pool.functions.token.return_value.call.return_value = self.lp_token
        
        mock_lp_token_contract = MagicMock()
        mock_lp_token_contract.functions.decimals.return_value.call.return_value = 18
        
        self.client._get_contract = MagicMock(side_effect=lambda name, addr: {
            "curve_pool": mock_pool,
            "erc20": mock_lp_token_contract
        }.get(name, mock_pool))
        
        vp = self.client.get_curve_pool_virtual_price(self.pool_address)
        
        self.assertIsInstance(vp, Decimal)
        self.assertEqual(vp, Decimal("1.0"))
    
    def test_get_curve_swap_rate(self):
        """Test calculating Curve swap rate."""
        # Mock pool contract
        mock_pool = MagicMock()
        mock_pool.functions.coins.return_value.call.side_effect = [
            self.token_in,
            self.token_out
        ]
        mock_pool.functions.get_dy.return_value.call.return_value = 100 * 10**18  # 100 FXN
        
        # Mock token contracts
        mock_token_in = MagicMock()
        mock_token_in.functions.decimals.return_value.call.return_value = 18
        mock_token_out = MagicMock()
        mock_token_out.functions.decimals.return_value.call.return_value = 18
        
        self.client._get_contract = MagicMock(side_effect=lambda name, addr: {
            "curve_pool": mock_pool,
            "erc20": mock_token_in if addr == self.token_in else mock_token_out
        }.get(name, mock_pool))
        
        amount_out = self.client.get_curve_swap_rate(
            pool_address=self.pool_address,
            token_in=self.token_in,
            token_out=self.token_out,
            amount_in=Decimal("1.0")
        )
        
        self.assertIsInstance(amount_out, Decimal)
        self.assertEqual(amount_out, Decimal("100.0"))
    
    def test_find_curve_pool(self):
        """Test finding a Curve pool for a token pair."""
        # Mock registry contracts
        mock_meta_registry = MagicMock()
        mock_meta_registry.functions.find_pool_for_coins.return_value.call.return_value = self.pool_address
        
        self.client._get_contract = MagicMock(return_value=mock_meta_registry)
        
        pool = self.client.find_curve_pool(self.token_in, self.token_out)
        
        self.assertEqual(pool, self.pool_address)
    
    def test_get_curve_pool_from_lp_token(self):
        """Test finding pool from LP token address."""
        # Mock registry contracts
        mock_meta_registry = MagicMock()
        mock_meta_registry.functions.get_pool_from_lp_token.return_value.call.return_value = self.pool_address
        
        self.client._get_contract = MagicMock(return_value=mock_meta_registry)
        
        pool = self.client.get_curve_pool_from_lp_token(self.lp_token)
        
        self.assertEqual(pool, self.pool_address)
    
    def test_get_curve_gauge_info(self):
        """Test getting Curve gauge information."""
        # Mock gauge contract
        mock_gauge = MagicMock()
        mock_gauge.functions.lp_token.return_value.call.return_value = self.lp_token
        mock_gauge.functions.totalSupply.return_value.call.return_value = 1000 * 10**18
        mock_gauge.functions.reward_count.return_value.call.return_value = 1
        mock_gauge.functions.reward_tokens.return_value.call.return_value = constants.CRV_TOKEN
        mock_gauge.functions.is_killed.return_value.call.return_value = False
        mock_gauge.functions.reward_data.return_value.call.return_value = (
            constants.CRV_TOKEN,
            "0x0000000000000000000000000000000000000000",  # distributor
            1234567890,  # period_finish
            10**18,  # rate
            1234567890,  # last_update
            10**18,  # integral
        )
        
        # Mock LP token contract
        mock_lp_token_contract = MagicMock()
        mock_lp_token_contract.functions.decimals.return_value.call.return_value = 18
        
        self.client._get_contract = MagicMock(side_effect=lambda name, addr: {
            "curve_gauge": mock_gauge,
            "erc20": mock_lp_token_contract
        }.get(name, mock_gauge))
        
        result = self.client.get_curve_gauge_info(self.gauge_address)
        
        self.assertIn("gauge_address", result)
        self.assertIn("lp_token", result)
        self.assertIn("reward_tokens", result)
        self.assertEqual(result["lp_token"], self.lp_token)
        self.assertEqual(len(result["reward_tokens"]), 1)
    
    def test_get_curve_gauge_balance(self):
        """Test getting staked balance in Curve gauge."""
        # Mock gauge contract
        mock_gauge = MagicMock()
        mock_gauge.functions.balanceOf.return_value.call.return_value = 100 * 10**18
        mock_gauge.functions.lp_token.return_value.call.return_value = self.lp_token
        
        # Mock LP token contract
        mock_lp_token_contract = MagicMock()
        mock_lp_token_contract.functions.decimals.return_value.call.return_value = 18
        
        self.client._get_contract = MagicMock(side_effect=lambda name, addr: {
            "curve_gauge": mock_gauge,
            "erc20": mock_lp_token_contract
        }.get(name, mock_gauge))
        
        balance = self.client.get_curve_gauge_balance(
            gauge_address=self.gauge_address,
            user_address=self.user_address
        )
        
        self.assertIsInstance(balance, Decimal)
        self.assertEqual(balance, Decimal("100.0"))
    
    def test_get_curve_gauge_rewards(self):
        """Test getting claimable rewards from Curve gauge."""
        # Mock gauge contract
        mock_gauge = MagicMock()
        mock_gauge.functions.reward_count.return_value.call.return_value = 1
        mock_gauge.functions.reward_tokens.return_value.call.return_value = constants.CRV_TOKEN
        mock_gauge.functions.claimable_reward.return_value.call.return_value = 50 * 10**18
        
        # Mock token contract
        mock_token_contract = MagicMock()
        mock_token_contract.functions.decimals.return_value.call.return_value = 18
        
        self.client._get_contract = MagicMock(side_effect=lambda name, addr: {
            "curve_gauge": mock_gauge,
            "erc20": mock_token_contract
        }.get(name, mock_gauge))
        
        rewards = self.client.get_curve_gauge_rewards(
            gauge_address=self.gauge_address,
            user_address=self.user_address
        )
        
        self.assertIsInstance(rewards, dict)
        self.assertIn(constants.CRV_TOKEN, rewards)
        self.assertEqual(rewards[constants.CRV_TOKEN], Decimal("50.0"))
    
    def test_get_curve_gauge_from_pool(self):
        """Test finding gauge address from pool address."""
        # Mock registry contracts
        mock_meta_registry = MagicMock()
        mock_meta_registry.functions.get_gauge.return_value.call.return_value = self.gauge_address
        
        self.client._get_contract = MagicMock(return_value=mock_meta_registry)
        
        gauge = self.client.get_curve_gauge_from_pool(self.pool_address)
        
        self.assertEqual(gauge, self.gauge_address)
    
    def test_curve_swap(self):
        """Test executing a Curve swap."""
        if not self.client.address:
            self.skipTest("Private key required for write operations")
        
        # Mock pool contract
        mock_pool = MagicMock()
        mock_pool.functions.coins.return_value.call.side_effect = [
            self.token_in,
            self.token_out
        ]
        mock_pool.functions.get_dy.return_value.call.return_value = 100 * 10**18
        
        # Mock token contracts
        mock_token_in = MagicMock()
        mock_token_in.functions.decimals.return_value.call.return_value = 18
        mock_token_in.functions.allowance.return_value.call.return_value = 0
        mock_token_in.functions.approve.return_value = MagicMock()
        
        mock_token_out = MagicMock()
        mock_token_out.functions.decimals.return_value.call.return_value = 18
        
        mock_pool.functions.exchange.return_value = MagicMock()
        
        self.client._get_contract = MagicMock(side_effect=lambda name, addr: {
            "curve_pool": mock_pool,
            "erc20": mock_token_in if addr == self.token_in else mock_token_out
        }.get(name, mock_pool))
        
        # Mock transaction building
        self.client._build_and_send_transaction = MagicMock(return_value="0x" + "a" * 64)
        
        tx_hash = self.client.curve_swap(
            pool_address=self.pool_address,
            token_in=self.token_in,
            token_out=self.token_out,
            amount_in=Decimal("1.0")
        )
        
        self.assertIsInstance(tx_hash, str)
        self.assertTrue(tx_hash.startswith("0x"))
    
    def test_curve_add_liquidity(self):
        """Test adding liquidity to a Curve pool."""
        if not self.client.address:
            self.skipTest("Private key required for write operations")
        
        # Mock pool contract
        mock_pool = MagicMock()
        mock_pool.functions.coins.return_value.call.side_effect = [
            self.token_in,
            self.token_out
        ]
        mock_pool.functions.token.return_value.call.return_value = self.lp_token
        mock_pool.functions.calc_token_amount.return_value.call.return_value = 10**18
        
        # Mock token contracts
        mock_token_contract = MagicMock()
        mock_token_contract.functions.decimals.return_value.call.return_value = 18
        mock_token_contract.functions.allowance.return_value.call.return_value = 0
        mock_token_contract.functions.approve.return_value = MagicMock()
        
        mock_lp_token_contract = MagicMock()
        mock_lp_token_contract.functions.decimals.return_value.call.return_value = 18
        
        mock_pool.functions.add_liquidity.return_value = MagicMock()
        
        self.client._get_contract = MagicMock(side_effect=lambda name, addr: {
            "curve_pool": mock_pool,
            "erc20": mock_token_contract
        }.get(name, mock_pool))
        
        # Mock transaction building
        self.client._build_and_send_transaction = MagicMock(return_value="0x" + "a" * 64)
        
        tx_hash = self.client.curve_add_liquidity(
            pool_address=self.pool_address,
            amounts=[Decimal("1.0"), Decimal("100.0")]
        )
        
        self.assertIsInstance(tx_hash, str)
        self.assertTrue(tx_hash.startswith("0x"))
    
    def test_curve_remove_liquidity(self):
        """Test removing liquidity from a Curve pool."""
        if not self.client.address:
            self.skipTest("Private key required for write operations")
        
        # Mock pool contract
        mock_pool = MagicMock()
        mock_pool.functions.token.return_value.call.return_value = self.lp_token
        mock_pool.functions.coins.return_value.call.side_effect = [
            self.token_in,
            self.token_out
        ]
        
        # Mock token contracts
        mock_token_contract = MagicMock()
        mock_token_contract.functions.decimals.return_value.call.return_value = 18
        
        mock_lp_token_contract = MagicMock()
        mock_lp_token_contract.functions.decimals.return_value.call.return_value = 18
        mock_lp_token_contract.functions.allowance.return_value.call.return_value = 0
        mock_lp_token_contract.functions.approve.return_value = MagicMock()
        
        mock_pool.functions.remove_liquidity.return_value = MagicMock()
        
        self.client._get_contract = MagicMock(side_effect=lambda name, addr: {
            "curve_pool": mock_pool,
            "erc20": mock_token_contract if addr != self.lp_token else mock_lp_token_contract
        }.get(name, mock_pool))
        
        # Mock transaction building
        self.client._build_and_send_transaction = MagicMock(return_value="0x" + "a" * 64)
        
        tx_hash = self.client.curve_remove_liquidity(
            pool_address=self.pool_address,
            lp_token_amount=Decimal("10.0")
        )
        
        self.assertIsInstance(tx_hash, str)
        self.assertTrue(tx_hash.startswith("0x"))
    
    def test_curve_stake_lp_tokens(self):
        """Test staking LP tokens in a Curve gauge."""
        if not self.client.address:
            self.skipTest("Private key required for write operations")
        
        # Mock gauge contract
        mock_gauge = MagicMock()
        mock_gauge.functions.lp_token.return_value.call.return_value = self.lp_token
        mock_gauge.functions.deposit.return_value = MagicMock()
        
        # Mock LP token contract
        mock_lp_token_contract = MagicMock()
        mock_lp_token_contract.functions.decimals.return_value.call.return_value = 18
        mock_lp_token_contract.functions.allowance.return_value.call.return_value = 0
        mock_lp_token_contract.functions.approve.return_value = MagicMock()
        
        self.client._get_contract = MagicMock(side_effect=lambda name, addr: {
            "curve_gauge": mock_gauge,
            "erc20": mock_lp_token_contract
        }.get(name, mock_gauge))
        
        # Mock transaction building
        self.client._build_and_send_transaction = MagicMock(return_value="0x" + "a" * 64)
        
        tx_hash = self.client.curve_stake_lp_tokens(
            gauge_address=self.gauge_address,
            lp_token_amount=Decimal("100.0")
        )
        
        self.assertIsInstance(tx_hash, str)
        self.assertTrue(tx_hash.startswith("0x"))
    
    def test_curve_unstake_lp_tokens(self):
        """Test unstaking LP tokens from a Curve gauge."""
        if not self.client.address:
            self.skipTest("Private key required for write operations")
        
        # Mock gauge contract
        mock_gauge = MagicMock()
        mock_gauge.functions.lp_token.return_value.call.return_value = self.lp_token
        mock_gauge.functions.withdraw.return_value = MagicMock()
        
        # Mock LP token contract
        mock_lp_token_contract = MagicMock()
        mock_lp_token_contract.functions.decimals.return_value.call.return_value = 18
        
        self.client._get_contract = MagicMock(side_effect=lambda name, addr: {
            "curve_gauge": mock_gauge,
            "erc20": mock_lp_token_contract
        }.get(name, mock_gauge))
        
        # Mock transaction building
        self.client._build_and_send_transaction = MagicMock(return_value="0x" + "a" * 64)
        
        tx_hash = self.client.curve_unstake_lp_tokens(
            gauge_address=self.gauge_address,
            lp_token_amount=Decimal("50.0")
        )
        
        self.assertIsInstance(tx_hash, str)
        self.assertTrue(tx_hash.startswith("0x"))
    
    def test_curve_claim_gauge_rewards(self):
        """Test claiming rewards from a Curve gauge."""
        if not self.client.address:
            self.skipTest("Private key required for write operations")
        
        # Mock gauge contract
        mock_gauge = MagicMock()
        mock_gauge.functions.claim_rewards.return_value = MagicMock()
        
        self.client._get_contract = MagicMock(return_value=mock_gauge)
        
        # Mock transaction building
        self.client._build_and_send_transaction = MagicMock(return_value="0x" + "a" * 64)
        
        tx_hash = self.client.curve_claim_gauge_rewards(
            gauge_address=self.gauge_address
        )
        
        self.assertIsInstance(tx_hash, str)
        self.assertTrue(tx_hash.startswith("0x"))
    
    def test_curve_swap_without_private_key(self):
        """Test that write operations fail without private key."""
        # Create read-only client
        with patch('fx_sdk.client.Web3', return_value=self.mock_w3):
            read_only_client = ProtocolClient(rpc_url="https://eth.llamarpc.com")
        
        with self.assertRaises(FXProtocolError):
            read_only_client.curve_swap(
                pool_address=self.pool_address,
                token_in=self.token_in,
                token_out=self.token_out,
                amount_in=Decimal("1.0")
            )
    
    def test_invalid_pool_address(self):
        """Test error handling for invalid pool address."""
        # Mock to_checksum_address to raise an error for invalid addresses
        with patch('fx_sdk.utils.to_checksum_address', side_effect=ValueError("Invalid address")):
            with self.assertRaises((ContractCallError, ValueError)):
                self.client.get_curve_pool_info("invalid_address")
    
    def test_invalid_gauge_address(self):
        """Test error handling for invalid gauge address."""
        # Mock to_checksum_address to raise an error for invalid addresses
        with patch('fx_sdk.utils.to_checksum_address', side_effect=ValueError("Invalid address")):
            with self.assertRaises((ContractCallError, ValueError)):
                self.client.get_curve_gauge_info("invalid_address")
    
    # --- Curve Helper Methods Tests ---
    
    def test_get_curve_pools_from_registry(self):
        """Test getting all Curve pools from registry."""
        pools = self.client.get_curve_pools_from_registry()
        
        self.assertIsInstance(pools, dict)
        # Should have at least some Curve pools
        self.assertGreater(len(pools), 0)
    
    def test_get_curve_pool_from_registry(self):
        """Test getting a specific Curve pool from registry."""
        # Test by pool_id
        pool = self.client.get_curve_pool_from_registry(pool_id=6)  # ETH/FXN pool
        
        if pool:
            self.assertIn("pool_id", pool)
            self.assertIn("lp_token", pool)
            self.assertIn("fx_gauge", pool)
            self.assertEqual(pool["pool_id"], 6)
    
    def test_get_curve_gauge_balances_batch(self):
        """Test batch balance queries for multiple gauges."""
        # Mock gauge balance method
        with patch.object(self.client, 'get_curve_gauge_balance', side_effect=[
            Decimal("100.0"),
            Decimal("50.0")
        ]):
            balances = self.client.get_curve_gauge_balances_batch(
                gauge_addresses=[self.gauge_address, "0x" + "1" * 40],
                user_address=self.user_address
            )
            
            self.assertIsInstance(balances, dict)
            self.assertEqual(len(balances), 2)
            self.assertEqual(balances[self.gauge_address], Decimal("100.0"))
    
    def test_get_curve_gauge_rewards_batch(self):
        """Test batch reward queries for multiple gauges."""
        # Mock gauge rewards method
        with patch.object(self.client, 'get_curve_gauge_rewards', side_effect=[
            {constants.CRV_TOKEN: Decimal("10.0")},
            {constants.CRV_TOKEN: Decimal("5.0")}
        ]):
            rewards = self.client.get_curve_gauge_rewards_batch(
                gauge_addresses=[self.gauge_address, "0x" + "1" * 40],
                user_address=self.user_address
            )
            
            self.assertIsInstance(rewards, dict)
            self.assertEqual(len(rewards), 2)
            self.assertIn(constants.CRV_TOKEN, rewards[self.gauge_address])
    
    def test_get_user_curve_positions_summary(self):
        """Test getting comprehensive summary of user's Curve positions."""
        # Mock helper methods
        with patch.object(self.client, 'get_curve_pools_from_registry', return_value={
            "eth_fxn": {
                "pool_id": 6,
                "name": "ETH/FXN Curve Pool",
                "fx_gauge": self.gauge_address,
                "lp_token": self.lp_token
            }
        }):
            with patch.object(self.client, 'get_curve_gauge_balance', return_value=Decimal("100.0")):
                with patch.object(self.client, 'get_curve_gauge_rewards', return_value={
                    constants.CRV_TOKEN: Decimal("10.0")
                }):
                    with patch.object(self.client, 'get_curve_pool_from_lp_token', return_value=self.pool_address):
                        with patch.object(self.client, 'get_curve_pool_info', return_value={
                            "pool_address": self.pool_address,
                            "coins": [self.token_in, self.token_out]
                        }):
                            summary = self.client.get_user_curve_positions_summary(
                                user_address=self.user_address
                            )
                            
                            self.assertIn("user_address", summary)
                            self.assertIn("total_gauges", summary)
                            self.assertIn("total_staked", summary)
                            self.assertIn("total_rewards", summary)
                            self.assertIn("positions", summary)
                            self.assertEqual(summary["total_gauges"], 1)
                            self.assertEqual(summary["total_staked"], 100.0)
    
    def test_get_curve_gauge_apy(self):
        """Test calculating APY for a Curve gauge."""
        # Mock gauge info
        with patch.object(self.client, 'get_curve_gauge_info', return_value={
            "lp_token": self.lp_token,
            "total_supply": 1000 * 10**18,
            "reward_tokens": [constants.CRV_TOKEN],
            "reward_data": [{
                "token": constants.CRV_TOKEN,
                "rate": 10**18,  # 1 CRV per second
                "period_finish": 1234567890
            }]
        }):
            # Mock token contracts
            mock_token_contract = MagicMock()
            mock_token_contract.functions.decimals.return_value.call.return_value = 18
            
            self.client._get_contract = MagicMock(return_value=mock_token_contract)
            
            apy_data = self.client.get_curve_gauge_apy(self.gauge_address)
            
            self.assertIn("apy", apy_data)
            self.assertIn("apy_percentage", apy_data)
            self.assertIn("reward_rate", apy_data)
            self.assertIn("total_staked", apy_data)
            self.assertIsInstance(apy_data["apy"], Decimal)
    
    def test_get_all_curve_gauges_apy(self):
        """Test getting APY for all Curve gauges."""
        # Mock helper methods
        with patch.object(self.client, 'get_curve_pools_from_registry', return_value={
            "eth_fxn": {
                "pool_id": 6,
                "name": "ETH/FXN Curve Pool",
                "fx_gauge": self.gauge_address,
                "lp_token": self.lp_token
            }
        }):
            with patch.object(self.client, 'get_curve_gauge_info', return_value={
                "lp_token": self.lp_token,
                "total_supply": 1000 * 10**18,
                "reward_tokens": [constants.CRV_TOKEN],
                "reward_data": [{
                    "token": constants.CRV_TOKEN,
                    "rate": 10**18,
                    "period_finish": 1234567890
                }]
            }):
                # Mock token contracts
                mock_token_contract = MagicMock()
                mock_token_contract.functions.decimals.return_value.call.return_value = 18
                
                self.client._get_contract = MagicMock(return_value=mock_token_contract)
                
                # Mock get_curve_gauge_apy
                with patch.object(self.client, 'get_curve_gauge_apy', return_value={
                    "apy": Decimal("0.05"),
                    "apy_percentage": 5.0,
                    "reward_rate": 1.0,
                    "total_staked": 1000.0,
                    "reward_token": constants.CRV_TOKEN
                }):
                    apy_data = self.client.get_all_curve_gauges_apy()
                    
                    self.assertIsInstance(apy_data, dict)
                    if apy_data:
                        self.assertIn(self.gauge_address, apy_data)
                        self.assertIn("apy_percentage", apy_data[self.gauge_address])


if __name__ == '__main__':
    unittest.main()

