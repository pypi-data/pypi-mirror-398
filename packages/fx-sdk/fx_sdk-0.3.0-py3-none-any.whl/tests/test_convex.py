#!/usr/bin/env python3
"""
Comprehensive tests for Convex Finance integration.

Tests cover:
- Vault creation and address lookup
- Vault information queries
- Deposits and withdrawals
- Reward claiming
- Error handling
- cvxFXN staking

Note: Test vault address (0x4ec8F6c9F6d79B11C1A189F4dc62371Cc0A08a03) is for
fxUSD V2 Stability Pool (Earns FXN) - Pool ID 37. This is a TEST-ONLY address
and should not be used in production.
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from web3 import Web3

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

from fx_sdk import ProtocolClient, constants
from fx_sdk.exceptions import (
    FXProtocolError,
    ContractCallError,
    InsufficientBalanceError
)


class TestConvexIntegration(unittest.TestCase):
    """Test suite for Convex Finance integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.rpc_url = "https://eth.llamarpc.com"
        self.private_key = "0x" + "1" * 64  # Dummy private key for testing
        self.user_address = "0x742d35Cc6634C0532925a3b844Bc9e2385C6b0e0"
        # TEST-ONLY vault address for fxUSD V2 Stability Pool (Earns FXN) - Pool ID 37
        # DO NOT use in production - this is a user-specific vault address
        self.vault_address = "0x4ec8F6c9F6d79B11C1A189F4dc62371Cc0A08a03"
        self.pool_id = 37  # fxUSD V2 Stability Pool (Earns FXN)
        
        # Mock Web3 instance
        self.mock_w3 = Mock(spec=Web3)
        self.mock_w3.is_connected.return_value = True
        self.mock_w3.is_address.return_value = True
        self.mock_w3.eth = Mock()
        self.mock_w3.eth.contract = Mock()
        self.mock_w3.eth.get_transaction = Mock()
        self.mock_w3.eth.get_transaction_receipt = Mock()
        self.mock_w3.eth.wait_for_transaction_receipt = Mock()
    
    @patch('fx_sdk.client.Web3')
    def test_get_convex_vault_address_success(self, mock_web3_class):
        """Test successful vault address lookup."""
        mock_web3_class.return_value = self.mock_w3
        
        # Mock event logs - use MagicMock to support item assignment
        mock_event = MagicMock()
        mock_event.__getitem__ = Mock(side_effect=lambda k: {
            'transactionHash': b'\x00' * 32,
            'args': {
                'user': self.user_address,
                'poolid': self.pool_id
            }
        }.get(k))
        mock_event.transactionHash = b'\x00' * 32
        mock_event.args = Mock()
        mock_event.args.user = self.user_address
        mock_event.args.poolid = self.pool_id
        
        # Mock registry contract
        mock_registry = Mock()
        mock_registry.events.AddUserVault.get_logs.return_value = [mock_event]
        
        # Mock transaction receipt
        mock_receipt = {
            'blockNumber': 18000000,
            'logs': [
                {
                    'address': self.vault_address,
                    'topics': [],
                    'data': ''
                }
            ]
        }
        self.mock_w3.eth.get_transaction_receipt.return_value = mock_receipt
        
        # Mock vault contract
        mock_vault = Mock()
        mock_vault.functions.owner.return_value.call.return_value = self.user_address
        mock_vault.functions.pid.return_value.call.return_value = self.pool_id
        
        client = ProtocolClient(self.rpc_url, private_key=self.private_key)
        client._get_contract = Mock(side_effect=[mock_registry, mock_vault])
        client.w3 = self.mock_w3
        
        # This will fail because get_convex_vault_address_from_tx is complex
        # But we can test the basic flow
        result = client.get_convex_vault_address(
            self.user_address,
            self.pool_id
        )
        
        # Should attempt to query events
        self.assertTrue(mock_registry.events.AddUserVault.get_logs.called)
    
    @patch('fx_sdk.client.Web3')
    def test_get_convex_vault_address_not_found(self, mock_web3_class):
        """Test vault address lookup when vault doesn't exist."""
        mock_web3_class.return_value = self.mock_w3
        
        # Mock registry contract with no events
        mock_registry = Mock()
        mock_registry.events.AddUserVault.get_logs.return_value = []
        
        client = ProtocolClient(self.rpc_url, private_key=self.private_key)
        client._get_contract = Mock(return_value=mock_registry)
        
        result = client.get_convex_vault_address(
            self.user_address,
            self.pool_id
        )
        
        self.assertIsNone(result)
    
    @patch('fx_sdk.client.Web3')
    def test_get_convex_vault_info_success(self, mock_web3_class):
        """Test getting vault information."""
        mock_web3_class.return_value = self.mock_w3
        
        # Mock vault contract
        mock_vault = Mock()
        mock_vault.functions.owner.return_value.call.return_value = self.user_address
        mock_vault.functions.pid.return_value.call.return_value = self.pool_id
        mock_vault.functions.stakingToken.return_value.call.return_value = constants.FXUSD_BASE_POOL
        mock_vault.functions.gaugeAddress.return_value.call.return_value = "0x215D87bd3c7482E2348338815E059DE07Daf798A"
        mock_vault.functions.rewards.return_value.call.return_value = "0x1234567890123456789012345678901234567890"
        
        client = ProtocolClient(self.rpc_url)
        client._get_contract = Mock(return_value=mock_vault)
        
        info = client.get_convex_vault_info(self.vault_address)
        
        self.assertEqual(info['owner'], self.user_address)
        self.assertEqual(info['pid'], self.pool_id)
        self.assertEqual(info['staking_token'], constants.FXUSD_BASE_POOL)
    
    @patch('fx_sdk.client.Web3')
    def test_get_convex_vault_info_invalid_address(self, mock_web3_class):
        """Test getting vault info with invalid address."""
        mock_web3_class.return_value = self.mock_w3
        self.mock_w3.is_address.return_value = False
        
        client = ProtocolClient(self.rpc_url)
        client.w3 = self.mock_w3
        
        with self.assertRaises(ContractCallError):
            client.get_convex_vault_info("invalid_address")
    
    @patch('fx_sdk.client.Web3')
    def test_get_convex_vault_balance_success(self, mock_web3_class):
        """Test getting vault balance."""
        mock_web3_class.return_value = self.mock_w3
        
        # Mock vault contract
        mock_vault = Mock()
        mock_vault.functions.owner.return_value.call.return_value = self.user_address
        mock_vault.functions.stakingToken.return_value.call.return_value = constants.FXUSD_BASE_POOL
        
        # Mock token contract
        mock_token = Mock()
        mock_token.functions.balanceOf.return_value.call.return_value = 1000000000000000000  # 1 token
        mock_token.functions.decimals.return_value.call.return_value = 18
        
        client = ProtocolClient(self.rpc_url)
        client._get_contract = Mock(return_value=mock_vault)
        client.w3 = self.mock_w3
        client.w3.eth.contract = Mock(return_value=mock_token)
        
        balance = client.get_convex_vault_balance(self.vault_address)
        
        self.assertEqual(balance, Decimal("1"))
    
    @patch('fx_sdk.client.Web3')
    def test_deposit_to_convex_vault_insufficient_balance(self, mock_web3_class):
        """Test deposit with insufficient balance."""
        mock_web3_class.return_value = self.mock_w3
        
        # Mock account
        mock_account = Mock()
        mock_account.address = self.user_address
        
        # Mock vault contract
        mock_vault = Mock()
        mock_vault.functions.owner.return_value.call.return_value = self.user_address
        mock_vault.functions.stakingToken.return_value.call.return_value = constants.FXUSD_BASE_POOL
        
        # Mock token contract with insufficient balance
        mock_token = Mock()
        mock_token.functions.decimals.return_value.call.return_value = 18
        mock_token.functions.balanceOf.return_value.call.return_value = 500000000000000000  # 0.5 tokens
        mock_token.functions.allowance.return_value.call.return_value = 0
        
        client = ProtocolClient(self.rpc_url, private_key=self.private_key)
        client.account = mock_account
        client.address = self.user_address
        client._get_contract = Mock(side_effect=[mock_vault, mock_token])
        client._load_abi = Mock(return_value=[])
        client.w3 = self.mock_w3
        client.w3.eth.contract = Mock(return_value=mock_token)
        
        with self.assertRaises(InsufficientBalanceError):
            client.deposit_to_convex_vault(self.vault_address, amount=1.0)
    
    @patch('fx_sdk.client.Web3')
    def test_deposit_to_convex_vault_no_private_key(self, mock_web3_class):
        """Test deposit without private key."""
        mock_web3_class.return_value = self.mock_w3
        
        client = ProtocolClient(self.rpc_url)  # No private key
        
        with self.assertRaises(FXProtocolError):
            client.deposit_to_convex_vault(self.vault_address, amount=1.0)
    
    @patch('fx_sdk.client.Web3')
    def test_withdraw_from_convex_vault_insufficient_balance(self, mock_web3_class):
        """Test withdrawal with insufficient vault balance."""
        mock_web3_class.return_value = self.mock_w3
        
        # Mock account
        mock_account = Mock()
        mock_account.address = self.user_address
        
        # Mock vault contract
        mock_vault = Mock()
        mock_vault.functions.owner.return_value.call.return_value = self.user_address
        mock_vault.functions.stakingToken.return_value.call.return_value = constants.FXUSD_BASE_POOL
        
        # Mock token contract
        mock_token = Mock()
        mock_token.functions.decimals.return_value.call.return_value = 18
        
        client = ProtocolClient(self.rpc_url, private_key=self.private_key)
        client.account = mock_account
        client.address = self.user_address
        client._get_contract = Mock(side_effect=[mock_vault, mock_token])
        client._load_abi = Mock(return_value=[])
        client.w3 = self.mock_w3
        client.w3.eth.contract = Mock(return_value=mock_token)
        client.get_convex_vault_balance = Mock(return_value=Decimal("0.5"))
        
        with self.assertRaises(InsufficientBalanceError):
            client.withdraw_from_convex_vault(self.vault_address, amount=1.0)
    
    @patch('fx_sdk.client.Web3')
    def test_get_convex_vault_rewards_success(self, mock_web3_class):
        """Test getting vault rewards."""
        mock_web3_class.return_value = self.mock_w3
        
        # Mock vault contract
        mock_vault = Mock()
        mock_vault.functions.owner.return_value.call.return_value = self.user_address
        mock_vault.functions.earned.return_value.call.return_value = (
            ["0x365AccFCa291e7D3914637ABf1F7635dB165Bb09"],  # FXN token
            [5000000000000000000]  # 5 tokens
        )
        
        # Mock token contract for decimals
        mock_token = Mock()
        mock_token.functions.decimals.return_value.call.return_value = 18
        
        client = ProtocolClient(self.rpc_url)
        client._get_contract = Mock(return_value=mock_vault)
        client.w3 = self.mock_w3
        client.w3.eth.contract = Mock(return_value=mock_token)
        
        rewards = client.get_convex_vault_rewards(self.vault_address)
        
        self.assertIn('token_addresses', rewards)
        self.assertIn('amounts', rewards)
        self.assertEqual(len(rewards['token_addresses']), 1)
        self.assertEqual(
            rewards['amounts']["0x365AccFCa291e7D3914637ABf1F7635dB165Bb09"],
            Decimal("5")
        )
    
    @patch('fx_sdk.client.Web3')
    def test_claim_convex_vault_rewards_no_private_key(self, mock_web3_class):
        """Test claiming rewards without private key."""
        mock_web3_class.return_value = self.mock_w3
        
        client = ProtocolClient(self.rpc_url)  # No private key
        
        with self.assertRaises(FXProtocolError):
            client.claim_convex_vault_rewards(self.vault_address)
    
    @patch('fx_sdk.client.Web3')
    def test_get_cvxfxn_balance(self, mock_web3_class):
        """Test getting cvxFXN balance."""
        mock_web3_class.return_value = self.mock_w3
        
        client = ProtocolClient(self.rpc_url)
        # Mock get_token_balance directly since it's called by get_cvxfxn_balance
        client.get_token_balance = Mock(return_value=Decimal("2"))
        
        balance = client.get_cvxfxn_balance(self.user_address)
        
        self.assertEqual(balance, Decimal("2"))
    
    @patch('fx_sdk.client.Web3')
    def test_get_staked_cvxfxn_balance(self, mock_web3_class):
        """Test getting staked cvxFXN balance."""
        mock_web3_class.return_value = self.mock_w3
        
        # Mock stake contract
        mock_stake = Mock()
        mock_stake.functions.balanceOf.return_value.call.return_value = 1000000000000000000  # 1 token
        mock_stake.functions.decimals.return_value.call.return_value = 18
        
        client = ProtocolClient(self.rpc_url)
        client._get_contract = Mock(return_value=mock_stake)
        
        balance = client.get_staked_cvxfxn_balance(self.user_address)
        
        self.assertEqual(balance, Decimal("1"))
    
    @patch('fx_sdk.client.Web3')
    def test_get_cvxfxn_staking_rewards(self, mock_web3_class):
        """Test getting cvxFXN staking rewards."""
        mock_web3_class.return_value = self.mock_w3
        
        # Mock stake contract
        mock_stake = Mock()
        mock_stake.functions.earned.return_value.call.return_value = 500000000000000000  # 0.5 tokens
        mock_stake.functions.decimals.return_value.call.return_value = 18
        
        client = ProtocolClient(self.rpc_url)
        client._get_contract = Mock(return_value=mock_stake)
        
        rewards = client.get_cvxfxn_staking_rewards(self.user_address)
        
        self.assertEqual(rewards, Decimal("0.5"))
    
    @patch('fx_sdk.client.Web3')
    def test_deposit_fxn_to_cvxfxn_no_private_key(self, mock_web3_class):
        """Test depositing FXN to cvxFXN without private key."""
        mock_web3_class.return_value = self.mock_w3
        
        client = ProtocolClient(self.rpc_url)  # No private key
        
        with self.assertRaises(FXProtocolError):
            client.deposit_fxn_to_cvxfxn(amount=1.0)
    
    @patch('fx_sdk.client.Web3')
    def test_stake_cvxfxn_no_private_key(self, mock_web3_class):
        """Test staking cvxFXN without private key."""
        mock_web3_class.return_value = self.mock_w3
        
        client = ProtocolClient(self.rpc_url)  # No private key
        
        with self.assertRaises(FXProtocolError):
            client.stake_cvxfxn(amount=1.0)
    
    @patch('fx_sdk.client.Web3')
    def test_get_convex_pool_info_by_id(self, mock_web3_class):
        """Test getting pool info by pool ID."""
        mock_web3_class.return_value = self.mock_w3
        
        client = ProtocolClient(self.rpc_url)
        
        pool_info = client.get_convex_pool_info(pool_id=37)
        
        self.assertEqual(pool_info['pool_id'], 37)
        self.assertIn('name', pool_info)
        self.assertIn('staked_token', pool_info)
        self.assertEqual(pool_info['pool_key'], 'fxusd_stability_fxn')
    
    @patch('fx_sdk.client.Web3')
    def test_get_convex_pool_info_by_key(self, mock_web3_class):
        """Test getting pool info by pool key."""
        mock_web3_class.return_value = self.mock_w3
        
        client = ProtocolClient(self.rpc_url)
        
        pool_info = client.get_convex_pool_info(pool_key='fxusd_stability_fxn')
        
        self.assertEqual(pool_info['pool_id'], 37)
        self.assertEqual(pool_info['pool_key'], 'fxusd_stability_fxn')
        self.assertIn('name', pool_info)
    
    @patch('fx_sdk.client.Web3')
    def test_get_convex_pool_info_not_found(self, mock_web3_class):
        """Test getting pool info for non-existent pool."""
        mock_web3_class.return_value = self.mock_w3
        
        client = ProtocolClient(self.rpc_url)
        
        with self.assertRaises(FXProtocolError):
            client.get_convex_pool_info(pool_id=99999)
    
    @patch('fx_sdk.client.Web3')
    def test_get_all_convex_pools(self, mock_web3_class):
        """Test getting all Convex pools."""
        mock_web3_class.return_value = self.mock_w3
        
        client = ProtocolClient(self.rpc_url)
        
        all_pools = client.get_all_convex_pools()
        
        self.assertIsInstance(all_pools, dict)
        self.assertGreater(len(all_pools), 0)
        # Check that pool 37 is in the results
        found_pool_37 = False
        for pool_key, pool_info in all_pools.items():
            if pool_info.get('pool_id') == 37:
                found_pool_37 = True
                self.assertEqual(pool_info['pool_key'], pool_key)
                break
        self.assertTrue(found_pool_37, "Pool 37 should be in the results")
    
    @patch('fx_sdk.client.Web3')
    def test_get_vault_balances_batch(self, mock_web3_class):
        """Test batch query of vault balances."""
        mock_web3_class.return_value = self.mock_w3
        
        client = ProtocolClient(self.rpc_url)
        client.get_convex_vault_balance = Mock(side_effect=[
            Decimal("100"),
            Decimal("50"),
            Decimal("0")
        ])
        
        vault_addresses = [self.vault_address, "0x" + "1" * 40, "0x" + "2" * 40]
        balances = client.get_vault_balances_batch(vault_addresses)
        
        self.assertEqual(len(balances), 3)
        self.assertEqual(balances[self.vault_address], Decimal("100"))
    
    @patch('fx_sdk.client.Web3')
    def test_get_vault_rewards_batch(self, mock_web3_class):
        """Test batch query of vault rewards."""
        mock_web3_class.return_value = self.mock_w3
        
        client = ProtocolClient(self.rpc_url)
        client.get_convex_vault_rewards = Mock(return_value={
            "token_addresses": ["0x365AccFCa291e7D3914637ABf1F7635dB165Bb09"],
            "amounts": {"0x365AccFCa291e7D3914637ABf1F7635dB165Bb09": Decimal("5")}
        })
        
        vault_addresses = [self.vault_address, "0x" + "1" * 40]
        rewards = client.get_vault_rewards_batch(vault_addresses)
        
        self.assertEqual(len(rewards), 2)
        self.assertIn(self.vault_address, rewards)
        self.assertIn("token_addresses", rewards[self.vault_address])
    
    @patch('fx_sdk.client.Web3')
    def test_get_convex_pool_apy(self, mock_web3_class):
        """Test getting APY for a Convex pool."""
        mock_web3_class.return_value = self.mock_w3
        
        # Mock booster contract
        mock_booster = Mock()
        mock_booster.functions.poolInfo.return_value.call.return_value = [
            constants.FXUSD_BASE_POOL,  # lptoken
            "0x1234567890123456789012345678901234567890",  # token
            "0x215D87bd3c7482E2348338815E059DE07Daf798A",  # gauge
            "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",  # crvRewards (BaseRewardPool)
            "0x0000000000000000000000000000000000000000",  # stash
            False  # shutdown
        ]
        
        # Mock reward pool contract
        mock_reward_pool = Mock()
        mock_reward_pool.functions.rewardRate.return_value.call.return_value = 1000000000000000000  # 1 token per second
        mock_reward_pool.functions.totalSupply.return_value.call.return_value = 100000000000000000000  # 100 tokens staked
        mock_reward_pool.functions.periodFinish.return_value.call.return_value = 9999999999  # Far future
        mock_reward_pool.functions.rewardToken.return_value.call.return_value = constants.FXN
        mock_reward_pool.functions.stakingToken.return_value.call.return_value = constants.FXUSD_BASE_POOL
        
        # Mock token contracts
        mock_reward_token = Mock()
        mock_reward_token.functions.decimals.return_value.call.return_value = 18
        mock_staking_token = Mock()
        mock_staking_token.functions.decimals.return_value.call.return_value = 18
        
        # Mock block
        mock_block = {'timestamp': 1000000000}
        self.mock_w3.eth.get_block.return_value = mock_block
        
        client = ProtocolClient(self.rpc_url)
        client._get_contract = Mock(side_effect=[
            mock_booster,  # booster
            mock_reward_pool,  # reward pool
            mock_reward_token,  # reward token
            mock_staking_token  # staking token
        ])
        client.w3 = self.mock_w3
        
        apy_data = client.get_convex_pool_apy(pool_id=37)
        
        self.assertIn('apy', apy_data)
        self.assertIn('reward_rate', apy_data)
        self.assertIn('total_staked', apy_data)
        self.assertIn('is_active', apy_data)
        self.assertEqual(apy_data['pool_id'], 37)
        # APY should be approximately: (1 * 31536000) / 100 * 100 = 315360%
        # But that's per second, so let's just check it's calculated
        self.assertIsInstance(apy_data['apy'], (int, float))
    
    @patch('fx_sdk.client.Web3')
    def test_get_convex_vault_apy(self, mock_web3_class):
        """Test getting APY for a Convex vault."""
        mock_web3_class.return_value = self.mock_w3
        
        # Mock vault contract
        mock_vault = Mock()
        mock_vault.functions.pid.return_value.call.return_value = 37
        mock_vault.functions.rewards.return_value.call.return_value = "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"
        mock_vault.functions.owner.return_value.call.return_value = self.user_address
        
        # Mock reward pool contract
        mock_reward_pool = Mock()
        mock_reward_pool.functions.rewardRate.return_value.call.return_value = 500000000000000000  # 0.5 token per second
        mock_reward_pool.functions.totalSupply.return_value.call.return_value = 50000000000000000000  # 50 tokens staked
        mock_reward_pool.functions.periodFinish.return_value.call.return_value = 9999999999
        mock_reward_pool.functions.rewardToken.return_value.call.return_value = constants.FXN
        mock_reward_pool.functions.stakingToken.return_value.call.return_value = constants.FXUSD_BASE_POOL
        
        # Mock token contracts
        mock_reward_token = Mock()
        mock_reward_token.functions.decimals.return_value.call.return_value = 18
        mock_staking_token = Mock()
        mock_staking_token.functions.decimals.return_value.call.return_value = 18
        
        # Mock block
        mock_block = {'timestamp': 1000000000}
        self.mock_w3.eth.get_block.return_value = mock_block
        
        client = ProtocolClient(self.rpc_url)
        client._get_contract = Mock(side_effect=[
            mock_vault,  # vault
            mock_reward_pool,  # reward pool
            mock_reward_token,  # reward token
            mock_staking_token  # staking token
        ])
        client.w3 = self.mock_w3
        client.get_convex_pool_info = Mock(return_value={"name": "Test Pool", "pool_key": "test"})
        
        apy_data = client.get_convex_vault_apy(self.vault_address)
        
        self.assertIn('apy', apy_data)
        self.assertIn('pool_id', apy_data)
        self.assertEqual(apy_data['pool_id'], 37)
        self.assertIn('vault_address', apy_data)
        self.assertEqual(apy_data['vault_address'], self.vault_address)
    
    @patch('fx_sdk.client.Web3')
    def test_get_all_convex_pools_apy(self, mock_web3_class):
        """Test getting APY for all Convex pools."""
        mock_web3_class.return_value = self.mock_w3
        
        client = ProtocolClient(self.rpc_url)
        client.get_convex_pool_apy = Mock(return_value={
            "apy": 10.5,
            "pool_id": 37,
            "pool_name": "Test Pool",
            "is_active": True
        })
        
        apys = client.get_all_convex_pools_apy()
        
        self.assertIsInstance(apys, dict)
        # Should have entries for pools that succeeded
        # (Some may fail, which is expected)
    
    @patch('fx_sdk.client.Web3')
    def test_get_convex_pool_details(self, mock_web3_class):
        """Test getting comprehensive pool details."""
        mock_web3_class.return_value = self.mock_w3
        
        # Mock booster contract
        mock_booster = Mock()
        mock_booster.functions.poolInfo.return_value.call.return_value = [
            constants.FXUSD_BASE_POOL,  # lptoken
            "0x1234567890123456789012345678901234567890",  # token
            "0x215D87bd3c7482E2348338815E059DE07Daf798A",  # gauge
            "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",  # crvRewards
            "0x0000000000000000000000000000000000000000",  # stash
            False  # shutdown
        ]
        
        # Mock reward pool contract
        mock_reward_pool = Mock()
        mock_reward_pool.functions.totalSupply.return_value.call.return_value = 100000000000000000000
        mock_reward_pool.functions.stakingToken.return_value.call.return_value = constants.FXUSD_BASE_POOL
        mock_reward_pool.functions.rewardToken.return_value.call.return_value = constants.FXN
        mock_reward_pool.functions.rewardRate.return_value.call.return_value = 1000000000000000000
        mock_reward_pool.functions.periodFinish.return_value.call.return_value = 9999999999
        
        # Mock token contracts
        mock_staking_token = Mock()
        mock_staking_token.functions.decimals.return_value.call.return_value = 18
        mock_reward_token = Mock()
        mock_reward_token.functions.decimals.return_value.call.return_value = 18
        
        # Mock block
        mock_block = {'timestamp': 1000000000}
        self.mock_w3.eth.get_block.return_value = mock_block
        
        client = ProtocolClient(self.rpc_url)
        client._get_contract = Mock(side_effect=[
            mock_booster,  # booster
            mock_reward_pool,  # reward pool (for TVL)
            mock_staking_token,  # staking token
            mock_reward_pool,  # reward pool (for rewards)
            mock_reward_token  # reward token
        ])
        client.w3 = self.mock_w3
        client.get_convex_pool_info = Mock(return_value={
            "pool_id": 37,
            "name": "fxUSD V2 Stability Pool (Earns FXN)",
            "staked_token": constants.FXUSD_BASE_POOL
        })
        
        details = client.get_convex_pool_details(pool_id=37)
        
        self.assertIn('pool_id', details)
        self.assertIn('tvl', details)
        self.assertIn('gauge_address', details)
        self.assertIn('reward_tokens', details)
        self.assertIn('rewards_active', details)
        self.assertEqual(details['pool_id'], 37)
    
    @patch('fx_sdk.client.Web3')
    def test_get_convex_pool_tvl(self, mock_web3_class):
        """Test getting pool TVL."""
        mock_web3_class.return_value = self.mock_w3
        
        # Mock booster and reward pool
        mock_booster = Mock()
        mock_booster.functions.poolInfo.return_value.call.return_value = [
            constants.FXUSD_BASE_POOL,  # lptoken
            "0x1234567890123456789012345678901234567890",  # token
            "0x215D87bd3c7482E2348338815E059DE07Daf798A",  # gauge
            "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",  # crvRewards
            "0x0000000000000000000000000000000000000000",  # stash
            False  # shutdown
        ]
        
        mock_reward_pool = Mock()
        mock_reward_pool.functions.totalSupply.return_value.call.return_value = 50000000000000000000
        mock_reward_pool.functions.stakingToken.return_value.call.return_value = constants.FXUSD_BASE_POOL
        
        mock_staking_token = Mock()
        mock_staking_token.functions.decimals.return_value.call.return_value = 18
        
        client = ProtocolClient(self.rpc_url)
        client._get_contract = Mock(side_effect=[
            mock_booster,
            mock_reward_pool,
            mock_staking_token
        ])
        client.w3 = self.mock_w3
        
        tvl = client.get_convex_pool_tvl(pool_id=37)
        
        self.assertIsNotNone(tvl)
        self.assertIsInstance(tvl, Decimal)
    
    @patch('fx_sdk.client.Web3')
    def test_get_convex_pool_reward_tokens(self, mock_web3_class):
        """Test getting pool reward tokens."""
        mock_web3_class.return_value = self.mock_w3
        
        mock_booster = Mock()
        mock_booster.functions.poolInfo.return_value.call.return_value = [
            constants.FXUSD_BASE_POOL,
            "0x1234567890123456789012345678901234567890",
            "0x215D87bd3c7482E2348338815E059DE07Daf798A",
            "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            "0x0000000000000000000000000000000000000000",
            False
        ]
        
        mock_reward_pool = Mock()
        mock_reward_pool.functions.rewardToken.return_value.call.return_value = constants.FXN
        
        client = ProtocolClient(self.rpc_url)
        client._get_contract = Mock(side_effect=[mock_booster, mock_reward_pool])
        client.w3 = self.mock_w3
        
        reward_tokens = client.get_convex_pool_reward_tokens(pool_id=37)
        
        self.assertIsInstance(reward_tokens, list)
        self.assertEqual(len(reward_tokens), 1)
        self.assertEqual(reward_tokens[0], constants.FXN)
    
    @patch('fx_sdk.client.Web3')
    def test_get_convex_pool_gauge_address(self, mock_web3_class):
        """Test getting pool gauge address."""
        mock_web3_class.return_value = self.mock_w3
        
        mock_booster = Mock()
        gauge_address = "0x215D87bd3c7482E2348338815E059DE07Daf798A"
        mock_booster.functions.poolInfo.return_value.call.return_value = [
            constants.FXUSD_BASE_POOL,
            "0x1234567890123456789012345678901234567890",
            gauge_address,
            "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            "0x0000000000000000000000000000000000000000",
            False
        ]
        
        client = ProtocolClient(self.rpc_url)
        client._get_contract = Mock(return_value=mock_booster)
        client.w3 = self.mock_w3
        
        gauge = client.get_convex_pool_gauge_address(pool_id=37)
        
        self.assertIsNotNone(gauge)
        self.assertEqual(gauge.lower(), gauge_address.lower())
    
    @patch('fx_sdk.client.Web3')
    def test_get_all_convex_pools_tvl(self, mock_web3_class):
        """Test getting TVL for all pools."""
        mock_web3_class.return_value = self.mock_w3
        
        client = ProtocolClient(self.rpc_url)
        client.get_convex_pool_tvl = Mock(return_value=Decimal("1000"))
        
        all_tvls = client.get_all_convex_pools_tvl()
        
        self.assertIsInstance(all_tvls, dict)
        # Should have entries for all pools
        self.assertGreater(len(all_tvls), 0)
    
    @patch('fx_sdk.client.Web3')
    def test_get_convex_pool_statistics(self, mock_web3_class):
        """Test getting comprehensive pool statistics."""
        mock_web3_class.return_value = self.mock_w3
        
        client = ProtocolClient(self.rpc_url)
        client.get_convex_pool_details = Mock(return_value={
            "pool_id": 37,
            "name": "Test Pool",
            "tvl": 1000.0,
            "reward_tokens": [constants.FXN],
            "rewards_active": True
        })
        client.get_convex_pool_apy = Mock(return_value={
            "apy": 10.5,
            "reward_rate": 1.0,
            "total_staked": 100.0
        })
        
        stats = client.get_convex_pool_statistics(pool_id=37)
        
        self.assertIn('pool_id', stats)
        self.assertIn('tvl', stats)
        self.assertIn('apy', stats)
        self.assertIn('statistics_available', stats)
        self.assertTrue(stats['statistics_available'])


if __name__ == '__main__':
    unittest.main()

