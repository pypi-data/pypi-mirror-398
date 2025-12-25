# Changelog

All notable changes to the fx-sdk project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2025-12-22

### Removed
- **APY Calculation Methods**: Removed all APY calculation methods due to complexity and accuracy issues:
  - `get_convex_pool_apy()` - Removed
  - `get_convex_vault_apy()` - Removed
  - `get_all_convex_pools_apy()` - Removed
  - `get_curve_gauge_apy()` - Removed
  - `get_all_curve_gauges_apy()` - Removed
  
  **Reason**: Convex and Curve APY calculations require historical data and multiple sources that are difficult to accurately replicate on-chain. Users should refer to Convex/Curve websites for official APY values.

### Changed
- `get_convex_pool_statistics()` - No longer includes APY data (APY calculation removed)

## [0.2.0] - 2025-12-22

### Added

#### Convex Finance Integration
- **Vault Management**: Create and query user-specific Convex vaults
  - `create_convex_vault()` - Create new vault for any Convex pool
  - `get_convex_vault_address()` - Find user's vault address
  - `get_convex_vault_address_from_tx()` - Extract vault from transaction
  - `get_convex_vault_address_or_create()` - Helper for automatic vault creation
- **Vault Operations**: Deposit, withdraw, and claim rewards
  - `deposit_to_convex_vault()` - Deposit LP tokens with automatic approvals
  - `withdraw_from_convex_vault()` - Withdraw staked LP tokens
  - `claim_convex_vault_rewards()` - Claim rewards with selective token support
- **Vault Information**: Query vault details and balances
  - `get_convex_vault_info()` - Comprehensive vault metadata
  - `get_convex_vault_balance()` - Staked balance queries (read-only)
  - `get_convex_vault_rewards()` - Claimable rewards tracking
- **cvxFXN Staking**: Dedicated staking mechanism for FXN
  - `deposit_fxn_to_cvxfxn()` - Convert FXN to cvxFXN
  - `stake_cvxfxn()` - Stake cvxFXN tokens
  - `unstake_cvxfxn()` - Unstake cvxFXN tokens
  - `claim_cvxfxn_staking_rewards()` - Claim staking rewards
  - `get_cvxfxn_balance()`, `get_staked_cvxfxn_balance()`, `get_cvxfxn_staking_rewards()` - Read methods
- **Helper Methods**: Batch operations and summaries
  - `get_all_user_vaults()` - Find all user vaults across pools
  - `get_convex_pool_info()` - Get pool metadata from registry
  - `get_all_convex_pools()` - List all pools in registry
  - `get_vault_balances_batch()` - Batch balance queries
  - `get_vault_rewards_batch()` - Batch reward queries
  - `get_user_vaults_summary()` - Comprehensive position summary
- **APY Calculations**: Real-time yield calculations
  - `get_convex_pool_apy()` - Calculate APY for any pool
  - `get_convex_vault_apy()` - Calculate APY for specific vault
  - `get_all_convex_pools_apy()` - Batch APY queries
- **Pool Information Queries**: Live on-chain data
  - `get_convex_pool_details()` - Comprehensive pool details
  - `get_convex_pool_tvl()` - Total Value Locked queries
  - `get_convex_pool_reward_tokens()` - Reward token addresses
  - `get_convex_pool_gauge_address()` - Gauge addresses
  - `get_all_convex_pools_tvl()` - Batch TVL queries
  - `get_convex_pool_statistics()` - Combined stats (details + TVL + APY)
- **Registry**: `CONVEX_POOLS` registry with 30+ f(x) Protocol pools

#### Curve Finance Integration
- **Pool Information**: Query Curve pool data
  - `get_curve_pool_info()` - Comprehensive pool information
  - `get_curve_pool_balances()` - Token balances in pools
  - `get_curve_pool_virtual_price()` - LP token virtual price
  - `get_curve_swap_rate()` - Calculate swap rates
  - `find_curve_pool()` - Find pools by token pair
  - `get_curve_pool_from_lp_token()` - Find pool from LP token
- **Gauge Operations**: Staking and rewards
  - `get_curve_gauge_info()` - Gauge information and rewards
  - `get_curve_gauge_balance()` - Staked LP token balance
  - `get_curve_gauge_rewards()` - Claimable rewards
  - `get_curve_gauge_from_pool()` - Find gauge from pool
- **Swap Operations**: Execute swaps on Curve
  - `curve_swap()` - Swap tokens with automatic approvals and slippage protection
- **Liquidity Management**: Add and remove liquidity
  - `curve_add_liquidity()` - Add liquidity to pools
  - `curve_remove_liquidity()` - Remove liquidity from pools
- **Gauge Staking**: Stake LP tokens in gauges
  - `curve_stake_lp_tokens()` - Stake LP tokens
  - `curve_unstake_lp_tokens()` - Unstake LP tokens
  - `curve_claim_gauge_rewards()` - Claim CRV rewards
- **Helper Methods**: Batch operations and summaries
  - `get_curve_pools_from_registry()` - Get all Curve pools from registry
  - `get_curve_pool_from_registry()` - Get pool by ID or key
  - `get_curve_gauge_balances_batch()` - Batch balance queries
  - `get_curve_gauge_rewards_batch()` - Batch reward queries
  - `get_user_curve_positions_summary()` - Comprehensive position summary
  - `get_curve_gauge_apy()` - Calculate APY for gauges
  - `get_all_curve_gauges_apy()` - Batch APY queries
- **Registry Support**: Automatic fallback between Meta Registry and Main Registry

#### Testing
- Comprehensive test suite for Convex integration (`tests/test_convex.py`)
- Comprehensive test suite for Curve integration (`tests/test_curve.py`)
- 26 Convex tests, 26 Curve tests (all passing)
- Full coverage of read/write operations, error handling, and edge cases

#### Documentation
- `CONVEX_INTEGRATION_COMPLETE.md` - Complete Convex integration guide
- `CURVE_INTEGRATION_COMPLETE.md` - Complete Curve integration guide
- Updated `features.md` with Convex and Curve sections
- Integration plans and comparison documents

### Changed
- Enhanced error handling with better validation
- Improved address validation order in several methods
- Updated `CONTRACTS` dictionary with Convex and Curve addresses

### Technical Details
- Added 7 Convex ABIs (vault factory, vault, booster, base reward pool, cvxFXN contracts)
- Added 7 Curve ABIs (registry, meta registry, address provider, factory, pool, gauge, CRV token)
- All methods support read-only mode (no private key required for queries)
- Automatic token approvals for all write operations
- Default slippage protection (0.5% tolerance)
- Decimal precision handling throughout

## [0.1.0] - 2025-12-20

### Added
- Initial release of fx-sdk
- Core f(x) Protocol V1 and V2 support
- Secure multi-source authentication
- High-precision Decimal handling
- Comprehensive test suite
- Production-ready error handling

