import logging
import json
import os
from decimal import Decimal
from typing import Optional, Union, Dict, Any, List

from web3 import Web3
from web3.contract import Contract
from eth_account import Account
from eth_account.signers.local import LocalAccount

# Try to import optional dependencies
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

try:
    from google.colab import userdata  # type: ignore[import-untyped]
    COLAB_AVAILABLE = True
except ImportError:
    COLAB_AVAILABLE = False

from . import constants
from . import utils
from .exceptions import (
    FXProtocolError,
    TransactionFailedError,
    InsufficientBalanceError,
    ContractCallError,
    ConfigurationError
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fx_sdk")

class ProtocolClient:
    """
    The main client for interacting with the f(x) Protocol.
    
    This class abstracts Web3.py boilerplate and provides easy-to-use
    methods for reading from and writing to the f(x) Protocol smart contracts.
    
    Wallet Authentication Priority:
    1. Explicit private_key parameter
    2. Environment variable: FX_PROTOCOL_PRIVATE_KEY
    3. .env file: FX_PROTOCOL_PRIVATE_KEY
    4. Google Colab secret: 'fx_protocol_private_key'
    5. Browser-injected wallet (window.ethereum)
    """

    def __init__(
        self,
        rpc_url: str,
        private_key: Optional[str] = None,
        abi_dir: Optional[str] = None,
        log_level: int = logging.INFO,
        use_browser_wallet: bool = False
    ):
        """
        Initialize the ProtocolClient.
        
        Args:
            rpc_url: The RPC URL for the Ethereum network.
            private_key: Optional private key for signing transactions. If not provided,
                       the client will attempt to discover credentials from environment
                       variables, .env files, Colab secrets, or browser wallets.
            abi_dir: Optional directory where contract ABIs are stored. Defaults to internal package directory.
            log_level: Logging level (default logging.INFO).
            use_browser_wallet: If True, attempt to connect to a browser-injected wallet (MetaMask, etc.).
                              Requires running in a browser environment with Web3 wallet extension.
        """
        logger.setLevel(log_level)
        
        # Load .env file if available
        if DOTENV_AVAILABLE:
            load_dotenv()
        
        # Discover wallet credentials
        discovered_key = self._discover_wallet_credentials(private_key, use_browser_wallet)
        
        # Initialize Web3 connection
        if use_browser_wallet and discovered_key is None:
            # Try to use browser-injected provider
            try:
                # This will work in browser environments (Jupyter with ipywidgets, etc.)
                # For Node.js-like environments, you'd use window.ethereum
                self.w3 = Web3()  # Will be set by browser provider
                logger.warning("Browser wallet connection requires additional setup. Falling back to RPC provider.")
                self.w3 = Web3(Web3.HTTPProvider(rpc_url))
            except Exception as e:
                logger.warning(f"Browser wallet not available: {e}. Using RPC provider.")
                self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        else:
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        try:
            is_connected = self.w3.is_connected()
        except AttributeError:
            is_connected = self.w3.isConnected()
            
        if not is_connected:
            raise ConfigurationError(f"Failed to connect to RPC at {rpc_url}")

        # Set up account
        self.account: Optional[LocalAccount] = None
        self.use_browser_wallet = use_browser_wallet and discovered_key is None
        
        if discovered_key:
            self.account = Account.from_key(discovered_key)
            self.address = self.account.address
            logger.info(f"Initialized client for address: {self.address}")
        elif use_browser_wallet:
            # Browser wallet will be used for signing, but we need to get address from provider
            try:
                accounts = self.w3.eth.accounts
                if accounts:
                    self.address = accounts[0]
                    logger.info(f"Connected to browser wallet: {self.address}")
                else:
                    self.address = None
                    logger.warning("Browser wallet connected but no accounts available")
            except Exception as e:
                logger.warning(f"Could not get browser wallet address: {e}")
                self.address = None
        else:
            self.address = None
            logger.warning("Initialized client without private key (Read-Only Mode)")

        # Default abi_dir to the internal package directory
        if abi_dir is None:
            self.abi_dir = os.path.join(os.path.dirname(__file__), "abis")
        else:
            self.abi_dir = abi_dir
            
        self.contracts: Dict[str, Contract] = {}
        self._load_contracts()

    def _discover_wallet_credentials(
        self, 
        explicit_key: Optional[str] = None,
        use_browser: bool = False
    ) -> Optional[str]:
        """
        Discover wallet credentials from multiple secure sources.
        
        Priority order:
        1. Explicit private_key parameter
        2. Environment variable: FX_PROTOCOL_PRIVATE_KEY
        3. .env file: FX_PROTOCOL_PRIVATE_KEY (loaded via dotenv)
        4. Google Colab secret: 'fx_protocol_private_key'
        5. Browser wallet (if use_browser=True)
        
        Returns:
            Optional[str]: Private key if discovered, None otherwise.
        """
        # 1. Explicit parameter (highest priority)
        if explicit_key:
            logger.debug("Using explicitly provided private key")
            return explicit_key
        
        # 2. Environment variable
        env_key = os.getenv("FX_PROTOCOL_PRIVATE_KEY")
        if env_key:
            logger.debug("Using private key from environment variable")
            return env_key
        
        # 3. .env file (already loaded by load_dotenv if available)
        # This is the same as env var, but loaded from .env file
        
        # 4. Google Colab secret
        if COLAB_AVAILABLE:
            try:
                colab_key = userdata.get('fx_protocol_private_key')
                if colab_key:
                    logger.debug("Using private key from Google Colab secret")
                    return colab_key
            except Exception as e:
                logger.debug(f"Colab secret not available: {e}")
        
        # 5. Browser wallet (handled separately in __init__)
        if use_browser:
            logger.debug("Browser wallet will be used for signing")
            return None
        
        return None

    def _load_contracts(self):
        """Internal method to pre-instantiate contract objects."""
        # Core Contracts
        self.fxusd = self._get_contract("fxusd", constants.FXUSD)
        self.fxusd_base_pool = self._get_contract("fxusd_base_pool", constants.FXUSD_BASE_POOL)
        self.diamond_router = self._get_contract("diamond", constants.DIAMOND_ROUTER)
        
        # Governance
        self.fxn = self._get_contract("fxn", constants.FXN)
        self.vefxn = self._get_contract("vefxn", constants.VEFXN)
        self.gauge_controller = self._get_contract("gauge_controller", constants.GAUGE_CONTROLLER)
        
        # V1 Market (for fETH/xETH)
        self.v1_market = self._get_contract("market", constants.MARKET_PROXY)
        self.v1_rebalance_registry = self._get_contract("rebalance_pool_registry", constants.REBALANCE_POOL_REGISTRY)
        
        # Supporting
        self.multipath_converter = self._get_contract("multipath_converter", constants.MULTI_PATH_CONVERTER)
        self.steth_gateway = self._get_contract("steth_gateway", constants.STETH_GATEWAY)

    def _get_contract(self, name: str, address: str) -> Contract:
        """
        Load a contract by its name and address.
        
        Args:
            name: The name of the contract (used to find the ABI file).
            address: The Ethereum address of the contract.
            
        Returns:
            Contract: The Web3 contract object.
        """
        abi_path = os.path.join(self.abi_dir, f"{name.lower()}.json")
        checksum_address = utils.to_checksum_address(address)
        try:
            if os.path.exists(abi_path) and os.path.getsize(abi_path) > 0:
                with open(abi_path, "r") as f:
                    abi = json.load(f)
            else:
                abi = []  # Fallback to empty ABI
            return self.w3.eth.contract(address=checksum_address, abi=abi)
        except Exception as e:
            # For now, we return a contract with empty ABI if file loading fails
            # This prevents initialization errors while ABIs are being added
            return self.w3.eth.contract(address=checksum_address, abi=[])

    # --- Generic Read Methods ---

    def get_token_balance(self, token_address: str, account_address: Optional[str] = None) -> Decimal:
        """
        Get the human-readable balance of a token for an account.
        
        Args:
            token_address: The address of the token contract (ERC20).
            account_address: Optional account address (defaults to client's address).
            
        Returns:
            Decimal: The human-readable balance.
        """
        target_address = account_address or self.address
        if not target_address:
            raise FXProtocolError("No account address provided or available in client.")
        
        contract = self.w3.eth.contract(
            address=utils.to_checksum_address(token_address),
            abi=[
                {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
            ]
        )
        
        try:
            raw_balance = contract.functions.balanceOf(target_address).call()
            decimals = contract.functions.decimals().call()
            return utils.wei_to_decimal(raw_balance, decimals)
        except Exception as e:
            raise ContractCallError(f"Failed to get balance: {str(e)}")

    def get_token_total_supply(self, token_address: str) -> Decimal:
        """Get the total supply of a token."""
        contract = self.w3.eth.contract(
            address=utils.to_checksum_address(token_address),
            abi=[
                {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
            ]
        )
        try:
            raw_supply = contract.functions.totalSupply().call()
            decimals = contract.functions.decimals().call()
            return utils.wei_to_decimal(raw_supply, decimals)
        except Exception as e:
            raise ContractCallError(f"Failed to get total supply: {str(e)}")

    def get_allowance(self, token_address: str, owner: str, spender: str) -> Decimal:
        """Get the allowance of a spender for a token owner."""
        contract = self.w3.eth.contract(
            address=utils.to_checksum_address(token_address),
            abi=[
                {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
            ]
        )
        try:
            raw_allowance = contract.functions.allowance(
                utils.to_checksum_address(owner),
                utils.to_checksum_address(spender)
            ).call()
            decimals = contract.functions.decimals().call()
            return utils.wei_to_decimal(raw_allowance, decimals)
        except Exception as e:
            raise ContractCallError(f"Failed to get allowance: {str(e)}")

    # --- V2 Product-Specific Read Methods ---

    def get_fxusd_total_supply(self) -> Decimal:
        """Get the total supply of fxUSD."""
        return self.get_token_total_supply(constants.FXUSD)

    def get_steth_price(self) -> Decimal:
        """Get the current stETH price from the oracle."""
        contract = self.w3.eth.contract(
            address=utils.to_checksum_address(constants.STETH_PRICE_ORACLE),
            abi=[{"constant": True, "inputs": [], "name": "getPrice", "outputs": [{"name": "", "type": "uint256"}], "type": "function"}]
        )
        try:
            raw_price = contract.functions.getPrice().call()
            return utils.wei_to_decimal(raw_price, 18)
        except Exception as e:
            raise ContractCallError(f"Failed to get stETH price: {str(e)}")

    def get_v2_pool_info(self) -> Dict[str, Any]:
        """
        Get information about the V2 fxUSD Base Pool.
        Note: Requires Base Pool ABI.
        """
        try:
            info = self.fxusd_base_pool.functions.getPoolInfo().call()
            return {
                "base_pool_address": info[0],
                "total_assets": utils.wei_to_decimal(info[1]),
                "total_supply": utils.wei_to_decimal(info[2]),
                # ... add more fields as needed based on ABI
            }
        except Exception as e:
            raise ContractCallError(f"Failed to get V2 pool info: {str(e)}")

    # --- V1 Legacy Read Methods ---

    def get_v1_nav(self) -> Dict[str, Decimal]:
        """
        Get the Net Asset Value (NAV) for V1 fETH and xETH.
        Note: Requires Market ABI.
        """
        try:
            nav = self.v1_market.functions.getNav().call()
            return {
                "fETH_NAV": utils.wei_to_decimal(nav[0]),
                "xETH_NAV": utils.wei_to_decimal(nav[1])
            }
        except Exception as e:
            raise ContractCallError(f"Failed to get V1 NAV: {str(e)}")

    def get_v1_collateral_ratio(self) -> Decimal:
        """
        Get the current collateral ratio of the V1 market.
        Note: Requires Market ABI.
        """
        try:
            cr = self.v1_market.functions.collateralRatio().call()
            return utils.wei_to_decimal(cr, 18)
        except Exception as e:
            raise ContractCallError(f"Failed to get V1 collateral ratio: {str(e)}")

    def get_v1_rebalance_pools(self) -> List[str]:
        """
        Get all registered V1 rebalance pools.
        Note: Requires RebalancePoolRegistry ABI.
        """
        try:
            # We assume a standard 'getPools' or similar function
            pools = self.v1_rebalance_registry.functions.getPools().call()
            return [utils.to_checksum_address(p) for p in pools]
        except Exception as e:
            logger.warning(f"Failed to fetch rebalance pools: {str(e)}")
            return []

    def get_v1_rebalance_pool_balances(self, pool_address: str, account_address: Optional[str] = None) -> Dict[str, Decimal]:
        """
        Get all balances for an account in a V1 rebalance pool.
        
        Returns:
            Dict: {staked, unlocked, unlocking} balances.
        """
        target_address = account_address or self.address
        pool = self._get_contract("rebalance_pool", pool_address)
        try:
            staked = pool.functions.balanceOf(target_address).call()
            unlocked = pool.functions.unlockedBalanceOf(target_address).call()
            unlocking = pool.functions.unlockingBalanceOf(target_address).call()
            return {
                "staked": utils.wei_to_decimal(staked, 18),
                "unlocked": utils.wei_to_decimal(unlocked, 18),
                "unlocking": utils.wei_to_decimal(unlocking, 18)
            }
        except Exception as e:
            raise ContractCallError(f"Failed to get rebalance pool balances: {str(e)}")

    # --- Infrastructure Read Methods ---

    def get_pool_manager_info(self, pool_address: str) -> Dict[str, Any]:
        """Get information from the Pool Manager for a specific pool."""
        contract = self._get_contract("pool_manager", constants.POOL_MANAGER)
        try:
            info = contract.functions.getPoolInfo(utils.to_checksum_address(pool_address)).call()
            return {
                "collateral_capacity": utils.wei_to_decimal(info[0]),
                "collateral_balance": utils.wei_to_decimal(info[1]),
                "debt_capacity": utils.wei_to_decimal(info[2]),
                "debt_balance": utils.wei_to_decimal(info[3]),
            }
        except Exception as e:
            raise ContractCallError(f"Failed to get pool manager info: {str(e)}")

    def get_reserve_pool_bonus_ratio(self, token_address: str) -> Decimal:
        """Get the bonus ratio for a token in the Reserve Pool."""
        contract = self._get_contract("reserve_pool", constants.RESERVE_POOL)
        try:
            ratio = contract.functions.bonusRatio(utils.to_checksum_address(token_address)).call()
            return utils.wei_to_decimal(ratio, 18)
        except Exception as e:
            raise ContractCallError(f"Failed to get reserve pool bonus ratio: {str(e)}")

    def get_steth_treasury_info(self) -> Dict[str, Any]:
        """Get information from the stETH Treasury."""
        contract = self._get_contract("steth_treasury", constants.STETH_TREASURY_PROXY)
        try:
            return {
                "total_base_token": utils.wei_to_decimal(contract.functions.totalBaseToken().call()),
                "collateral_ratio": utils.wei_to_decimal(contract.functions.collateralRatio().call(), 18),
                "leverage_ratio": utils.wei_to_decimal(contract.functions.leverageRatio().call(), 18),
            }
        except Exception as e:
            raise ContractCallError(f"Failed to get stETH treasury info: {str(e)}")

    def get_treasury_nav(self) -> Dict[str, Decimal]:
        """Get Net Asset Values from the treasury."""
        contract = self._get_contract("steth_treasury", constants.STETH_TREASURY_PROXY)
        try:
            nav = contract.functions.getCurrentNav().call()
            return {
                "base_nav": utils.wei_to_decimal(nav[0]),
                "f_nav": utils.wei_to_decimal(nav[1]),
                "x_nav": utils.wei_to_decimal(nav[2])
            }
        except Exception as e:
            raise ContractCallError(f"Failed to get treasury NAV: {str(e)}")

    def get_market_info(self, market_address: str) -> Dict[str, Any]:
        """
        Get info for a specific market (V1 or V2).
        """
        contract = self._get_contract("market", market_address)
        try:
            return {
                "collateral_ratio": utils.wei_to_decimal(contract.functions.collateralRatio().call(), 18),
                "total_collateral": utils.wei_to_decimal(contract.functions.totalCollateral().call()),
            }
        except Exception as e:
            raise ContractCallError(f"Failed to get market info: {str(e)}")

    def get_fxusd_balance(self, account_address: Optional[str] = None) -> Decimal:
        """Get the fxUSD balance of an account."""
        return self.get_token_balance(constants.FXUSD, account_address)

    def get_feth_balance(self, account_address: Optional[str] = None) -> Decimal:
        """Get the fETH balance of an account."""
        return self.get_token_balance(constants.FETH, account_address)

    def get_rusd_balance(self, account_address: Optional[str] = None) -> Decimal:
        """Get the rUSD balance of an account."""
        return self.get_token_balance(constants.RUSD, account_address)

    def get_arusd_balance(self, account_address: Optional[str] = None) -> Decimal:
        """Get the arUSD balance of an account."""
        # Note: ARUSD address needs to be verified and added to constants
        if not hasattr(constants, 'ARUSD'):
            raise ConfigurationError("arUSD address not yet configured in constants.py")
        return self.get_token_balance(constants.ARUSD, account_address)

    def get_btcusd_balance(self, account_address: Optional[str] = None) -> Decimal:
        """Get the btcUSD balance of an account."""
        return self.get_token_balance(constants.BTCUSD, account_address)

    def get_cvxusd_balance(self, account_address: Optional[str] = None) -> Decimal:
        """Get the cvxUSD balance of an account."""
        return self.get_token_balance(constants.CVXUSD, account_address)

    def get_xeth_balance(self, account_address: Optional[str] = None) -> Decimal:
        """Get the xETH balance of an account."""
        return self.get_token_balance(constants.XETH, account_address)

    def get_xcvx_balance(self, account_address: Optional[str] = None) -> Decimal:
        """Get the xCVX balance of an account."""
        return self.get_token_balance(constants.XCVX, account_address)

    def get_xwbtc_balance(self, account_address: Optional[str] = None) -> Decimal:
        """Get the xWBTC balance of an account."""
        return self.get_token_balance(constants.XWBTC, account_address)

    def get_xeeth_balance(self, account_address: Optional[str] = None) -> Decimal:
        """Get the xeETH balance of an account."""
        return self.get_token_balance(constants.XEETH, account_address)

    def get_xezeth_balance(self, account_address: Optional[str] = None) -> Decimal:
        """Get the xezETH balance of an account."""
        return self.get_token_balance(constants.XEZETH, account_address)

    def get_xsteth_balance(self, account_address: Optional[str] = None) -> Decimal:
        """Get the xstETH balance of an account."""
        return self.get_token_balance(constants.XSTETH, account_address)

    def get_xfrxeth_balance(self, account_address: Optional[str] = None) -> Decimal:
        """Get the xfrxETH balance of an account."""
        return self.get_token_balance(constants.XFRXETH, account_address)

    # --- Savings & Stability Pool Read Methods ---

    def get_fxsave_balance(self, account_address: Optional[str] = None) -> Decimal:
        """Get the fxSAVE (Saving fxUSD) balance of an account."""
        return self.get_token_balance(constants.SAVING_FXUSD, account_address)

    def get_fxsp_balance(self, account_address: Optional[str] = None) -> Decimal:
        """Get the fxSP (Stability Pool) balance of an account."""
        # This usually returns the staked amount
        return self.get_token_balance(constants.FXSP, account_address)

    def get_savings_apr(self) -> Decimal:
        """Get the current APR for fxSAVE."""
        contract = self._get_contract("saving_fxusd", constants.SAVING_FXUSD)
        try:
            # Get current APR from the savings contract
            apr = contract.functions.currentAPR().call()
            return utils.wei_to_decimal(apr, 18)
        except Exception:
            return Decimal(0)

    # --- Governance Read Methods ---

    def get_fxn_balance(self, account_address: Optional[str] = None) -> Decimal:
        """Get the FXN balance of an account."""
        return self.get_token_balance(constants.FXN, account_address)

    def get_vefxn_balance(self, account_address: Optional[str] = None) -> Decimal:
        """Get the veFXN balance of an account."""
        return self.get_token_balance(constants.VEFXN, account_address)

    def get_vefxn_locked_info(self, account_address: Optional[str] = None) -> Dict[str, Any]:
        """Get locked FXN info in veFXN."""
        target_address = account_address or self.address
        if not target_address:
            raise FXProtocolError("No account address provided or available in client.")
        
        try:
            locked = self.vefxn.functions.locked(utils.to_checksum_address(target_address)).call()
            return {
                "amount": utils.wei_to_decimal(locked[0], 18),
                "end": locked[1]
            }
        except Exception as e:
            raise ContractCallError(f"Failed to get veFXN locked info: {str(e)}")

    def get_gauge_weight(self, gauge_address: str) -> Decimal:
        """Get the relative weight of a gauge in the controller."""
        try:
            # We use the pre-loaded gauge_controller if available
            weight = self.gauge_controller.functions.get_gauge_weight(
                utils.to_checksum_address(gauge_address)
            ).call()
            # Weights are typically returned with 18 decimals in GaugeController
            return utils.wei_to_decimal(weight, 18)
        except Exception as e:
            # Fallback for when ABI is empty or call fails
            raise ContractCallError(f"Failed to get gauge weight: {str(e)}")

    def get_gauge_relative_weight(self, gauge_address: str) -> Decimal:
        """Get the relative weight of a gauge."""
        try:
            weight = self.gauge_controller.functions.gauge_relative_weight(
                utils.to_checksum_address(gauge_address)
            ).call()
            return utils.wei_to_decimal(weight, 18)
        except Exception as e:
            raise ContractCallError(f"Failed to get gauge relative weight: {str(e)}")

    def get_claimable_rewards(self, gauge_address: str, token_address: str, account_address: Optional[str] = None) -> Decimal:
        """Get claimable rewards from a gauge."""
        target_address = account_address or self.address
        if not target_address:
            raise FXProtocolError("No account address provided or available in client.")
        
        gauge = self._get_contract("liquidity_gauge", gauge_address)
        try:
            # LiquidityGauge has claimable(address, address)
            amount = gauge.functions.claimable(
                utils.to_checksum_address(target_address),
                utils.to_checksum_address(token_address)
            ).call()
            # We need to know token decimals, assuming 18 for now
            return utils.wei_to_decimal(amount, 18)
        except Exception as e:
            raise ContractCallError(f"Failed to get claimable rewards: {str(e)}")

    def get_all_balances(self, account_address: Optional[str] = None) -> Dict[str, Decimal]:
        """
        Get all protocol token balances for an account.
        
        Includes all protocol tokens: fxUSD, fETH, rUSD, btcUSD, cvxUSD, arUSD,
        and all x tokens (xETH, xCVX, xWBTC, xeETH, xezETH, xstETH, xfrxETH).
        
        Args:
            account_address: Optional account address.
            
        Returns:
            Dict[str, Decimal]: Map of token names to balances.
        """
        tokens = {
            "fxUSD": constants.FXUSD,
            "fETH": constants.FETH,
            "rUSD": constants.RUSD,
            "btcUSD": constants.BTCUSD,
            "cvxUSD": constants.CVXUSD,
            "xETH": constants.XETH,
            "xCVX": constants.XCVX,
            "xWBTC": constants.XWBTC,
            "xeETH": constants.XEETH,
            "xezETH": constants.XEZETH,
            "xstETH": constants.XSTETH,
            "xfrxETH": constants.XFRXETH,
        }
        
        balances = {}
        for name, address in tokens.items():
            try:
                balances[name] = self.get_token_balance(address, account_address)
            except Exception:
                balances[name] = Decimal(0)
                
        # Handle arUSD separately since it might be missing
        if hasattr(constants, 'ARUSD'):
            try:
                balances["arUSD"] = self.get_token_balance(constants.ARUSD, account_address)
            except Exception:
                balances["arUSD"] = Decimal(0)
                
        return balances

    def get_all_gauge_balances(self, account_address: Optional[str] = None) -> Dict[str, Decimal]:
        """
        Get all liquidity gauge stakes for an account.
        """
        balances = {}
        for name, address in constants.GAUGES.items():
            try:
                balances[name] = self.get_token_balance(address, account_address)
            except Exception:
                balances[name] = Decimal(0)
        return balances

    def mint_via_treasury(self, base_in: Union[int, float, Decimal, str], recipient: Optional[str] = None, option: int = 0) -> str:
        """
        Mint fToken and/or xToken via the Treasury.
        
        Args:
            base_in: human-readable amount of base token.
            recipient: recipient address.
            option: MintOption (0: Both, 1: fToken, 2: xToken).
        """
        contract = self._get_contract("steth_treasury", constants.STETH_TREASURY_PROXY)
        target_recipient = recipient or self.address
        raw_base_in = utils.decimal_to_wei(base_in, 18)
        
        return self._build_and_send_transaction(
            contract.functions.mint(raw_base_in, target_recipient, option)
        )

    def redeem_via_treasury(self, f_token_in: Union[int, float, Decimal, str] = 0, x_token_in: Union[int, float, Decimal, str] = 0, owner: Optional[str] = None) -> str:
        """
        Redeem fToken and/or xToken for base collateral via Treasury.
        """
        contract = self._get_contract("steth_treasury", constants.STETH_TREASURY_PROXY)
        target_owner = owner or self.address
        raw_f_in = utils.decimal_to_wei(f_token_in, 18)
        raw_x_in = utils.decimal_to_wei(x_token_in, 18)
        
        return self._build_and_send_transaction(
            contract.functions.redeem(raw_f_in, raw_x_in, target_owner)
        )

    def harvest_treasury(self) -> str:
        """
        Harvest rewards from the Treasury.
        """
        contract = self._get_contract("steth_treasury", constants.STETH_TREASURY_PROXY)
        return self._build_and_send_transaction(contract.functions.harvest())

    def initialize_v2_treasury(self, sample_interval: int) -> str:
        """
        Initialize V2 features for the Treasury.
        """
        contract = self._get_contract("steth_treasury", constants.STETH_TREASURY_PROXY)
        return self._build_and_send_transaction(contract.functions.initializeV2(sample_interval))

    # --- Write Methods ---

    def _build_and_send_transaction(self, contract_function, value: int = 0) -> str:
        """
        Internal helper to build, sign, and send a transaction.
        
        Supports both private key signing and browser wallet signing.
        
        Args:
            contract_function: The contract function to call.
            value: Optional ETH value to send with the transaction (in Wei).
            
        Returns:
            str: The transaction hash.
        """
        if not self.account and not self.use_browser_wallet:
            raise ConfigurationError(
                "Private key or browser wallet required for write operations. "
                "Provide a private key, set FX_PROTOCOL_PRIVATE_KEY environment variable, "
                "or use use_browser_wallet=True with a browser wallet extension."
            )

        if not self.address:
            raise ConfigurationError("No account address available for transaction.")

        nonce = self.w3.eth.get_transaction_count(self.address)
        
        tx_params = {
            'from': self.address,
            'nonce': nonce,
            'value': value,
            'gasPrice': self.w3.eth.gas_price
        }

        try:
            # Estimate gas
            tx_params['gas'] = contract_function.estimate_gas(tx_params)
            
            # Build transaction
            built_tx = contract_function.build_transaction(tx_params)
            
            # Sign and send based on wallet type
            if self.use_browser_wallet:
                # Browser wallet: send_transaction prompts user in browser
                # The provider (MetaMask, etc.) handles signing
                tx_hash = self.w3.eth.send_transaction(built_tx)
            else:
                # Private key: sign locally and send raw transaction
                signed_tx = self.w3.eth.account.sign_transaction(built_tx, self.account.key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status != 1:
                raise TransactionFailedError(f"Transaction failed: {tx_hash.hex()}")
                
            return tx_hash.hex()
            
        except Exception as e:
            if isinstance(e, TransactionFailedError):
                raise
            raise TransactionFailedError(f"Failed to send transaction: {str(e)}")

    def approve(self, token_address: str, spender_address: str, amount: Union[int, float, Decimal, str]) -> str:
        """
        Approve a spender to spend tokens.
        
        Args:
            token_address: The address of the token contract.
            spender_address: The address of the spender.
            amount: Human-readable amount to approve.
            
        Returns:
            str: Transaction hash.
        """
        contract = self.w3.eth.contract(
            address=utils.to_checksum_address(token_address),
            abi=[
                {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
            ]
        )
        
        decimals = contract.functions.decimals().call()
        raw_amount = utils.decimal_to_wei(amount, decimals)
        
        return self._build_and_send_transaction(contract.functions.approve(spender_address, raw_amount))

    def transfer(self, token_address: str, recipient_address: str, amount: Union[int, float, Decimal, str]) -> str:
        """
        Transfer tokens to a recipient.
        
        Args:
            token_address: The address of the token contract.
            recipient_address: The address of the recipient.
            amount: Human-readable amount to transfer.
            
        Returns:
            str: Transaction hash.
        """
        contract = self.w3.eth.contract(
            address=utils.to_checksum_address(token_address),
            abi=[
                {"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
            ]
        )
        
        decimals = contract.functions.decimals().call()
        raw_amount = utils.decimal_to_wei(amount, decimals)
        
        return self._build_and_send_transaction(contract.functions.transfer(recipient_address, raw_amount))

    # --- f(x) Protocol Specific Write Methods ---

    def mint_f_token(self, market_address: str, base_in: Union[int, float, Decimal, str], recipient: Optional[str] = None, min_f_token_out: Union[int, float, Decimal, str] = 0) -> str:
        """
        Mint fToken using base collateral (e.g., stETH).
        
        Args:
            market_address: The address of the market contract.
            base_in: Human-readable amount of base token to provide.
            recipient: Optional recipient address (defaults to client address).
            min_f_token_out: Human-readable minimum fToken to receive.
        """
        contract = self._get_contract("market", market_address)
        target_recipient = recipient or self.address
        
        # We need to know the decimals of the base token, usually 18 for stETH
        # For simplicity, we assume 18 here, but a robust version would check
        raw_base_in = utils.decimal_to_wei(base_in, 18)
        raw_min_out = utils.decimal_to_wei(min_f_token_out, 18)
        
        return self._build_and_send_transaction(
            contract.functions.mintFToken(raw_base_in, target_recipient, raw_min_out)
        )

    def mint_x_token(self, market_address: str, base_in: Union[int, float, Decimal, str], recipient: Optional[str] = None, min_x_token_out: Union[int, float, Decimal, str] = 0) -> str:
        """
        Mint xToken using base collateral.
        """
        contract = self._get_contract("market", market_address)
        target_recipient = recipient or self.address
        
        raw_base_in = utils.decimal_to_wei(base_in, 18)
        raw_min_out = utils.decimal_to_wei(min_x_token_out, 18)
        
        return self._build_and_send_transaction(
            contract.functions.mintXToken(raw_base_in, target_recipient, raw_min_out)
        )

    def mint_both_tokens(self, market_address: str, base_in: Union[int, float, Decimal, str], recipient: Optional[str] = None, min_f_token_out: Union[int, float, Decimal, str] = 0, min_x_token_out: Union[int, float, Decimal, str] = 0) -> str:
        """
        Mint both fToken and xToken proportionally.
        """
        contract = self._get_contract("market", market_address)
        target_recipient = recipient or self.address
        
        raw_base_in = utils.decimal_to_wei(base_in, 18)
        raw_min_f_out = utils.decimal_to_wei(min_f_token_out, 18)
        raw_min_x_out = utils.decimal_to_wei(min_x_token_out, 18)
        
        return self._build_and_send_transaction(
            contract.functions.mint(raw_base_in, target_recipient, raw_min_f_out, raw_min_x_out)
        )

    def redeem(self, market_address: str, f_token_in: Union[int, float, Decimal, str] = 0, x_token_in: Union[int, float, Decimal, str] = 0, recipient: Optional[str] = None, min_base_out: Union[int, float, Decimal, str] = 0) -> str:
        """
        Redeem fToken and/or xToken for base collateral.
        """
        contract = self._get_contract("market", market_address)
        target_recipient = recipient or self.address
        
        raw_f_in = utils.decimal_to_wei(f_token_in, 18)
        raw_x_in = utils.decimal_to_wei(x_token_in, 18)
        raw_min_base_out = utils.decimal_to_wei(min_base_out, 18)
        
        return self._build_and_send_transaction(
            contract.functions.redeem(raw_f_in, raw_x_in, target_recipient, raw_min_base_out)
        )

    # --- Governance Write Methods ---

    def deposit_to_vefxn(self, amount: Union[int, float, Decimal, str], unlock_time: int) -> str:
        """
        Deposit FXN into veFXN to get voting power.
        
        Args:
            amount: Amount of FXN to deposit.
            unlock_time: Unix timestamp for the unlock date.
        """
        raw_amount = utils.decimal_to_wei(amount, 18)
        # Note: 'create_lock' is the standard function name in VotingEscrow
        return self._build_and_send_transaction(
            self.vefxn.functions.create_lock(raw_amount, unlock_time)
        )

    def vote_for_gauge_weight(self, gauge_address: str, user_weight: int) -> str:
        """
        Vote for a gauge's weight in the GaugeController.
        
        Args:
            gauge_address: The address of the gauge.
            user_weight: The weight to assign (out of 10000).
        """
        return self._build_and_send_transaction(
            self.gauge_controller.functions.vote_for_gauge_weights(
                utils.to_checksum_address(gauge_address),
                user_weight
            )
        )

    def claim_gauge_rewards(self, gauge_address: str, account: Optional[str] = None) -> str:
        """
        Claim rewards from a liquidity gauge.
        
        Args:
            gauge_address: The address of the gauge.
            account: Optional account address to claim for.
        """
        gauge = self._get_contract("liquidity_gauge", gauge_address)
        target_account = account or self.address
        if not target_account:
            raise FXProtocolError("No account address provided or available in client.")
            
        return self._build_and_send_transaction(gauge.functions.claim(target_account))

    def claim_all_gauge_rewards(self) -> List[str]:
        """
        Claim rewards from all configured gauges.
        """
        tx_hashes = []
        for name, address in constants.GAUGES.items():
            try:
                logger.info(f"Claiming rewards for gauge: {name}")
                tx_hash = self.claim_gauge_rewards(address)
                tx_hashes.append(tx_hash)
            except Exception as e:
                logger.warning(f"Failed to claim rewards for gauge {name}: {str(e)}")
        return tx_hashes

    def operate_position(self, pool_address: str, position_id: int, new_collateral: Union[int, float, Decimal, str], new_debt: Union[int, float, Decimal, str]) -> str:
        """
        Operate on a position in the Pool Manager.
        
        Args:
            pool_address: The address of the pool.
            position_id: The ID of the position.
            new_collateral: The new human-readable collateral amount (delta).
            new_debt: The new human-readable debt amount (delta).
        """
        contract = self._get_contract("pool_manager", constants.POOL_MANAGER)
        raw_coll = utils.decimal_to_wei(new_collateral, 18)
        raw_debt = utils.decimal_to_wei(new_debt, 18)
        
        return self._build_and_send_transaction(
            contract.functions.operate(
                utils.to_checksum_address(pool_address),
                position_id,
                raw_coll,
                raw_debt
            )
        )

    def rebalance_position(self, pool_address: str, receiver: str, position_id: int, max_fxusd: Union[int, float, Decimal, str], max_stable: Union[int, float, Decimal, str]) -> str:
        """
        Rebalance a position in the Pool Manager.
        """
        contract = self._get_contract("pool_manager", constants.POOL_MANAGER)
        raw_fxusd = utils.decimal_to_wei(max_fxusd, 18)
        raw_stable = utils.decimal_to_wei(max_stable, 18)
        
        return self._build_and_send_transaction(
            contract.functions.rebalance(
                utils.to_checksum_address(pool_address),
                utils.to_checksum_address(receiver),
                position_id,
                raw_fxusd,
                raw_stable
            )
        )

    def liquidate_position(self, pool_address: str, receiver: str, position_id: int, max_fxusd: Union[int, float, Decimal, str], max_stable: Union[int, float, Decimal, str]) -> str:
        """
        Liquidate a position in the Pool Manager.
        """
        contract = self._get_contract("pool_manager", constants.POOL_MANAGER)
        raw_fxusd = utils.decimal_to_wei(max_fxusd, 18)
        raw_stable = utils.decimal_to_wei(max_stable, 18)
        
        return self._build_and_send_transaction(
            contract.functions.liquidate(
                utils.to_checksum_address(pool_address),
                utils.to_checksum_address(receiver),
                position_id,
                raw_fxusd,
                raw_stable
            )
        )

    def harvest_pool_manager(self, pool_address: str) -> str:
        """
        Harvest rewards for a pool in the Pool Manager.
        """
        contract = self._get_contract("pool_manager", constants.POOL_MANAGER)
        return self._build_and_send_transaction(
            contract.functions.harvest(utils.to_checksum_address(pool_address))
        )

    def get_position_info(self, position_id: int) -> Dict[str, Any]:
        """
        Get details for a specific position in the Pool Manager.
        
        Returns:
            Dict: collateral, debt, and owner info.
        """
        contract = self._get_contract("pool_manager", constants.POOL_MANAGER)
        try:
            info = contract.functions.getPosition(position_id).call()
            # Assuming returns (owner, collateral, debt) based on V2 common patterns
            return {
                "owner": info[0],
                "collateral": utils.wei_to_decimal(info[1]),
                "debt": utils.wei_to_decimal(info[2])
            }
        except Exception as e:
            raise ContractCallError(f"Failed to get position info: {str(e)}")

    def get_peg_keeper_info(self) -> Dict[str, Any]:
        """Get the current status from the Peg Keeper."""
        contract = self._get_contract("peg_keeper", constants.PEG_KEEPER)
        try:
            return {
                "is_active": contract.functions.isActive().call(),
                "debt_ceiling": utils.wei_to_decimal(contract.functions.debtCeiling().call()),
                "total_debt": utils.wei_to_decimal(contract.functions.totalDebt().call()),
            }
        except Exception as e:
            raise ContractCallError(f"Failed to get peg keeper info: {str(e)}")

    def flash_loan(self, token_address: str, amount: Union[int, float, Decimal, str], receiver: str, data: bytes = b"") -> str:
        """
        Execute a flash loan from the Pool Manager.
        """
        contract = self._get_contract("pool_manager", constants.POOL_MANAGER)
        raw_amount = utils.decimal_to_wei(amount, 18)
        
        return self._build_and_send_transaction(
            contract.functions.flashLoan(
                utils.to_checksum_address(receiver),
                utils.to_checksum_address(token_address),
                raw_amount,
                data
            )
        )

    def request_reserve_pool_bonus(self, token_address: str, recipient: str, original_amount: Union[int, float, Decimal, str]) -> str:
        """
        Request a bonus from the Reserve Pool.
        """
        contract = self._get_contract("reserve_pool", constants.RESERVE_POOL)
        raw_amount = utils.decimal_to_wei(original_amount, 18)
        
        return self._build_and_send_transaction(
            contract.functions.requestBonus(
                utils.to_checksum_address(token_address),
                utils.to_checksum_address(recipient),
                raw_amount
            )
        )

    # --- V1 Write Methods ---

    def deposit_to_rebalance_pool(self, pool_address: str, amount: Union[int, float, Decimal, str], recipient: Optional[str] = None) -> str:
        """
        Deposit assets into a V1 rebalance pool.
        
        Args:
            pool_address: The address of the rebalance pool.
            amount: Human-readable amount to deposit.
            recipient: Optional recipient address (defaults to client address).
        """
        pool = self._get_contract("rebalance_pool", pool_address)
        target_recipient = recipient or self.address
        raw_amount = utils.decimal_to_wei(amount, 18)
        return self._build_and_send_transaction(pool.functions.deposit(raw_amount, utils.to_checksum_address(target_recipient)))

    def unlock_rebalance_pool_assets(self, pool_address: str, amount: Union[int, float, Decimal, str]) -> str:
        """
        Start the unlock process for assets in a V1 rebalance pool.
        
        Args:
            pool_address: The address of the rebalance pool.
            amount: Human-readable amount to unlock.
        """
        pool = self._get_contract("rebalance_pool", pool_address)
        raw_amount = utils.decimal_to_wei(amount, 18)
        return self._build_and_send_transaction(pool.functions.unlock(raw_amount))

    def withdraw_unlocked_rebalance_pool_assets(self, pool_address: str, claim_rewards: bool = True) -> str:
        """
        Withdraw unlocked assets from a V1 rebalance pool.
        
        Args:
            pool_address: The address of the rebalance pool.
            claim_rewards: Whether to claim rewards during withdrawal.
        """
        pool = self._get_contract("rebalance_pool", pool_address)
        return self._build_and_send_transaction(pool.functions.withdrawUnlocked(claim_rewards))

    def claim_rebalance_pool_rewards(self, pool_address: str, tokens: List[str]) -> str:
        """
        Claim rewards from a V1 rebalance pool.
        
        Args:
            pool_address: The address of the rebalance pool.
            tokens: List of reward token addresses to claim.
        """
        pool = self._get_contract("rebalance_pool", pool_address)
        return self._build_and_send_transaction(pool.functions.claim([utils.to_checksum_address(t) for t in tokens]))

    # --- Supporting Write Methods ---

    def swap(self, token_in: str, amount_in: Union[int, float, Decimal, str], encoding: int, routes: List[int]) -> str:
        """
        Swap tokens using the MultiPathConverter.
        
        Args:
            token_in: The address of the token to swap from.
            amount_in: Human-readable amount to swap.
            encoding: Encoding for the converter.
            routes: List of routes for the swap.
        """
        raw_amount_in = utils.decimal_to_wei(amount_in, 18)  # Adjust decimals as needed
        return self._build_and_send_transaction(
            self.multipath_converter.functions.convert(
                utils.to_checksum_address(token_in),
                raw_amount_in,
                encoding,
                routes
            )
        )

    def mint_f_token_via_gateway(self, amount_eth: Union[int, float, Decimal, str], min_f_token_out: Union[int, float, Decimal, str] = 0) -> str:
        """
        Deposit ETH/stETH through the stETH Gateway to mint fToken.
        
        Args:
            amount_eth: Human-readable amount of ETH to send.
            min_f_token_out: Human-readable minimum fToken to receive.
        """
        raw_amount_eth = utils.decimal_to_wei(amount_eth, 18)
        raw_min_out = utils.decimal_to_wei(min_f_token_out, 18)
        
        return self._build_and_send_transaction(
            self.steth_gateway.functions.mintFToken(raw_min_out),
            value=raw_amount_eth
        )

    def mint_x_token_via_gateway(self, amount_eth: Union[int, float, Decimal, str], min_x_token_out: Union[int, float, Decimal, str] = 0) -> str:
        """
        Deposit ETH/stETH through the stETH Gateway to mint xToken.
        """
        raw_amount_eth = utils.decimal_to_wei(amount_eth, 18)
        raw_min_out = utils.decimal_to_wei(min_x_token_out, 18)
        
        return self._build_and_send_transaction(
            self.steth_gateway.functions.mintXToken(raw_min_out),
            value=raw_amount_eth
        )

    # --- Savings Write Methods ---

    def deposit_fxsave(self, amount: Union[int, float, Decimal, str]) -> str:
        """
        Deposit fxUSD into fxSAVE.
        """
        contract = self._get_contract("saving_fxusd", constants.SAVING_FXUSD)
        raw_amount = utils.decimal_to_wei(amount, 18)
        return self._build_and_send_transaction(contract.functions.deposit(raw_amount))

    def redeem_fxsave(self, amount: Union[int, float, Decimal, str]) -> str:
        """
        Redeem fxUSD from fxSAVE.
        """
        contract = self._get_contract("saving_fxusd", constants.SAVING_FXUSD)
        raw_amount = utils.decimal_to_wei(amount, 18)
        return self._build_and_send_transaction(contract.functions.withdraw(raw_amount))

    # --- Stability Pool Write Methods ---

    def deposit_to_stability_pool(self, amount: Union[int, float, Decimal, str]) -> str:
        """
        Deposit assets into the stability pool (fxSP).
        """
        contract = self._get_contract("fxsp", constants.FXSP)
        raw_amount = utils.decimal_to_wei(amount, 18)
        return self._build_and_send_transaction(contract.functions.deposit(raw_amount))

    def withdraw_from_stability_pool(self, amount: Union[int, float, Decimal, str]) -> str:
        """
        Withdraw assets from the stability pool (fxSP).
        """
        contract = self._get_contract("fxsp", constants.FXSP)
        raw_amount = utils.decimal_to_wei(amount, 18)
        return self._build_and_send_transaction(contract.functions.withdraw(raw_amount))

    # --- Vesting Write Methods ---

    def claim_fxn_vesting(self) -> str:
        """Claim vested FXN tokens."""
        vesting = self._get_contract("vesting", constants.VESTING_FXN)
        return self._build_and_send_transaction(vesting.functions.claim())

    def claim_feth_vesting(self) -> str:
        """Claim vested fETH tokens."""
        vesting = self._get_contract("vesting", constants.VESTING_FETH)
        return self._build_and_send_transaction(vesting.functions.claim())

    def claim_fxusd_vesting(self) -> str:
        """Claim vested fxUSD tokens."""
        vesting = self._get_contract("vesting", constants.VESTING_FXUSD)
        return self._build_and_send_transaction(vesting.functions.claim())

    # --- Convex Finance Integration ---

    def get_convex_vault_address(
        self,
        user_address: str,
        pool_id: int,
        from_block: int = 0
    ) -> Optional[str]:
        """
        Get user's Convex vault address by querying AddUserVault events.
        
        The vault address is created via CREATE in the same transaction that emits
        the AddUserVault event. We extract it from the transaction receipt.
        
        Args:
            user_address: User's wallet address
            pool_id: Convex pool ID
            from_block: Block number to start searching from (0 = from genesis)
        
        Returns:
            Vault address if found, None if vault doesn't exist
        
        Note: If the vault address cannot be extracted automatically, users can
        provide their vault address directly or query it from the transaction hash
        using get_convex_vault_address_from_tx().
        """
        registry = self._get_contract("convex_vault_factory", constants.CONVEX_VAULT_REGISTRY)
        user_address_checksum = utils.to_checksum_address(user_address)
        
        try:
            # Query AddUserVault events from the registry
            events = registry.events.AddUserVault.get_logs(
                fromBlock=from_block,
                argument_filters={
                    "user": user_address_checksum,
                    "poolid": pool_id
                }
            )
            
            if events:
                # Get the most recent event (latest vault creation)
                latest_event = events[-1]
                tx_hash = latest_event['transactionHash']
                
                # Try to extract vault address from the transaction receipt
                vault_address = self.get_convex_vault_address_from_tx(tx_hash)
                if vault_address:
                    return vault_address
                
                # Fallback: Try to find the vault by querying the factory contract
                # Some factory contracts have a mapping to get vault addresses
                # For now, we'll log a warning and return None
                logger.warning(
                    f"Could not extract vault address from tx {tx_hash.hex()}. "
                    f"Please provide your vault address directly or query it manually."
                )
                
        except Exception as e:
            logger.debug(f"Error querying vault events: {e}")
        
        return None

    def create_convex_vault(self, pool_id: int) -> Dict[str, Any]:
        """
        Create a Convex vault for the user.
        
        Args:
            pool_id: Convex pool ID
        
        Returns:
            Dictionary with:
            - transaction_hash: Transaction hash
            - vault_address: Vault address (if successfully extracted, None otherwise)
        
        Note: The vault address is returned by createVault() and can be extracted
        from the transaction receipt after confirmation. If extraction fails, users
        can query their vault address using get_convex_vault_address() or
        get_convex_vault_address_from_tx().
        """
        if not self.account:
            raise FXProtocolError("Private key required to create a vault.")
        
        factory = self._get_contract("convex_vault_factory", constants.CONVEX_VAULT_FACTORY)
        tx_hash = self._build_and_send_transaction(
            factory.functions.createVault(pool_id)
        )
        
        # Wait for transaction confirmation to get the vault address
        try:
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            # Try to extract vault address from the transaction receipt
            vault_address = self.get_convex_vault_address_from_tx(tx_hash)
            
            if vault_address:
                logger.info(f"Vault created successfully at address: {vault_address}")
            else:
                logger.warning(
                    f"Vault creation transaction confirmed, but could not extract vault address. "
                    f"Transaction hash: {tx_hash}. "
                    f"Please query your vault address using get_convex_vault_address() or "
                    f"get_convex_vault_address_from_tx('{tx_hash}')."
                )
            
            return {
                "transaction_hash": tx_hash,
                "vault_address": vault_address
            }
        except Exception as e:
            logger.warning(f"Could not wait for transaction confirmation: {e}")
            return {
                "transaction_hash": tx_hash,
                "vault_address": None
            }

    def get_convex_vault_address_or_create(
        self,
        pool_id: int,
        user_address: Optional[str] = None,
        auto_create: bool = False
    ) -> Optional[str]:
        """
        Get user's vault address, optionally creating it if it doesn't exist.
        
        Args:
            pool_id: Convex pool ID
            user_address: User address (defaults to client's address)
            auto_create: If True, create vault if it doesn't exist
        
        Returns:
            Vault address, or None if not found and auto_create is False
        """
        target_address = user_address or self.address
        if not target_address:
            raise FXProtocolError("No user address provided or available in client.")
        
        vault_address = self.get_convex_vault_address(target_address, pool_id)
        
        if vault_address:
            return vault_address
        
        if auto_create and self.account:
            # Create vault
            result = self.create_convex_vault(pool_id)
            logger.info(f"Vault creation transaction: {result['transaction_hash']}")
            # User should query again after confirmation to get the vault address
            return None
        
        return None

    def get_convex_vault_balance(
        self,
        vault_address: str,
        token_address: Optional[str] = None
    ) -> Decimal:
        """
        Get the staked balance in a Convex vault.
        
        Args:
            vault_address: User's vault address (user-specific, each user has their own)
            token_address: Optional token address to check balance for
        
        Returns:
            Staked balance in the vault
        
        Raises:
            ContractCallError: If the vault address is invalid or the call fails
        """
        vault_address = utils.to_checksum_address(vault_address)
        
        # Validate vault address
        if not self.w3.is_address(vault_address):
            raise ContractCallError(f"Invalid vault address: {vault_address}")
        
        vault = self._get_contract("convex_vault", vault_address)
        
        # Verify the vault exists and is valid
        try:
            vault.functions.owner().call()
        except Exception as e:
            raise ContractCallError(
                f"Invalid vault address or vault does not exist: {vault_address}. "
                f"Error: {str(e)}"
            )
        
        # The vault holds staked tokens - we need to check the staking token balance
        # or query the rewards contract for the staked amount
        try:
            # Get the staking token address
            staking_token = vault.functions.stakingToken().call()
            token_contract = self.w3.eth.contract(
                address=utils.to_checksum_address(staking_token),
                abi=[
                    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
                    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
                ]
            )
            balance = token_contract.functions.balanceOf(vault_address).call()
            decimals = token_contract.functions.decimals().call()
            return utils.wei_to_decimal(balance, decimals)
        except Exception as e:
            raise ContractCallError(f"Failed to get vault balance: {str(e)}")

    def get_convex_vault_rewards(
        self,
        vault_address: str
    ) -> Dict[str, Any]:
        """
        Get claimable rewards for a Convex vault.
        
        Args:
            vault_address: User's vault address (user-specific)
        
        Returns:
            Dictionary with:
            - token_addresses: List of reward token addresses
            - amounts: Dictionary mapping token addresses to claimable amounts (Decimal)
        
        Raises:
            ContractCallError: If the vault address is invalid or the call fails
        """
        vault_address = utils.to_checksum_address(vault_address)
        
        # Validate vault address
        if not self.w3.is_address(vault_address):
            raise ContractCallError(f"Invalid vault address: {vault_address}")
        
        vault = self._get_contract("convex_vault", vault_address)
        
        # Verify the vault exists
        try:
            vault.functions.owner().call()
        except Exception as e:
            raise ContractCallError(
                f"Invalid vault address or vault does not exist: {vault_address}. "
                f"Error: {str(e)}"
            )
        
        try:
            # Call earned() which returns (address[] token_addresses, uint256[] total_earned)
            result = vault.functions.earned().call()
            token_addresses = result[0]
            amounts = result[1]
            
            # Convert amounts to Decimal
            # We need to get decimals for each token
            reward_dict = {}
            for i, token_addr in enumerate(token_addresses):
                try:
                    token_contract = self.w3.eth.contract(
                        address=utils.to_checksum_address(token_addr),
                        abi=[
                            {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
                        ]
                    )
                    decimals = token_contract.functions.decimals().call()
                    reward_dict[token_addr] = utils.wei_to_decimal(amounts[i], decimals)
                except Exception:
                    # Default to 18 decimals if we can't get it
                    reward_dict[token_addr] = utils.wei_to_decimal(amounts[i], 18)
            
            return {
                "token_addresses": token_addresses,
                "amounts": reward_dict
            }
        except Exception as e:
            raise ContractCallError(f"Failed to get vault rewards: {str(e)}")

    def deposit_to_convex_vault(
        self,
        vault_address: str,
        amount: Union[int, float, Decimal, str],
        manage: bool = False
    ) -> str:
        """
        Deposit tokens to a Convex vault.
        
        Args:
            vault_address: User's vault address (user-specific, each user has their own)
            amount: Amount of LP tokens to deposit
            manage: Whether to manage the deposit (auto-stake, etc.)
        
        Returns:
            Transaction hash
        
        Raises:
            FXProtocolError: If private key is not available
            ContractCallError: If the vault address is invalid
            InsufficientBalanceError: If user doesn't have enough tokens
        """
        if not self.account:
            raise FXProtocolError("Private key required to deposit tokens.")
        
        vault_address = utils.to_checksum_address(vault_address)
        
        # Validate vault address
        if not self.w3.is_address(vault_address):
            raise ContractCallError(f"Invalid vault address: {vault_address}")
        
        # Validate amount
        if amount <= 0:
            raise FXProtocolError("Deposit amount must be greater than zero.")
        
        vault = self._get_contract("convex_vault", vault_address)
        
        # Verify the vault exists
        try:
            vault_owner = vault.functions.owner().call()
            if vault_owner.lower() != self.address.lower():
                logger.warning(
                    f"Vault owner ({vault_owner}) does not match client address ({self.address}). "
                    f"Proceeding with deposit anyway."
                )
        except Exception as e:
            raise ContractCallError(
                f"Invalid vault address or vault does not exist: {vault_address}. "
                f"Error: {str(e)}"
            )
        
        # Get staking token address and check balance
        try:
            staking_token = vault.functions.stakingToken().call()
            staking_token_contract = self.w3.eth.contract(
                address=utils.to_checksum_address(staking_token),
                abi=self._load_abi("erc20")
            )
            
            # Check balance
            decimals = staking_token_contract.functions.decimals().call()
            raw_amount = utils.decimal_to_wei(amount, decimals)
            balance = staking_token_contract.functions.balanceOf(self.address).call()
            
            if balance < raw_amount:
                raise InsufficientBalanceError(
                    f"Insufficient balance. Required: {amount}, Available: "
                    f"{utils.wei_to_decimal(balance, decimals)}"
                )
            
            # Check and approve if needed
            allowance = staking_token_contract.functions.allowance(
                self.address, vault_address
            ).call()
            
            if allowance < raw_amount:
                logger.info(f"Approving {amount} tokens for vault deposit...")
                self.approve(
                    token_address=staking_token,
                    spender_address=vault_address,
                    amount=amount
                )
        except InsufficientBalanceError:
            raise
        except Exception as e:
            logger.warning(f"Could not validate balance/allowance: {e}. Proceeding with deposit...")
            # Default to 18 decimals if we can't determine
            raw_amount = utils.decimal_to_wei(amount, 18)
        
        if manage:
            return self._build_and_send_transaction(
                vault.functions.deposit(raw_amount, True)
            )
        else:
            return self._build_and_send_transaction(
                vault.functions.deposit(raw_amount)
            )

    def withdraw_from_convex_vault(
        self,
        vault_address: str,
        amount: Union[int, float, Decimal, str]
    ) -> str:
        """
        Withdraw tokens from a Convex vault.
        
        Args:
            vault_address: User's vault address (user-specific)
            amount: Amount of tokens to withdraw
        
        Returns:
            Transaction hash
        
        Raises:
            FXProtocolError: If private key is not available
            ContractCallError: If the vault address is invalid
            InsufficientBalanceError: If vault doesn't have enough tokens
        """
        if not self.account:
            raise FXProtocolError("Private key required to withdraw tokens.")
        
        vault_address = utils.to_checksum_address(vault_address)
        
        # Validate vault address
        if not self.w3.is_address(vault_address):
            raise ContractCallError(f"Invalid vault address: {vault_address}")
        
        # Validate amount
        if amount <= 0:
            raise FXProtocolError("Withdrawal amount must be greater than zero.")
        
        vault = self._get_contract("convex_vault", vault_address)
        
        # Verify the vault exists
        try:
            vault.functions.owner().call()
        except Exception as e:
            raise ContractCallError(
                f"Invalid vault address or vault does not exist: {vault_address}. "
                f"Error: {str(e)}"
            )
        
        # Check vault balance
        try:
            vault_balance = self.get_convex_vault_balance(vault_address)
            if vault_balance < Decimal(str(amount)):
                raise InsufficientBalanceError(
                    f"Insufficient vault balance. Required: {amount}, Available: {vault_balance}"
                )
        except InsufficientBalanceError:
            raise
        except Exception as e:
            logger.warning(f"Could not validate vault balance: {e}. Proceeding with withdrawal...")
        
        # Get decimals from staking token
        try:
            staking_token = vault.functions.stakingToken().call()
            staking_token_contract = self.w3.eth.contract(
                address=utils.to_checksum_address(staking_token),
                abi=self._load_abi("erc20")
            )
            decimals = staking_token_contract.functions.decimals().call()
            raw_amount = utils.decimal_to_wei(amount, decimals)
        except Exception:
            # Default to 18 decimals if we can't determine
            raw_amount = utils.decimal_to_wei(amount, 18)
        
        return self._build_and_send_transaction(
            vault.functions.withdraw(raw_amount)
        )

    def claim_convex_vault_rewards(
        self,
        vault_address: str,
        claim: bool = True,
        token_list: Optional[List[str]] = None
    ) -> str:
        """
        Claim rewards from a Convex vault.
        
        Args:
            vault_address: User's vault address (user-specific)
            claim: Whether to claim rewards
            token_list: Optional list of specific tokens to claim (if None, claims all)
        
        Returns:
            Transaction hash
        
        Raises:
            FXProtocolError: If private key is not available
            ContractCallError: If the vault address is invalid
        """
        if not self.account:
            raise FXProtocolError("Private key required to claim rewards.")
        
        vault_address = utils.to_checksum_address(vault_address)
        
        # Validate vault address
        if not self.w3.is_address(vault_address):
            raise ContractCallError(f"Invalid vault address: {vault_address}")
        
        vault = self._get_contract("convex_vault", vault_address)
        
        # Verify the vault exists
        try:
            vault.functions.owner().call()
        except Exception as e:
            raise ContractCallError(
                f"Invalid vault address or vault does not exist: {vault_address}. "
                f"Error: {str(e)}"
            )
        
        # Check if there are any rewards to claim
        try:
            rewards = self.get_convex_vault_rewards(vault_address)
            total_rewards = sum(rewards['amounts'].values())
            if total_rewards == 0:
                logger.warning("No rewards available to claim.")
        except Exception:
            # Continue anyway - the transaction will fail if there are no rewards
            pass
        
        if token_list:
            # Claim specific tokens
            token_list_checksum = [utils.to_checksum_address(t) for t in token_list]
            return self._build_and_send_transaction(
                vault.functions.getReward(claim, token_list_checksum)
            )
        elif claim:
            # Claim all rewards
            return self._build_and_send_transaction(
                vault.functions.getReward(claim)
            )
        else:
            # Just getReward() - claims all
            return self._build_and_send_transaction(
                vault.functions.getReward()
            )

    def get_convex_vault_info(self, vault_address: str) -> Dict[str, Any]:
        """
        Get information about a Convex vault.
        
        Args:
            vault_address: User's vault address (user-specific)
        
        Returns:
            Dictionary with vault information:
            - owner: Vault owner address
            - pid: Pool ID
            - staking_token: Staking token address
            - gauge_address: Gauge address
            - rewards: Rewards contract address
        
        Raises:
            ContractCallError: If the vault address is invalid or the call fails
        """
        # Validate vault address first
        if not self.w3.is_address(vault_address):
            raise ContractCallError(f"Invalid vault address: {vault_address}")
        
        vault_address = utils.to_checksum_address(vault_address)
        
        vault = self._get_contract("convex_vault", vault_address)
        
        try:
            return {
                "owner": vault.functions.owner().call(),
                "pid": vault.functions.pid().call(),
                "staking_token": vault.functions.stakingToken().call(),
                "gauge_address": vault.functions.gaugeAddress().call(),
                "rewards": vault.functions.rewards().call(),
            }
        except Exception as e:
            raise ContractCallError(
                f"Failed to get vault info. The vault address may be invalid or the vault "
                f"does not exist: {vault_address}. Error: {str(e)}"
            )

    def get_convex_vault_address_from_tx(self, tx_hash: str) -> Optional[str]:
        """
        Extract vault address from a createVault transaction.
        
        This method attempts to extract the vault address from the transaction receipt
        by looking for contract creation events and AddUserVault events.
        
        Args:
            tx_hash: Transaction hash from create_convex_vault()
        
        Returns:
            Vault address if found, None otherwise
        
        Note: If automatic extraction fails, users can query their vault address
        using get_convex_vault_address() with their wallet address and pool_id.
        """
        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            
            # Method 1: Check if there's a contract creation in the receipt
            # (only works for top-level contract creations, not internal ones)
            if receipt.get('contractAddress'):
                # This is a top-level contract creation, not our case
                # But we'll check if it's the vault anyway
                try:
                    vault = self._get_contract("convex_vault", receipt['contractAddress'])
                    # Verify it's a valid vault by checking it has the expected functions
                    vault.functions.owner().call()
                    vault.functions.pid().call()
                    return utils.to_checksum_address(receipt['contractAddress'])
                except Exception:
                    pass
            
            # Method 2: Look for AddUserVault event in the transaction receipt
            # The event is emitted by the registry contract
            registry = self._get_contract("convex_vault_factory", constants.CONVEX_VAULT_REGISTRY)
            
            try:
                # Parse events from the receipt
                events = registry.events.AddUserVault.get_logs(
                    fromBlock=receipt['blockNumber'],
                    toBlock=receipt['blockNumber']
                )
                
                # Filter events from this specific transaction
                tx_events = [e for e in events if e['transactionHash'].hex() == tx_hash]
                
                if tx_events:
                    # The vault address should be the address where the event was emitted
                    # or we can look for contract creation in the logs
                    # Actually, the vault address is the contract that was created
                    # Look for logs from a new contract (address not in the original transaction)
                    
                    # Get the transaction to see the 'to' address (factory)
                    tx = self.w3.eth.get_transaction(tx_hash)
                    factory_address = tx['to']
                    
                    # Look through logs to find a log from a new contract address
                    # that's not the factory or registry
                    known_addresses = {
                        utils.to_checksum_address(factory_address),
                        utils.to_checksum_address(constants.CONVEX_VAULT_FACTORY),
                        utils.to_checksum_address(constants.CONVEX_VAULT_REGISTRY)
                    }
                    
                    for log in receipt.get('logs', []):
                        log_address = utils.to_checksum_address(log['address'])
                        if log_address not in known_addresses:
                            # This might be the vault address
                            # Verify it's a valid vault
                            try:
                                vault = self._get_contract("convex_vault", log_address)
                                owner = vault.functions.owner().call()
                                pid = vault.functions.pid().call()
                                
                                # Check if the owner matches the user from the event
                                event = tx_events[0]
                                event_user = event['args']['user']
                                event_pool_id = event['args']['poolid']
                                
                                if owner.lower() == event_user.lower() and pid == event_pool_id:
                                    return log_address
                            except Exception:
                                # Not a valid vault, continue
                                continue
                
            except Exception as e:
                logger.debug(f"Error parsing events from receipt: {e}")
            
            # Method 3: Query the vault address using the event's user and pool_id
            # This is a fallback if we couldn't extract from logs directly
            try:
                events = registry.events.AddUserVault.get_logs(
                    fromBlock=receipt['blockNumber'],
                    toBlock=receipt['blockNumber']
                )
                tx_events = [e for e in events if e['transactionHash'].hex() == tx_hash]
                
                if tx_events:
                    event = tx_events[0]
                    user = event['args']['user']
                    pool_id = event['args']['poolid']
                    
                    # Query the vault address using get_convex_vault_address
                    # This queries events from the registry to find the vault
                    vault_address = self.get_convex_vault_address(
                        user_address=user,
                        pool_id=pool_id,
                        from_block=receipt['blockNumber']
                    )
                    
                    if vault_address:
                        logger.debug(
                            f"Successfully queried vault address for user {user}, pool {pool_id}: {vault_address}"
                        )
                        return vault_address
                    else:
                        logger.debug(
                            f"Found AddUserVault event for user {user}, pool {pool_id}, "
                            f"but could not query vault address. "
                            f"Please use get_convex_vault_address(user='{user}', pool_id={pool_id}) "
                            f"to query the vault address."
                        )
            except Exception as e:
                logger.debug(f"Error in fallback vault address extraction: {e}")
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract vault address from transaction: {e}")
            return None

    # --- cvxFXN Staking Methods ---

    def deposit_fxn_to_cvxfxn(
        self,
        amount: Union[int, float, Decimal, str],
        recipient: Optional[str] = None
    ) -> str:
        """
        Deposit FXN to receive cvxFXN.
        
        Args:
            amount: Amount of FXN to deposit
            recipient: Optional recipient address (defaults to client's address)
        
        Returns:
            Transaction hash
        
        Raises:
            FXProtocolError: If private key is not available
        """
        if not self.account:
            raise FXProtocolError("Private key required to deposit FXN.")
        
        deposit_contract = self._get_contract("cvxfxn_deposit", constants.CVXFXN_DEPOSIT)
        raw_amount = utils.decimal_to_wei(amount, 18)  # FXN has 18 decimals
        
        recipient_address = recipient or self.address
        if not recipient_address:
            raise FXProtocolError("No recipient address provided or available in client.")
        
        # First, ensure FXN is approved
        fxn_contract = self._get_contract("erc20", constants.FXN)
        current_allowance = fxn_contract.functions.allowance(
            utils.to_checksum_address(recipient_address),
            utils.to_checksum_address(constants.CVXFXN_DEPOSIT)
        ).call()
        
        if current_allowance < raw_amount:
            # Approve FXN spending
            approve_tx = self._build_and_send_transaction(
                fxn_contract.functions.approve(
                    utils.to_checksum_address(constants.CVXFXN_DEPOSIT),
                    raw_amount
                )
            )
            logger.info(f"FXN approval transaction: {approve_tx}")
        
        if recipient:
            return self._build_and_send_transaction(
                deposit_contract.functions.deposit(raw_amount, utils.to_checksum_address(recipient))
            )
        else:
            return self._build_and_send_transaction(
                deposit_contract.functions.deposit(raw_amount)
            )

    def get_cvxfxn_balance(self, account_address: Optional[str] = None) -> Decimal:
        """
        Get cvxFXN token balance for an account.
        
        Args:
            account_address: Optional account address (defaults to client's address)
        
        Returns:
            cvxFXN balance
        """
        return self.get_token_balance(constants.CVXFXN_TOKEN, account_address)

    def stake_cvxfxn(self, amount: Union[int, float, Decimal, str]) -> str:
        """
        Stake cvxFXN tokens.
        
        Args:
            amount: Amount of cvxFXN to stake
        
        Returns:
            Transaction hash
        
        Raises:
            FXProtocolError: If private key is not available
        """
        if not self.account:
            raise FXProtocolError("Private key required to stake cvxFXN.")
        
        if not self.address:
            raise FXProtocolError("No address available in client.")
        
        stake_contract = self._get_contract("cvxfxn_stake", constants.CVXFXN_STAKE)
        raw_amount = utils.decimal_to_wei(amount, 18)  # cvxFXN has 18 decimals
        
        # First, ensure cvxFXN is approved
        cvxfxn_contract = self._get_contract("erc20", constants.CVXFXN_TOKEN)
        current_allowance = cvxfxn_contract.functions.allowance(
            utils.to_checksum_address(self.address),
            utils.to_checksum_address(constants.CVXFXN_STAKE)
        ).call()
        
        if current_allowance < raw_amount:
            # Approve cvxFXN spending
            approve_tx = self._build_and_send_transaction(
                cvxfxn_contract.functions.approve(
                    utils.to_checksum_address(constants.CVXFXN_STAKE),
                    raw_amount
                )
            )
            logger.info(f"cvxFXN approval transaction: {approve_tx}")
        
        return self._build_and_send_transaction(
            stake_contract.functions.stake(raw_amount)
        )

    def get_staked_cvxfxn_balance(self, account_address: Optional[str] = None) -> Decimal:
        """
        Get staked cvxFXN balance for an account.
        
        Args:
            account_address: Optional account address (defaults to client's address)
        
        Returns:
            Staked cvxFXN balance
        """
        target_address = account_address or self.address
        if not target_address:
            raise FXProtocolError("No account address provided or available in client.")
        
        stake_contract = self._get_contract("cvxfxn_stake", constants.CVXFXN_STAKE)
        
        try:
            raw_balance = stake_contract.functions.balanceOf(
                utils.to_checksum_address(target_address)
            ).call()
            return utils.wei_to_decimal(raw_balance, 18)
        except Exception as e:
            raise ContractCallError(f"Failed to get staked cvxFXN balance: {str(e)}")

    def unstake_cvxfxn(self, amount: Union[int, float, Decimal, str]) -> str:
        """
        Unstake cvxFXN tokens.
        
        Args:
            amount: Amount of cvxFXN to unstake
        
        Returns:
            Transaction hash
        """
        stake_contract = self._get_contract("cvxfxn_stake", constants.CVXFXN_STAKE)
        raw_amount = utils.decimal_to_wei(amount, 18)
        
        return self._build_and_send_transaction(
            stake_contract.functions.withdraw(raw_amount)
        )

    def get_cvxfxn_staking_rewards(self, account_address: Optional[str] = None) -> Decimal:
        """
        Get claimable rewards for staked cvxFXN.
        
        Args:
            account_address: Optional account address (defaults to client's address)
        
        Returns:
            Claimable reward amount
        """
        target_address = account_address or self.address
        if not target_address:
            raise FXProtocolError("No account address provided or available in client.")
        
        stake_contract = self._get_contract("cvxfxn_stake", constants.CVXFXN_STAKE)
        
        try:
            raw_rewards = stake_contract.functions.earned(
                utils.to_checksum_address(target_address)
            ).call()
            return utils.wei_to_decimal(raw_rewards, 18)
        except Exception as e:
            raise ContractCallError(f"Failed to get cvxFXN staking rewards: {str(e)}")

    def claim_cvxfxn_staking_rewards(self) -> str:
        """
        Claim rewards from staked cvxFXN.
        
        Returns:
            Transaction hash
        """
        stake_contract = self._get_contract("cvxfxn_stake", constants.CVXFXN_STAKE)
        
        return self._build_and_send_transaction(
            stake_contract.functions.getReward()
        )

    def get_cvxfxn_staking_info(self) -> Dict[str, Any]:
        """
        Get information about cvxFXN staking contract.
        
        Returns:
            Dictionary with:
            - staking_token: cvxFXN token address
            - rewards_token: Reward token address
            - reward_rate: Current reward rate
            - period_finish: When the current reward period ends
        """
        stake_contract = self._get_contract("cvxfxn_stake", constants.CVXFXN_STAKE)
        
        try:
            return {
                "staking_token": stake_contract.functions.stakingToken().call(),
                "rewards_token": stake_contract.functions.rewardsToken().call(),
                "reward_rate": utils.wei_to_decimal(stake_contract.functions.rewardRate().call(), 18),
                "period_finish": stake_contract.functions.periodFinish().call(),
            }
        except Exception as e:
            raise ContractCallError(f"Failed to get cvxFXN staking info: {str(e)}")
    
    # --- Convex Helper Methods ---
    
    def get_all_user_vaults(
        self,
        user_address: Optional[str] = None,
        from_block: int = 0
    ) -> Dict[int, Optional[str]]:
        """
        Get all Convex vault addresses for a user across all known pools.
        
        This method queries all pools in the CONVEX_POOLS registry to find
        vault addresses for the specified user.
        
        Args:
            user_address: User's wallet address (defaults to client's address)
            from_block: Block number to start searching from (0 = from genesis)
        
        Returns:
            Dictionary mapping pool_id to vault_address (None if vault doesn't exist)
        
        Example:
            vaults = client.get_all_user_vaults()
            # Returns: {37: "0x...", 36: "0x...", 0: None, ...}
        """
        target_address = user_address or self.address
        if not target_address:
            raise FXProtocolError("No user address provided or available in client.")
        
        vaults = {}
        
        # Query all pools in the registry
        for pool_key, pool_info in constants.CONVEX_POOLS.items():
            pool_id = pool_info["pool_id"]
            try:
                vault_address = self.get_convex_vault_address(
                    target_address,
                    pool_id,
                    from_block
                )
                vaults[pool_id] = vault_address
            except Exception as e:
                logger.debug(f"Error querying vault for pool {pool_id}: {e}")
                vaults[pool_id] = None
        
        return vaults
    
    def get_convex_pool_info(self, pool_id: Optional[int] = None, pool_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about a Convex pool from the registry.
        
        Args:
            pool_id: Convex pool ID (e.g., 37)
            pool_key: Pool key from CONVEX_POOLS (e.g., "fxusd_stability_fxn")
        
        Returns:
            Dictionary with pool information:
            - pool_id: Pool ID
            - name: Pool name
            - staked_token: Staking token address
            - base_token: Base token address (if applicable)
            - redeems_to: Asset this pool redeems to
            - earns: Rewards this pool earns
            - fx_gauge: f(x) Protocol gauge address
            - stability_pool: Stability pool address (if applicable)
            - convex_url: Convex Finance URL for this pool
        
        Raises:
            FXProtocolError: If pool_id or pool_key not found
        
        Example:
            # By pool ID
            pool_info = client.get_convex_pool_info(pool_id=37)
            
            # By pool key
            pool_info = client.get_convex_pool_info(pool_key="fxusd_stability_fxn")
        """
        if pool_id is not None:
            # Find pool by ID
            for pool_key_iter, pool_info in constants.CONVEX_POOLS.items():
                if pool_info["pool_id"] == pool_id:
                    result = pool_info.copy()
                    result["pool_key"] = pool_key_iter
                    return result
            raise FXProtocolError(f"Pool ID {pool_id} not found in CONVEX_POOLS registry.")
        
        elif pool_key is not None:
            # Find pool by key
            if pool_key in constants.CONVEX_POOLS:
                result = constants.CONVEX_POOLS[pool_key].copy()
                result["pool_key"] = pool_key
                return result
            raise FXProtocolError(f"Pool key '{pool_key}' not found in CONVEX_POOLS registry.")
        
        else:
            raise FXProtocolError("Either pool_id or pool_key must be provided.")
    
    def get_all_convex_pools(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all Convex pools in the registry.
        
        Returns:
            Dictionary mapping pool keys to pool information dictionaries
        
        Example:
            all_pools = client.get_all_convex_pools()
            for pool_key, pool_info in all_pools.items():
                print(f"{pool_info['name']}: Pool ID {pool_info['pool_id']}")
        """
        result = {}
        for pool_key, pool_info in constants.CONVEX_POOLS.items():
            result[pool_key] = pool_info.copy()
            result[pool_key]["pool_key"] = pool_key
        return result
    
    def get_vault_balances_batch(
        self,
        vault_addresses: List[str]
    ) -> Dict[str, Decimal]:
        """
        Get balances for multiple vaults in a single batch query.
        
        Args:
            vault_addresses: List of vault addresses to query
        
        Returns:
            Dictionary mapping vault_address to balance
        
        Example:
            vaults = ["0x...", "0x...", "0x..."]
            balances = client.get_vault_balances_batch(vaults)
            # Returns: {"0x...": Decimal("100"), "0x...": Decimal("50"), ...}
        """
        balances = {}
        for vault_address in vault_addresses:
            try:
                balance = self.get_convex_vault_balance(vault_address)
                balances[vault_address] = balance
            except Exception as e:
                logger.warning(f"Failed to get balance for vault {vault_address}: {e}")
                balances[vault_address] = Decimal("0")
        return balances
    
    def get_vault_rewards_batch(
        self,
        vault_addresses: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get rewards for multiple vaults in a single batch query.
        
        Args:
            vault_addresses: List of vault addresses to query
        
        Returns:
            Dictionary mapping vault_address to rewards dictionary
        
        Example:
            vaults = ["0x...", "0x...", "0x..."]
            rewards = client.get_vault_rewards_batch(vaults)
            # Returns: {
            #   "0x...": {"token_addresses": [...], "amounts": {...}},
            #   ...
            # }
        """
        rewards = {}
        for vault_address in vault_addresses:
            try:
                vault_rewards = self.get_convex_vault_rewards(vault_address)
                rewards[vault_address] = vault_rewards
            except Exception as e:
                logger.warning(f"Failed to get rewards for vault {vault_address}: {e}")
                rewards[vault_address] = {"token_addresses": [], "amounts": {}}
        return rewards
    
    def get_user_vaults_summary(
        self,
        user_address: Optional[str] = None,
        from_block: int = 0
    ) -> Dict[str, Any]:
        """
        Get a comprehensive summary of all user's Convex vaults including balances and rewards.
        
        Args:
            user_address: User's wallet address (defaults to client's address)
            from_block: Block number to start searching from (0 = from genesis)
        
        Returns:
            Dictionary with:
            - user_address: User's wallet address
            - total_vaults: Number of vaults found
            - vaults: Dictionary mapping pool_id to vault information
                - vault_address: Vault address (None if not found)
                - pool_info: Pool information
                - balance: Staked balance (if vault exists)
                - rewards: Claimable rewards (if vault exists)
        
        Example:
            summary = client.get_user_vaults_summary()
            print(f"User has {summary['total_vaults']} vaults")
            for pool_id, vault_data in summary['vaults'].items():
                if vault_data['vault_address']:
                    print(f"Pool {pool_id}: {vault_data['balance']} staked")
        """
        target_address = user_address or self.address
        if not target_address:
            raise FXProtocolError("No user address provided or available in client.")
        
        # Get all vault addresses
        vault_addresses = self.get_all_user_vaults(target_address, from_block)
        
        # Build summary
        summary = {
            "user_address": target_address,
            "total_vaults": sum(1 for addr in vault_addresses.values() if addr is not None),
            "vaults": {}
        }
        
        # Get detailed information for each vault
        for pool_id, vault_address in vault_addresses.items():
            vault_data = {
                "vault_address": vault_address,
                "pool_info": None,
                "balance": None,
                "rewards": None
            }
            
            # Get pool info
            try:
                vault_data["pool_info"] = self.get_convex_pool_info(pool_id=pool_id)
            except Exception as e:
                logger.debug(f"Error getting pool info for pool {pool_id}: {e}")
            
            # Get balance and rewards if vault exists
            if vault_address:
                try:
                    vault_data["balance"] = self.get_convex_vault_balance(vault_address)
                    vault_data["rewards"] = self.get_convex_vault_rewards(vault_address)
                except Exception as e:
                    logger.debug(f"Error getting vault data for {vault_address}: {e}")
            
            summary["vaults"][pool_id] = vault_data
        
        return summary
    
    # --- APY Calculation Methods ---
    
    def get_convex_pool_apy(
        self,
        pool_id: int,
        reward_token_price: Optional[Decimal] = None,
        staking_token_price: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Calculate APY for a Convex pool.
        
        This method calculates APY based on the current reward rate and total staked amount.
        If token prices are provided, it also calculates USD-denominated APY.
        
        Args:
            pool_id: Convex pool ID
            reward_token_price: Optional reward token price in USD (for USD APY calculation)
            staking_token_price: Optional staking token price in USD (for USD APY calculation)
        
        Returns:
            Dictionary with:
            - apy: APY as percentage (e.g., 15.5 for 15.5%)
            - reward_rate: Reward rate per second
            - total_staked: Total staked amount
            - reward_token: Reward token address
            - staking_token: Staking token address
            - usd_apy: USD-denominated APY (if prices provided)
            - period_finish: When current reward period ends
            - is_active: Whether rewards are currently active (period_finish > current_time)
        
        Note: This calculates simple APR (Annual Percentage Rate) based on current reward rate.
        Actual APY may vary based on reward claiming frequency, compounding, and token price changes.
        For true APY with compounding, additional data about compounding frequency is needed.
        """
        # Get pool info for reference
        try:
            pool_info = self.get_convex_pool_info(pool_id=pool_id)
        except Exception:
            pool_info = None
        
        # Get reward data from the Convex Booster contract
        try:
            booster = self._get_contract("convex_booster", constants.CONVEX_BOOSTER)
            # poolInfo returns: [lptoken, token, gauge, crvRewards, stash, shutdown]
            pool_info_data = booster.functions.poolInfo(pool_id).call()
            base_reward_pool_address = pool_info_data[3]  # crvRewards is the BaseRewardPool
            
            if base_reward_pool_address == "0x0000000000000000000000000000000000000000":
                raise ContractCallError(f"Pool {pool_id} does not have a reward pool configured.")
            
            reward_pool = self._get_contract("convex_base_reward_pool", base_reward_pool_address)
            
            # Get reward data
            reward_rate = reward_pool.functions.rewardRate().call()
            total_staked = reward_pool.functions.totalSupply().call()
            period_finish = reward_pool.functions.periodFinish().call()
            reward_token = reward_pool.functions.rewardToken().call()
            staking_token = reward_pool.functions.stakingToken().call()
            
            # Get current block timestamp to check if rewards are active
            current_block = self.w3.eth.get_block('latest')
            current_time = current_block['timestamp']
            is_active = period_finish > current_time
            
            # Get decimals
            reward_token_contract = self._get_contract("erc20", reward_token)
            staking_token_contract = self._get_contract("erc20", staking_token)
            
            reward_decimals = reward_token_contract.functions.decimals().call()
            staking_decimals = staking_token_contract.functions.decimals().call()
            
            # Convert to Decimal
            reward_rate_decimal = utils.wei_to_decimal(reward_rate, reward_decimals)
            total_staked_decimal = utils.wei_to_decimal(total_staked, staking_decimals)
            
            # Calculate APY
            # APR = (reward_rate * seconds_per_year) / total_staked * 100
            # Note: This is APR, not true APY (which accounts for compounding)
            seconds_per_year = Decimal("31536000")  # 365 * 24 * 60 * 60
            
            if total_staked_decimal > 0 and is_active:
                # Simple APR calculation
                apy = (reward_rate_decimal * seconds_per_year / total_staked_decimal) * Decimal("100")
            else:
                apy = Decimal("0")
            
            result = {
                "apy": float(apy),
                "reward_rate": float(reward_rate_decimal),
                "total_staked": float(total_staked_decimal),
                "reward_token": reward_token,
                "staking_token": staking_token,
                "period_finish": period_finish,
                "is_active": is_active,
                "usd_apy": None,
                "pool_id": pool_id
            }
            
            # Add pool info if available
            if pool_info:
                result["pool_name"] = pool_info.get("name")
                result["pool_key"] = pool_info.get("pool_key")
            
            # Calculate USD APY if prices provided
            if reward_token_price is not None and staking_token_price is not None:
                # USD APY = (reward_rate * seconds_per_year * reward_price) / (total_staked * staking_price) * 100
                if total_staked_decimal > 0 and staking_token_price > 0 and is_active:
                    usd_apy = (
                        (reward_rate_decimal * seconds_per_year * reward_token_price) /
                        (total_staked_decimal * staking_token_price)
                    ) * Decimal("100")
                    result["usd_apy"] = float(usd_apy)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to calculate APY for pool {pool_id}: {e}")
            raise ContractCallError(f"Failed to calculate APY: {str(e)}")
    
    def get_convex_vault_apy(
        self,
        vault_address: str,
        reward_token_price: Optional[Decimal] = None,
        staking_token_price: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Calculate APY for a specific Convex vault.
        
        This method uses the vault's rewards contract to calculate APY.
        
        Args:
            vault_address: User's vault address
            reward_token_price: Optional reward token price in USD
            staking_token_price: Optional staking token price in USD
        
        Returns:
            Dictionary with APY information (same format as get_convex_pool_apy)
        
        Note: This calculates simple APR (Annual Percentage Rate) based on current reward rate.
        Actual APY may vary based on reward claiming frequency, compounding, and token price changes.
        """
        vault_address = utils.to_checksum_address(vault_address)
        
        # Validate vault address
        if not self.w3.is_address(vault_address):
            raise ContractCallError(f"Invalid vault address: {vault_address}")
        
        vault = self._get_contract("convex_vault", vault_address)
        
        try:
            # Get pool ID and rewards contract from vault
            pool_id = vault.functions.pid().call()
            rewards_contract_address = vault.functions.rewards().call()
            
            # Use the rewards contract (BaseRewardPool) to get APY data
            reward_pool = self._get_contract("convex_base_reward_pool", rewards_contract_address)
            
            # Get reward data
            reward_rate = reward_pool.functions.rewardRate().call()
            total_staked = reward_pool.functions.totalSupply().call()
            period_finish = reward_pool.functions.periodFinish().call()
            reward_token = reward_pool.functions.rewardToken().call()
            staking_token = reward_pool.functions.stakingToken().call()
            
            # Get current block timestamp to check if rewards are active
            current_block = self.w3.eth.get_block('latest')
            current_time = current_block['timestamp']
            is_active = period_finish > current_time
            
            # Get decimals
            reward_token_contract = self._get_contract("erc20", reward_token)
            staking_token_contract = self._get_contract("erc20", staking_token)
            
            reward_decimals = reward_token_contract.functions.decimals().call()
            staking_decimals = staking_token_contract.functions.decimals().call()
            
            # Convert to Decimal
            reward_rate_decimal = utils.wei_to_decimal(reward_rate, reward_decimals)
            total_staked_decimal = utils.wei_to_decimal(total_staked, staking_decimals)
            
            # Calculate APY
            seconds_per_year = Decimal("31536000")
            
            if total_staked_decimal > 0 and is_active:
                apy = (reward_rate_decimal * seconds_per_year / total_staked_decimal) * Decimal("100")
            else:
                apy = Decimal("0")
            
            result = {
                "apy": float(apy),
                "reward_rate": float(reward_rate_decimal),
                "total_staked": float(total_staked_decimal),
                "reward_token": reward_token,
                "staking_token": staking_token,
                "pool_id": pool_id,
                "period_finish": period_finish,
                "is_active": is_active,
                "usd_apy": None,
                "vault_address": vault_address
            }
            
            # Get pool info if available
            try:
                pool_info = self.get_convex_pool_info(pool_id=pool_id)
                result["pool_name"] = pool_info.get("name")
                result["pool_key"] = pool_info.get("pool_key")
            except Exception:
                pass
            
            # Calculate USD APY if prices provided
            if reward_token_price is not None and staking_token_price is not None:
                if total_staked_decimal > 0 and staking_token_price > 0 and is_active:
                    usd_apy = (
                        (reward_rate_decimal * seconds_per_year * reward_token_price) /
                        (total_staked_decimal * staking_token_price)
                    ) * Decimal("100")
                    result["usd_apy"] = float(usd_apy)
            
            return result
            
        except Exception as e:
            raise ContractCallError(f"Failed to calculate vault APY: {str(e)}")
    
    def get_all_convex_pools_apy(
        self,
        reward_token_prices: Optional[Dict[str, Decimal]] = None,
        staking_token_prices: Optional[Dict[str, Decimal]] = None
    ) -> Dict[int, Dict[str, Any]]:
        """
        Get APY for all Convex pools in the registry.
        
        Args:
            reward_token_prices: Optional dictionary mapping reward token addresses to USD prices
            staking_token_prices: Optional dictionary mapping staking token addresses to USD prices
        
        Returns:
            Dictionary mapping pool_id to APY information
        
        Example:
            apys = client.get_all_convex_pools_apy()
            for pool_id, apy_data in apys.items():
                print(f"Pool {pool_id}: {apy_data['apy']}% APY")
        """
        apys = {}
        
        for pool_key, pool_info in constants.CONVEX_POOLS.items():
            pool_id = pool_info["pool_id"]
            try:
                reward_price = None
                staking_price = None
                
                # Get prices if provided
                if reward_token_prices:
                    # Try to find reward token price (we'd need to know the reward token)
                    # For now, skip price-based calculation
                    pass
                
                if staking_token_prices and pool_info.get("staked_token"):
                    staking_price = staking_token_prices.get(pool_info["staked_token"])
                
                apy_data = self.get_convex_pool_apy(
                    pool_id=pool_id,
                    reward_token_price=reward_price,
                    staking_token_price=staking_price
                )
                apy_data["pool_key"] = pool_key
                apy_data["pool_name"] = pool_info["name"]
                apys[pool_id] = apy_data
                
            except Exception as e:
                logger.warning(f"Failed to get APY for pool {pool_id}: {e}")
                apys[pool_id] = {
                    "pool_id": pool_id,
                    "pool_key": pool_key,
                    "pool_name": pool_info["name"],
                    "error": str(e)
                }
        
        return apys
    
    # --- Pool Information Queries ---
    
    def get_convex_pool_details(
        self,
        pool_id: int,
        include_tvl: bool = True,
        include_rewards: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive details about a Convex pool including live on-chain data.
        
        This method combines registry information with live contract data to provide
        a complete picture of the pool's current state.
        
        Args:
            pool_id: Convex pool ID
            include_tvl: Whether to include TVL (Total Value Locked) data
            include_rewards: Whether to include reward token information
        
        Returns:
            Dictionary with comprehensive pool information:
            - Registry data: pool_id, name, staked_token, base_token, redeems_to, earns, etc.
            - Live data: TVL, reward tokens, gauge address, BaseRewardPool address
            - Contract addresses: All relevant contract addresses
            - Status: Whether pool is active, shutdown status
        
        Example:
            details = client.get_convex_pool_details(pool_id=37)
            print(f"Pool: {details['name']}")
            print(f"TVL: {details['tvl']} tokens")
            print(f"Reward Tokens: {details['reward_tokens']}")
            print(f"Gauge: {details['gauge_address']}")
        """
        # Get registry info
        try:
            pool_info = self.get_convex_pool_info(pool_id=pool_id)
        except Exception as e:
            raise FXProtocolError(f"Pool {pool_id} not found in registry: {e}")
        
        # Start with registry data
        result = pool_info.copy()
        
        # Get live data from Convex Booster
        try:
            booster = self._get_contract("convex_booster", constants.CONVEX_BOOSTER)
            # poolInfo returns: [lptoken, token, gauge, crvRewards, stash, shutdown]
            pool_info_data = booster.functions.poolInfo(pool_id).call()
            
            result.update({
                "lptoken": pool_info_data[0],
                "token": pool_info_data[1],
                "gauge_address": pool_info_data[2],
                "base_reward_pool": pool_info_data[3],  # crvRewards
                "stash": pool_info_data[4],
                "shutdown": pool_info_data[5]
            })
            
            # Get TVL if requested
            if include_tvl and pool_info_data[3] != "0x0000000000000000000000000000000000000000":
                try:
                    reward_pool = self._get_contract("convex_base_reward_pool", pool_info_data[3])
                    total_staked = reward_pool.functions.totalSupply().call()
                    staking_token = reward_pool.functions.stakingToken().call()
                    
                    # Get decimals
                    staking_token_contract = self._get_contract("erc20", staking_token)
                    staking_decimals = staking_token_contract.functions.decimals().call()
                    
                    result["tvl"] = float(utils.wei_to_decimal(total_staked, staking_decimals))
                    result["tvl_raw"] = total_staked
                except Exception as e:
                    logger.warning(f"Failed to get TVL for pool {pool_id}: {e}")
                    result["tvl"] = None
            
            # Get reward token information if requested
            if include_rewards and pool_info_data[3] != "0x0000000000000000000000000000000000000000":
                try:
                    reward_pool = self._get_contract("convex_base_reward_pool", pool_info_data[3])
                    reward_token = reward_pool.functions.rewardToken().call()
                    reward_rate = reward_pool.functions.rewardRate().call()
                    period_finish = reward_pool.functions.periodFinish().call()
                    
                    # Get reward token decimals
                    reward_token_contract = self._get_contract("erc20", reward_token)
                    reward_decimals = reward_token_contract.functions.decimals().call()
                    
                    # Check if rewards are active
                    current_block = self.w3.eth.get_block('latest')
                    current_time = current_block['timestamp']
                    is_active = period_finish > current_time
                    
                    result.update({
                        "reward_tokens": [reward_token],  # Primary reward token
                        "primary_reward_token": reward_token,
                        "reward_rate": float(utils.wei_to_decimal(reward_rate, reward_decimals)),
                        "reward_period_finish": period_finish,
                        "rewards_active": is_active
                    })
                except Exception as e:
                    logger.warning(f"Failed to get reward info for pool {pool_id}: {e}")
                    result["reward_tokens"] = []
            
        except Exception as e:
            logger.warning(f"Failed to get live data for pool {pool_id}: {e}")
            # Return registry data only if live data fails
            result["live_data_available"] = False
        
        return result
    
    def get_convex_pool_tvl(self, pool_id: int) -> Optional[Decimal]:
        """
        Get Total Value Locked (TVL) for a Convex pool.
        
        Args:
            pool_id: Convex pool ID
        
        Returns:
            TVL as Decimal (total staked amount), or None if unavailable
        
        Example:
            tvl = client.get_convex_pool_tvl(pool_id=37)
            print(f"Pool 37 TVL: {tvl} tokens")
        """
        try:
            booster = self._get_contract("convex_booster", constants.CONVEX_BOOSTER)
            pool_info_data = booster.functions.poolInfo(pool_id).call()
            base_reward_pool_address = pool_info_data[3]
            
            if base_reward_pool_address == "0x0000000000000000000000000000000000000000":
                return None
            
            reward_pool = self._get_contract("convex_base_reward_pool", base_reward_pool_address)
            total_staked = reward_pool.functions.totalSupply().call()
            staking_token = reward_pool.functions.stakingToken().call()
            
            # Get decimals
            staking_token_contract = self._get_contract("erc20", staking_token)
            staking_decimals = staking_token_contract.functions.decimals().call()
            
            return utils.wei_to_decimal(total_staked, staking_decimals)
            
        except Exception as e:
            logger.warning(f"Failed to get TVL for pool {pool_id}: {e}")
            return None
    
    def get_convex_pool_reward_tokens(self, pool_id: int) -> List[str]:
        """
        Get list of reward token addresses for a Convex pool.
        
        Args:
            pool_id: Convex pool ID
        
        Returns:
            List of reward token addresses
        
        Note: This currently returns the primary reward token. Additional reward tokens
        may be available through extra reward contracts (stash).
        """
        try:
            booster = self._get_contract("convex_booster", constants.CONVEX_BOOSTER)
            pool_info_data = booster.functions.poolInfo(pool_id).call()
            base_reward_pool_address = pool_info_data[3]
            
            if base_reward_pool_address == "0x0000000000000000000000000000000000000000":
                return []
            
            reward_pool = self._get_contract("convex_base_reward_pool", base_reward_pool_address)
            reward_token = reward_pool.functions.rewardToken().call()
            
            return [reward_token]
            
        except Exception as e:
            logger.warning(f"Failed to get reward tokens for pool {pool_id}: {e}")
            return []
    
    def get_convex_pool_gauge_address(self, pool_id: int) -> Optional[str]:
        """
        Get the gauge address for a Convex pool.
        
        Args:
            pool_id: Convex pool ID
        
        Returns:
            Gauge address, or None if unavailable
        
        Example:
            gauge = client.get_convex_pool_gauge_address(pool_id=37)
            print(f"Pool 37 Gauge: {gauge}")
        """
        try:
            booster = self._get_contract("convex_booster", constants.CONVEX_BOOSTER)
            pool_info_data = booster.functions.poolInfo(pool_id).call()
            gauge_address = pool_info_data[2]
            
            if gauge_address == "0x0000000000000000000000000000000000000000":
                return None
            
            return utils.to_checksum_address(gauge_address)
            
        except Exception as e:
            logger.warning(f"Failed to get gauge address for pool {pool_id}: {e}")
            return None
    
    def get_all_convex_pools_tvl(self) -> Dict[int, Optional[Decimal]]:
        """
        Get TVL for all Convex pools in the registry.
        
        Returns:
            Dictionary mapping pool_id to TVL (None if unavailable)
        
        Example:
            all_tvls = client.get_all_convex_pools_tvl()
            for pool_id, tvl in all_tvls.items():
                if tvl:
                    print(f"Pool {pool_id}: {tvl} TVL")
        """
        tvls = {}
        
        for pool_key, pool_info in constants.CONVEX_POOLS.items():
            pool_id = pool_info["pool_id"]
            try:
                tvl = self.get_convex_pool_tvl(pool_id)
                tvls[pool_id] = tvl
            except Exception as e:
                logger.debug(f"Error getting TVL for pool {pool_id}: {e}")
                tvls[pool_id] = None
        
        return tvls
    
    def get_convex_pool_statistics(self, pool_id: int) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a Convex pool.
        
        This method combines pool details, TVL, APY, and other metrics.
        
        Args:
            pool_id: Convex pool ID
        
        Returns:
            Dictionary with comprehensive pool statistics:
            - Pool information (from registry)
            - TVL and staking data
            - Reward information
            - APY data
            - Contract addresses
            - Status information
        
        Example:
            stats = client.get_convex_pool_statistics(pool_id=37)
            print(f"Pool: {stats['name']}")
            print(f"TVL: {stats['tvl']} tokens")
            print(f"APY: {stats['apy']}%")
            print(f"Active: {stats['rewards_active']}")
        """
        # Get pool details
        details = self.get_convex_pool_details(pool_id=pool_id, include_tvl=True, include_rewards=True)
        
        # Get APY
        try:
            apy_data = self.get_convex_pool_apy(pool_id=pool_id)
            details.update({
                "apy": apy_data.get("apy"),
                "usd_apy": apy_data.get("usd_apy"),
                "apy_reward_rate": apy_data.get("reward_rate"),
                "apy_total_staked": apy_data.get("total_staked")
            })
        except Exception as e:
            logger.debug(f"Failed to get APY for pool {pool_id}: {e}")
            details["apy"] = None
        
        # Combine all data
        result = details.copy()
        result["statistics_available"] = True
        
        return result
    
    # --- Curve Finance Methods ---
    
    def get_curve_pool_info(self, pool_address: str) -> Dict[str, Any]:
        """
        Get information about a Curve pool.
        
        Args:
            pool_address: Curve pool contract address
        
        Returns:
            Dictionary with pool information:
            - pool_address: Pool address
            - coins: List of coin addresses
            - balances: List of coin balances
            - virtual_price: LP token virtual price
            - lp_token: LP token address
            - A: Amplification parameter
            - fee: Pool fee
        
        Example:
            pool_info = client.get_curve_pool_info("0xE06A65e09Ae18096B99770A809BA175FA05960e2")
            print(f"Coins: {pool_info['coins']}")
            print(f"Balances: {pool_info['balances']}")
        """
        pool_address = utils.to_checksum_address(pool_address)
        
        if not self.w3.is_address(pool_address):
            raise ContractCallError(f"Invalid pool address: {pool_address}")
        
        pool = self._get_contract("curve_pool", pool_address)
        
        try:
            # Get basic pool info
            lp_token = pool.functions.token().call()
            
            # Get coins (for 2-coin pools)
            coins = []
            balances = []
            for i in range(2):  # Most f(x) pools are 2-coin pools
                try:
                    coin = pool.functions.coins(i).call()
                    balance = pool.functions.balances(i).call()
                    coins.append(coin)
                    balances.append(balance)
                except Exception:
                    break
            
            # Get pool parameters
            try:
                virtual_price = pool.functions.get_virtual_price().call()
            except Exception:
                virtual_price = None
            
            try:
                A = pool.functions.A().call()
            except Exception:
                A = None
            
            try:
                fee = pool.functions.fee().call()
            except Exception:
                fee = None
            
            # Get decimals for each coin
            decimals = []
            for coin in coins:
                try:
                    coin_contract = self._get_contract("erc20", coin)
                    dec = coin_contract.functions.decimals().call()
                    decimals.append(dec)
                except Exception:
                    decimals.append(18)  # Default
            
            # Convert balances to Decimal
            balances_decimal = [
                utils.wei_to_decimal(balances[i], decimals[i]) if i < len(decimals) else Decimal("0")
                for i in range(len(balances))
            ]
            
            result = {
                "pool_address": pool_address,
                "coins": coins,
                "balances": balances,
                "balances_decimal": [float(b) for b in balances_decimal],
                "decimals": decimals,
                "lp_token": lp_token,
                "virtual_price": virtual_price,
                "A": A,
                "fee": fee,
            }
            
            # Try to get virtual price as decimal
            if virtual_price:
                try:
                    lp_token_contract = self._get_contract("erc20", lp_token)
                    lp_decimals = lp_token_contract.functions.decimals().call()
                    result["virtual_price_decimal"] = float(utils.wei_to_decimal(virtual_price, lp_decimals))
                except Exception:
                    pass
            
            return result
            
        except Exception as e:
            raise ContractCallError(f"Failed to get pool info: {str(e)}")
    
    def get_curve_pool_balances(self, pool_address: str) -> List[Decimal]:
        """
        Get token balances for a Curve pool.
        
        Args:
            pool_address: Curve pool contract address
        
        Returns:
            List of balances as Decimal values
        
        Example:
            balances = client.get_curve_pool_balances("0xE06A65e09Ae18096B99770A809BA175FA05960e2")
            print(f"Token 0: {balances[0]}, Token 1: {balances[1]}")
        """
        pool_info = self.get_curve_pool_info(pool_address)
        return [Decimal(str(b)) for b in pool_info["balances_decimal"]]
    
    def get_curve_pool_virtual_price(self, pool_address: str) -> Decimal:
        """
        Get virtual price (LP token price) for a Curve pool.
        
        Args:
            pool_address: Curve pool contract address
        
        Returns:
            Virtual price as Decimal
        
        Example:
            vp = client.get_curve_pool_virtual_price("0xE06A65e09Ae18096B99770A809BA175FA05960e2")
            print(f"LP Token Price: {vp}")
        """
        pool_address = utils.to_checksum_address(pool_address)
        
        if not self.w3.is_address(pool_address):
            raise ContractCallError(f"Invalid pool address: {pool_address}")
        
        pool = self._get_contract("curve_pool", pool_address)
        
        try:
            virtual_price = pool.functions.get_virtual_price().call()
            lp_token = pool.functions.token().call()
            
            # Get LP token decimals
            lp_token_contract = self._get_contract("erc20", lp_token)
            lp_decimals = lp_token_contract.functions.decimals().call()
            
            return utils.wei_to_decimal(virtual_price, lp_decimals)
            
        except Exception as e:
            raise ContractCallError(f"Failed to get virtual price: {str(e)}")
    
    def get_curve_swap_rate(
        self,
        pool_address: str,
        token_in: str,
        token_out: str,
        amount_in: Decimal
    ) -> Decimal:
        """
        Calculate the output amount for a swap on Curve.
        
        Args:
            pool_address: Curve pool contract address
            token_in: Input token address
            token_out: Output token address
            amount_in: Input amount
        
        Returns:
            Output amount as Decimal
        
        Example:
            amount_out = client.get_curve_swap_rate(
                pool_address="0xE06A65e09Ae18096B99770A809BA175FA05960e2",
                token_in=constants.ETH,
                token_out=constants.FXN,
                amount_in=Decimal("1.0")
            )
            print(f"1 ETH = {amount_out} FXN")
        """
        pool_address = utils.to_checksum_address(pool_address)
        token_in = utils.to_checksum_address(token_in)
        token_out = utils.to_checksum_address(token_out)
        
        if not all(self.w3.is_address(addr) for addr in [pool_address, token_in, token_out]):
            raise ContractCallError("Invalid address provided")
        
        pool = self._get_contract("curve_pool", pool_address)
        
        try:
            # Find coin indices
            coin_i = None
            coin_j = None
            
            for i in range(2):  # Most pools are 2-coin
                try:
                    coin = pool.functions.coins(i).call()
                    if coin.lower() == token_in.lower():
                        coin_i = i
                    if coin.lower() == token_out.lower():
                        coin_j = i
                except Exception:
                    break
            
            if coin_i is None or coin_j is None:
                raise ContractCallError(f"Token not found in pool. Token in: {token_in}, Token out: {token_out}")
            
            # Get input token decimals
            token_in_contract = self._get_contract("erc20", token_in)
            decimals = token_in_contract.functions.decimals().call()
            
            # Convert amount to Wei
            amount_in_wei = utils.decimal_to_wei(amount_in, decimals)
            
            # Calculate output using get_dy
            amount_out_wei = pool.functions.get_dy(coin_i, coin_j, amount_in_wei).call()
            
            # Get output token decimals
            token_out_contract = self._get_contract("erc20", token_out)
            out_decimals = token_out_contract.functions.decimals().call()
            
            return utils.wei_to_decimal(amount_out_wei, out_decimals)
            
        except Exception as e:
            raise ContractCallError(f"Failed to calculate swap rate: {str(e)}")
    
    def get_curve_pool_from_lp_token(self, lp_token: str) -> Optional[str]:
        """
        Find Curve pool address from LP token address.
        
        Args:
            lp_token: LP token address
        
        Returns:
            Pool address if found, None otherwise
        
        Example:
            pool = client.get_curve_pool_from_lp_token("0xE06A65e09Ae18096B99770A809BA175FA05960e2")
        """
        lp_token = utils.to_checksum_address(lp_token)
        
        if not self.w3.is_address(lp_token):
            raise ContractCallError(f"Invalid LP token address: {lp_token}")
        
        try:
            # Try Meta Registry first (more comprehensive)
            meta_registry = self._get_contract("curve_meta_registry", constants.CURVE_META_REGISTRY)
            pool_address = meta_registry.functions.get_pool_from_lp_token(lp_token).call()
            
            if pool_address != "0x0000000000000000000000000000000000000000":
                return utils.to_checksum_address(pool_address)
        except Exception:
            pass
        
        try:
            # Fallback to main registry
            registry = self._get_contract("curve_registry", constants.CURVE_REGISTRY)
            pool_address = registry.functions.get_pool_from_lp_token(lp_token).call()
            
            if pool_address != "0x0000000000000000000000000000000000000000":
                return utils.to_checksum_address(pool_address)
        except Exception:
            pass
        
        return None
    
    def find_curve_pool(self, token_a: str, token_b: str) -> Optional[str]:
        """
        Find a Curve pool for a token pair.
        
        Args:
            token_a: First token address
            token_b: Second token address
        
        Returns:
            Pool address if found, None otherwise
        
        Example:
            pool = client.find_curve_pool(constants.ETH, constants.FXN)
            if pool:
                print(f"Found pool: {pool}")
        """
        token_a = utils.to_checksum_address(token_a)
        token_b = utils.to_checksum_address(token_b)
        
        if not all(self.w3.is_address(addr) for addr in [token_a, token_b]):
            raise ContractCallError("Invalid token address provided")
        
        try:
            # Try Meta Registry first
            meta_registry = self._get_contract("curve_meta_registry", constants.CURVE_META_REGISTRY)
            pool_address = meta_registry.functions.find_pool_for_coins(token_a, token_b).call()
            
            if pool_address != "0x0000000000000000000000000000000000000000":
                return utils.to_checksum_address(pool_address)
        except Exception:
            pass
        
        try:
            # Fallback to main registry
            registry = self._get_contract("curve_registry", constants.CURVE_REGISTRY)
            pool_address = registry.functions.find_pool_for_coins(token_a, token_b).call()
            
            if pool_address != "0x0000000000000000000000000000000000000000":
                return utils.to_checksum_address(pool_address)
        except Exception:
            pass
        
        return None
    
    # --- Curve Gauge Read Methods ---
    
    def get_curve_gauge_info(self, gauge_address: str) -> Dict[str, Any]:
        """
        Get information about a Curve gauge.
        
        Args:
            gauge_address: Curve gauge contract address
        
        Returns:
            Dictionary with gauge information:
            - gauge_address: Gauge address
            - lp_token: LP token address
            - total_supply: Total staked LP tokens
            - reward_count: Number of reward tokens
            - reward_tokens: List of reward token addresses
            - is_killed: Whether gauge is killed
        
        Example:
            gauge_info = client.get_curve_gauge_info("0xA5250C540914E012E22e623275E290c4dC993D11")
            print(f"LP Token: {gauge_info['lp_token']}")
            print(f"Reward Tokens: {gauge_info['reward_tokens']}")
        """
        gauge_address = utils.to_checksum_address(gauge_address)
        
        if not self.w3.is_address(gauge_address):
            raise ContractCallError(f"Invalid gauge address: {gauge_address}")
        
        gauge = self._get_contract("curve_gauge", gauge_address)
        
        try:
            lp_token = gauge.functions.lp_token().call()
            total_supply = gauge.functions.totalSupply().call()
            reward_count = gauge.functions.reward_count().call()
            is_killed = gauge.functions.is_killed().call()
            
            # Get reward tokens
            reward_tokens = []
            for i in range(reward_count):
                try:
                    token = gauge.functions.reward_tokens(i).call()
                    reward_tokens.append(token)
                except Exception:
                    break
            
            # Get LP token decimals
            lp_token_contract = self._get_contract("erc20", lp_token)
            lp_decimals = lp_token_contract.functions.decimals().call()
            
            result = {
                "gauge_address": gauge_address,
                "lp_token": lp_token,
                "total_supply": total_supply,
                "total_supply_decimal": float(utils.wei_to_decimal(total_supply, lp_decimals)),
                "reward_count": reward_count,
                "reward_tokens": reward_tokens,
                "is_killed": is_killed,
            }
            
            # Get reward data for each token
            reward_data_list = []
            for token in reward_tokens:
                try:
                    data = gauge.functions.reward_data(token).call()
                    reward_data_list.append({
                        "token": token,
                        "distributor": data[1],
                        "period_finish": data[2],
                        "rate": data[3],
                        "last_update": data[4],
                        "integral": data[5],
                    })
                except Exception:
                    pass
            
            result["reward_data"] = reward_data_list
            
            return result
            
        except Exception as e:
            raise ContractCallError(f"Failed to get gauge info: {str(e)}")
    
    def get_curve_gauge_balance(self, gauge_address: str, user_address: Optional[str] = None) -> Decimal:
        """
        Get staked LP token balance in a Curve gauge.
        
        Args:
            gauge_address: Curve gauge contract address
            user_address: User address (defaults to connected wallet)
        
        Returns:
            Staked balance as Decimal
        
        Example:
            balance = client.get_curve_gauge_balance(
                gauge_address="0xA5250C540914E012E22e623275E290c4dC993D11",
                user_address="0x..."
            )
            print(f"Staked: {balance} LP tokens")
        """
        gauge_address = utils.to_checksum_address(gauge_address)
        user_address = utils.to_checksum_address(user_address or self.address)
        
        if not self.w3.is_address(gauge_address):
            raise ContractCallError(f"Invalid gauge address: {gauge_address}")
        if not self.w3.is_address(user_address):
            raise ContractCallError(f"Invalid user address: {user_address}")
        
        gauge = self._get_contract("curve_gauge", gauge_address)
        
        try:
            balance = gauge.functions.balanceOf(user_address).call()
            lp_token = gauge.functions.lp_token().call()
            
            # Get LP token decimals
            lp_token_contract = self._get_contract("erc20", lp_token)
            lp_decimals = lp_token_contract.functions.decimals().call()
            
            return utils.wei_to_decimal(balance, lp_decimals)
            
        except Exception as e:
            raise ContractCallError(f"Failed to get gauge balance: {str(e)}")
    
    def get_curve_gauge_rewards(
        self,
        gauge_address: str,
        user_address: Optional[str] = None,
        reward_token: Optional[str] = None
    ) -> Dict[str, Decimal]:
        """
        Get claimable rewards from a Curve gauge.
        
        Args:
            gauge_address: Curve gauge contract address
            user_address: User address (defaults to connected wallet)
            reward_token: Specific reward token address (optional, returns all if None)
        
        Returns:
            Dictionary mapping reward token addresses to claimable amounts
        
        Example:
            rewards = client.get_curve_gauge_rewards(
                gauge_address="0xA5250C540914E012E22e623275E290c4dC993D11",
                user_address="0x..."
            )
            for token, amount in rewards.items():
                print(f"{token}: {amount}")
        """
        gauge_address = utils.to_checksum_address(gauge_address)
        user_address = utils.to_checksum_address(user_address or self.address)
        
        if not self.w3.is_address(gauge_address):
            raise ContractCallError(f"Invalid gauge address: {gauge_address}")
        if not self.w3.is_address(user_address):
            raise ContractCallError(f"Invalid user address: {user_address}")
        
        gauge = self._get_contract("curve_gauge", gauge_address)
        
        try:
            # Get reward tokens
            reward_count = gauge.functions.reward_count().call()
            reward_tokens = []
            for i in range(reward_count):
                try:
                    token = gauge.functions.reward_tokens(i).call()
                    if reward_token is None or token.lower() == reward_token.lower():
                        reward_tokens.append(token)
                except Exception:
                    break
            
            # Get claimable rewards for each token
            rewards = {}
            for token in reward_tokens:
                try:
                    claimable = gauge.functions.claimable_reward(user_address, token).call()
                    
                    # Get token decimals
                    token_contract = self._get_contract("erc20", token)
                    decimals = token_contract.functions.decimals().call()
                    
                    rewards[token] = utils.wei_to_decimal(claimable, decimals)
                except Exception:
                    rewards[token] = Decimal("0")
            
            return rewards
            
        except Exception as e:
            raise ContractCallError(f"Failed to get gauge rewards: {str(e)}")
    
    def get_curve_gauge_from_pool(self, pool_address: str) -> Optional[str]:
        """
        Find Curve gauge address from pool address.
        
        Args:
            pool_address: Curve pool contract address
        
        Returns:
            Gauge address if found, None otherwise
        
        Example:
            gauge = client.get_curve_gauge_from_pool("0xE06A65e09Ae18096B99770A809BA175FA05960e2")
        """
        pool_address = utils.to_checksum_address(pool_address)
        
        if not self.w3.is_address(pool_address):
            raise ContractCallError(f"Invalid pool address: {pool_address}")
        
        try:
            # Try Meta Registry first
            meta_registry = self._get_contract("curve_meta_registry", constants.CURVE_META_REGISTRY)
            gauge_address = meta_registry.functions.get_gauge(pool_address).call()
            
            if gauge_address != "0x0000000000000000000000000000000000000000":
                return utils.to_checksum_address(gauge_address)
        except Exception:
            pass
        
        try:
            # Fallback to main registry
            registry = self._get_contract("curve_registry", constants.CURVE_REGISTRY)
            gauges = registry.functions.get_gauges(pool_address).call()
            
            # get_gauges returns (gauges, types)
            if gauges and len(gauges) > 0 and gauges[0] != "0x0000000000000000000000000000000000000000":
                return utils.to_checksum_address(gauges[0])
        except Exception:
            pass
        
        return None
    
    # --- Curve Write Methods ---
    
    def curve_swap(
        self,
        pool_address: str,
        token_in: str,
        token_out: str,
        amount_in: Union[int, float, Decimal, str],
        min_amount_out: Optional[Union[int, float, Decimal, str]] = None
    ) -> str:
        """
        Execute a swap on Curve.
        
        Args:
            pool_address: Curve pool contract address
            token_in: Input token address
            token_out: Output token address
            amount_in: Input amount
            min_amount_out: Minimum output amount (optional, for slippage protection)
        
        Returns:
            Transaction hash
        
        Example:
            tx_hash = client.curve_swap(
                pool_address="0xE06A65e09Ae18096B99770A809BA175FA05960e2",
                token_in=constants.ETH,
                token_out=constants.FXN,
                amount_in=Decimal("1.0"),
                min_amount_out=Decimal("0.95")  # 5% slippage tolerance
            )
        """
        if not self.address:
            raise FXProtocolError("Private key required for write operations")
        
        pool_address = utils.to_checksum_address(pool_address)
        token_in = utils.to_checksum_address(token_in)
        token_out = utils.to_checksum_address(token_out)
        
        if not all(self.w3.is_address(addr) for addr in [pool_address, token_in, token_out]):
            raise ContractCallError("Invalid address provided")
        
        pool = self._get_contract("curve_pool", pool_address)
        
        try:
            # Find coin indices
            coin_i = None
            coin_j = None
            
            for i in range(2):  # Most pools are 2-coin
                try:
                    coin = pool.functions.coins(i).call()
                    if coin.lower() == token_in.lower():
                        coin_i = i
                    if coin.lower() == token_out.lower():
                        coin_j = i
                except Exception:
                    break
            
            if coin_i is None or coin_j is None:
                raise ContractCallError(f"Token not found in pool. Token in: {token_in}, Token out: {token_out}")
            
            # Get input token decimals
            token_in_contract = self._get_contract("erc20", token_in)
            decimals = token_in_contract.functions.decimals().call()
            
            # Convert amount to Wei
            amount_in_wei = utils.decimal_to_wei(Decimal(str(amount_in)), decimals)
            
            # Calculate expected output if min_amount_out not provided
            if min_amount_out is None:
                amount_out_wei = pool.functions.get_dy(coin_i, coin_j, amount_in_wei).call()
                # Apply 0.5% slippage tolerance by default
                min_amount_out_wei = int(amount_out_wei * 0.995)
            else:
                token_out_contract = self._get_contract("erc20", token_out)
                out_decimals = token_out_contract.functions.decimals().call()
                min_amount_out_wei = utils.decimal_to_wei(Decimal(str(min_amount_out)), out_decimals)
            
            # Check and approve token if needed
            allowance = token_in_contract.functions.allowance(self.address, pool_address).call()
            if allowance < amount_in_wei:
                approve_tx = self._build_and_send_transaction(
                    token_in_contract.functions.approve(pool_address, amount_in_wei)
                )
                logger.info(f"Approval transaction: {approve_tx}")
                # Wait for approval confirmation
                self.w3.eth.wait_for_transaction_receipt(approve_tx)
            
            # Execute swap
            swap_func = pool.functions.exchange(coin_i, coin_j, amount_in_wei, min_amount_out_wei)
            
            return self._build_and_send_transaction(swap_func)
            
        except Exception as e:
            raise ContractCallError(f"Failed to execute swap: {str(e)}")
    
    def curve_add_liquidity(
        self,
        pool_address: str,
        amounts: List[Union[int, float, Decimal, str]],
        min_lp_tokens: Optional[Union[int, float, Decimal, str]] = None
    ) -> str:
        """
        Add liquidity to a Curve pool.
        
        Args:
            pool_address: Curve pool contract address
            amounts: List of token amounts to deposit (one per coin)
            min_lp_tokens: Minimum LP tokens to receive (optional, for slippage protection)
        
        Returns:
            Transaction hash
        
        Example:
            tx_hash = client.curve_add_liquidity(
                pool_address="0xE06A65e09Ae18096B99770A809BA175FA05960e2",
                amounts=[Decimal("1.0"), Decimal("100.0")],  # 1 ETH, 100 FXN
                min_lp_tokens=Decimal("0.99")  # 1% slippage tolerance
            )
        """
        if not self.address:
            raise FXProtocolError("Private key required for write operations")
        
        pool_address = utils.to_checksum_address(pool_address)
        
        if not self.w3.is_address(pool_address):
            raise ContractCallError(f"Invalid pool address: {pool_address}")
        
        pool = self._get_contract("curve_pool", pool_address)
        
        try:
            # Get pool coins
            coins = []
            decimals = []
            for i in range(len(amounts)):
                try:
                    coin = pool.functions.coins(i).call()
                    coins.append(coin)
                    coin_contract = self._get_contract("erc20", coin)
                    dec = coin_contract.functions.decimals().call()
                    decimals.append(dec)
                except Exception:
                    break
            
            if len(coins) != len(amounts):
                raise ContractCallError(f"Mismatch: {len(coins)} coins in pool, {len(amounts)} amounts provided")
            
            # Convert amounts to Wei
            amounts_wei = [
                utils.decimal_to_wei(Decimal(str(amounts[i])), decimals[i])
                for i in range(len(amounts))
            ]
            
            # Calculate expected LP tokens if min_lp_tokens not provided
            if min_lp_tokens is None:
                try:
                    lp_tokens_wei = pool.functions.calc_token_amount(amounts_wei, True).call()
                    # Apply 0.5% slippage tolerance by default
                    min_lp_tokens_wei = int(lp_tokens_wei * 0.995)
                except Exception:
                    min_lp_tokens_wei = 0
            else:
                lp_token = pool.functions.token().call()
                lp_token_contract = self._get_contract("erc20", lp_token)
                lp_decimals = lp_token_contract.functions.decimals().call()
                min_lp_tokens_wei = utils.decimal_to_wei(Decimal(str(min_lp_tokens)), lp_decimals)
            
            # Check and approve tokens if needed
            for i, coin in enumerate(coins):
                coin_contract = self._get_contract("erc20", coin)
                allowance = coin_contract.functions.allowance(self.address, pool_address).call()
                if allowance < amounts_wei[i]:
                    approve_tx = self._build_and_send_transaction(
                        coin_contract.functions.approve(pool_address, amounts_wei[i])
                    )
                    logger.info(f"Approval transaction for {coin}: {approve_tx}")
                    # Wait for approval confirmation
                    self.w3.eth.wait_for_transaction_receipt(approve_tx)
            
            # Add liquidity
            add_liq_func = pool.functions.add_liquidity(amounts_wei, min_lp_tokens_wei)
            
            return self._build_and_send_transaction(add_liq_func)
            
        except Exception as e:
            raise ContractCallError(f"Failed to add liquidity: {str(e)}")
    
    def curve_remove_liquidity(
        self,
        pool_address: str,
        lp_token_amount: Union[int, float, Decimal, str],
        min_amounts: Optional[List[Union[int, float, Decimal, str]]] = None
    ) -> str:
        """
        Remove liquidity from a Curve pool.
        
        Args:
            pool_address: Curve pool contract address
            lp_token_amount: Amount of LP tokens to burn
            min_amounts: Minimum token amounts to receive (optional, for slippage protection)
        
        Returns:
            Transaction hash
        
        Example:
            tx_hash = client.curve_remove_liquidity(
                pool_address="0xE06A65e09Ae18096B99770A809BA175FA05960e2",
                lp_token_amount=Decimal("10.0"),
                min_amounts=[Decimal("0.9"), Decimal("90.0")]  # 10% slippage tolerance
            )
        """
        if not self.address:
            raise FXProtocolError("Private key required for write operations")
        
        pool_address = utils.to_checksum_address(pool_address)
        
        if not self.w3.is_address(pool_address):
            raise ContractCallError(f"Invalid pool address: {pool_address}")
        
        pool = self._get_contract("curve_pool", pool_address)
        
        try:
            # Get LP token
            lp_token = pool.functions.token().call()
            lp_token_contract = self._get_contract("erc20", lp_token)
            lp_decimals = lp_token_contract.functions.decimals().call()
            
            # Convert LP token amount to Wei
            lp_token_amount_wei = utils.decimal_to_wei(Decimal(str(lp_token_amount)), lp_decimals)
            
            # Get pool coins
            coins = []
            decimals = []
            for i in range(2):  # Most pools are 2-coin
                try:
                    coin = pool.functions.coins(i).call()
                    coins.append(coin)
                    coin_contract = self._get_contract("erc20", coin)
                    dec = coin_contract.functions.decimals().call()
                    decimals.append(dec)
                except Exception:
                    break
            
            # Calculate min amounts if not provided
            if min_amounts is None:
                min_amounts_wei = [0] * len(coins)  # No slippage protection
            else:
                if len(min_amounts) != len(coins):
                    raise ContractCallError(f"Mismatch: {len(coins)} coins in pool, {len(min_amounts)} min amounts provided")
                min_amounts_wei = [
                    utils.decimal_to_wei(Decimal(str(min_amounts[i])), decimals[i])
                    for i in range(len(min_amounts))
                ]
            
            # Check and approve LP token if needed
            allowance = lp_token_contract.functions.allowance(self.address, pool_address).call()
            if allowance < lp_token_amount_wei:
                approve_tx = self._build_and_send_transaction(
                    lp_token_contract.functions.approve(pool_address, lp_token_amount_wei)
                )
                logger.info(f"Approval transaction: {approve_tx}")
                # Wait for approval confirmation
                self.w3.eth.wait_for_transaction_receipt(approve_tx)
            
            # Remove liquidity
            remove_liq_func = pool.functions.remove_liquidity(lp_token_amount_wei, min_amounts_wei)
            
            return self._build_and_send_transaction(remove_liq_func)
            
        except Exception as e:
            raise ContractCallError(f"Failed to remove liquidity: {str(e)}")
    
    def curve_stake_lp_tokens(
        self,
        gauge_address: str,
        lp_token_amount: Union[int, float, Decimal, str],
        claim_rewards: bool = False
    ) -> str:
        """
        Stake LP tokens in a Curve gauge.
        
        Args:
            gauge_address: Curve gauge contract address
            lp_token_amount: Amount of LP tokens to stake
            claim_rewards: Whether to claim rewards when staking
        
        Returns:
            Transaction hash
        
        Example:
            tx_hash = client.curve_stake_lp_tokens(
                gauge_address="0xA5250C540914E012E22e623275E290c4dC993D11",
                lp_token_amount=Decimal("100.0"),
                claim_rewards=True
            )
        """
        if not self.address:
            raise FXProtocolError("Private key required for write operations")
        
        gauge_address = utils.to_checksum_address(gauge_address)
        
        if not self.w3.is_address(gauge_address):
            raise ContractCallError(f"Invalid gauge address: {gauge_address}")
        
        gauge = self._get_contract("curve_gauge", gauge_address)
        
        try:
            # Get LP token
            lp_token = gauge.functions.lp_token().call()
            lp_token_contract = self._get_contract("erc20", lp_token)
            lp_decimals = lp_token_contract.functions.decimals().call()
            
            # Convert amount to Wei
            lp_token_amount_wei = utils.decimal_to_wei(Decimal(str(lp_token_amount)), lp_decimals)
            
            # Check and approve LP token if needed
            allowance = lp_token_contract.functions.allowance(self.address, gauge_address).call()
            if allowance < lp_token_amount_wei:
                approve_tx = self._build_and_send_transaction(
                    lp_token_contract.functions.approve(gauge_address, lp_token_amount_wei)
                )
                logger.info(f"Approval transaction: {approve_tx}")
                # Wait for approval confirmation
                self.w3.eth.wait_for_transaction_receipt(approve_tx)
            
            # Stake LP tokens
            if claim_rewards:
                stake_func = gauge.functions.deposit(lp_token_amount_wei, self.address, True)
            else:
                stake_func = gauge.functions.deposit(lp_token_amount_wei)
            
            return self._build_and_send_transaction(stake_func)
            
        except Exception as e:
            raise ContractCallError(f"Failed to stake LP tokens: {str(e)}")
    
    def curve_unstake_lp_tokens(
        self,
        gauge_address: str,
        lp_token_amount: Union[int, float, Decimal, str],
        claim_rewards: bool = False
    ) -> str:
        """
        Unstake LP tokens from a Curve gauge.
        
        Args:
            gauge_address: Curve gauge contract address
            lp_token_amount: Amount of LP tokens to unstake
            claim_rewards: Whether to claim rewards when unstaking
        
        Returns:
            Transaction hash
        
        Example:
            tx_hash = client.curve_unstake_lp_tokens(
                gauge_address="0xA5250C540914E012E22e623275E290c4dC993D11",
                lp_token_amount=Decimal("50.0"),
                claim_rewards=True
            )
        """
        if not self.address:
            raise FXProtocolError("Private key required for write operations")
        
        gauge_address = utils.to_checksum_address(gauge_address)
        
        if not self.w3.is_address(gauge_address):
            raise ContractCallError(f"Invalid gauge address: {gauge_address}")
        
        gauge = self._get_contract("curve_gauge", gauge_address)
        
        try:
            # Get LP token
            lp_token = gauge.functions.lp_token().call()
            lp_token_contract = self._get_contract("erc20", lp_token)
            lp_decimals = lp_token_contract.functions.decimals().call()
            
            # Convert amount to Wei
            lp_token_amount_wei = utils.decimal_to_wei(Decimal(str(lp_token_amount)), lp_decimals)
            
            # Unstake LP tokens
            if claim_rewards:
                unstake_func = gauge.functions.withdraw(lp_token_amount_wei, True)
            else:
                unstake_func = gauge.functions.withdraw(lp_token_amount_wei)
            
            return self._build_and_send_transaction(unstake_func)
            
        except Exception as e:
            raise ContractCallError(f"Failed to unstake LP tokens: {str(e)}")
    
    def curve_claim_gauge_rewards(
        self,
        gauge_address: str,
        receiver: Optional[str] = None
    ) -> str:
        """
        Claim rewards from a Curve gauge.
        
        Args:
            gauge_address: Curve gauge contract address
            receiver: Address to receive rewards (defaults to connected wallet)
        
        Returns:
            Transaction hash
        
        Example:
            tx_hash = client.curve_claim_gauge_rewards(
                gauge_address="0xA5250C540914E012E22e623275E290c4dC993D11"
            )
        """
        if not self.address:
            raise FXProtocolError("Private key required for write operations")
        
        gauge_address = utils.to_checksum_address(gauge_address)
        receiver = utils.to_checksum_address(receiver or self.address)
        
        if not self.w3.is_address(gauge_address):
            raise ContractCallError(f"Invalid gauge address: {gauge_address}")
        if not self.w3.is_address(receiver):
            raise ContractCallError(f"Invalid receiver address: {receiver}")
        
        gauge = self._get_contract("curve_gauge", gauge_address)
        
        try:
            # Claim rewards
            claim_func = gauge.functions.claim_rewards(receiver, receiver)
            
            return self._build_and_send_transaction(claim_func)
            
        except Exception as e:
            raise ContractCallError(f"Failed to claim gauge rewards: {str(e)}")
    
    # --- Curve Helper Methods ---
    
    def get_curve_pools_from_registry(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all Curve pools from the SDK's registry.
        
        Returns:
            Dictionary mapping pool keys to pool information
        
        Example:
            pools = client.get_curve_pools_from_registry()
            for key, pool in pools.items():
                print(f"{key}: {pool['name']}")
        """
        curve_pools = {}
        for pool_id, pool_data in constants.CONVEX_POOLS.items():
            if pool_data.get("pool_type") == "curve_lp":
                curve_pools[pool_data.get("key", str(pool_id))] = {
                    "pool_id": pool_id,
                    **pool_data
                }
        return curve_pools
    
    def get_curve_pool_from_registry(
        self,
        pool_id: Optional[int] = None,
        pool_key: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get Curve pool information from the SDK's registry.
        
        Args:
            pool_id: Convex pool ID (optional)
            pool_key: Pool key identifier (optional)
        
        Returns:
            Dictionary with pool information if found, None otherwise
        
        Example:
            pool = client.get_curve_pool_from_registry(pool_id=6)  # ETH/FXN pool
            if pool:
                print(f"LP Token: {pool['lp_token']}")
                print(f"Gauge: {pool['fx_gauge']}")
        """
        if pool_id is not None:
            pool_data = constants.CONVEX_POOLS.get(pool_id)
            if pool_data and pool_data.get("pool_type") == "curve_lp":
                return {"pool_id": pool_id, **pool_data}
        elif pool_key is not None:
            for pid, pdata in constants.CONVEX_POOLS.items():
                if pdata.get("key") == pool_key and pdata.get("pool_type") == "curve_lp":
                    return {"pool_id": pid, **pdata}
        return None
    
    def get_curve_gauge_balances_batch(
        self,
        gauge_addresses: List[str],
        user_address: Optional[str] = None
    ) -> Dict[str, Decimal]:
        """
        Get staked balances for multiple Curve gauges in a batch.
        
        Args:
            gauge_addresses: List of gauge addresses
            user_address: User address (defaults to connected wallet)
        
        Returns:
            Dictionary mapping gauge addresses to staked balances
        
        Example:
            gauges = ["0xA5250C540914E012E22e623275E290c4dC993D11", "0x..."]
            balances = client.get_curve_gauge_balances_batch(gauges, user_address="0x...")
            for gauge, balance in balances.items():
                print(f"{gauge}: {balance}")
        """
        user_address = utils.to_checksum_address(user_address or self.address)
        
        if not self.w3.is_address(user_address):
            raise ContractCallError(f"Invalid user address: {user_address}")
        
        balances = {}
        for gauge_address in gauge_addresses:
            try:
                balance = self.get_curve_gauge_balance(gauge_address, user_address)
                balances[gauge_address] = balance
            except Exception as e:
                logger.warning(f"Failed to get balance for gauge {gauge_address}: {e}")
                balances[gauge_address] = Decimal("0")
        
        return balances
    
    def get_curve_gauge_rewards_batch(
        self,
        gauge_addresses: List[str],
        user_address: Optional[str] = None
    ) -> Dict[str, Dict[str, Decimal]]:
        """
        Get claimable rewards for multiple Curve gauges in a batch.
        
        Args:
            gauge_addresses: List of gauge addresses
            user_address: User address (defaults to connected wallet)
        
        Returns:
            Dictionary mapping gauge addresses to reward dictionaries
        
        Example:
            gauges = ["0xA5250C540914E012E22e623275E290c4dC993D11", "0x..."]
            rewards = client.get_curve_gauge_rewards_batch(gauges, user_address="0x...")
            for gauge, gauge_rewards in rewards.items():
                print(f"{gauge}: {gauge_rewards}")
        """
        user_address = utils.to_checksum_address(user_address or self.address)
        
        if not self.w3.is_address(user_address):
            raise ContractCallError(f"Invalid user address: {user_address}")
        
        rewards = {}
        for gauge_address in gauge_addresses:
            try:
                gauge_rewards = self.get_curve_gauge_rewards(gauge_address, user_address)
                rewards[gauge_address] = gauge_rewards
            except Exception as e:
                logger.warning(f"Failed to get rewards for gauge {gauge_address}: {e}")
                rewards[gauge_address] = {}
        
        return rewards
    
    def get_user_curve_positions_summary(
        self,
        user_address: Optional[str] = None,
        include_pool_info: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive summary of user's Curve positions across all f(x) Protocol pools.
        
        Args:
            user_address: User address (defaults to connected wallet)
            include_pool_info: Whether to include pool information (default: True)
        
        Returns:
            Dictionary with summary of all Curve positions:
            - total_gauges: Number of gauges with positions
            - total_staked: Total LP tokens staked across all gauges
            - total_rewards: Total claimable rewards (by token)
            - positions: List of position details
        
        Example:
            summary = client.get_user_curve_positions_summary(user_address="0x...")
            print(f"Total Staked: {summary['total_staked']}")
            print(f"Total Rewards: {summary['total_rewards']}")
            for position in summary['positions']:
                print(f"{position['pool_name']}: {position['staked']} LP tokens")
        """
        user_address = utils.to_checksum_address(user_address or self.address)
        
        if not self.w3.is_address(user_address):
            raise ContractCallError(f"Invalid user address: {user_address}")
        
        # Get all Curve pools from registry
        curve_pools = self.get_curve_pools_from_registry()
        
        positions = []
        total_staked = Decimal("0")
        total_rewards = {}
        
        for pool_key, pool_data in curve_pools.items():
            gauge_address = pool_data.get("fx_gauge")
            if not gauge_address:
                continue
            
            try:
                # Get staked balance
                staked = self.get_curve_gauge_balance(gauge_address, user_address)
                
                if staked > 0:
                    # Get rewards
                    rewards = self.get_curve_gauge_rewards(gauge_address, user_address)
                    
                    # Get pool info if requested
                    pool_info = None
                    if include_pool_info:
                        lp_token = pool_data.get("lp_token")
                        if lp_token:
                            try:
                                pool_address = self.get_curve_pool_from_lp_token(lp_token)
                                if pool_address:
                                    pool_info = self.get_curve_pool_info(pool_address)
                            except Exception:
                                pass
                    
                    position = {
                        "pool_id": pool_data.get("pool_id"),
                        "pool_name": pool_data.get("name", "Unknown"),
                        "pool_key": pool_key,
                        "gauge_address": gauge_address,
                        "lp_token": pool_data.get("lp_token"),
                        "staked": float(staked),
                        "rewards": {token: float(amount) for token, amount in rewards.items()},
                    }
                    
                    if pool_info:
                        position["pool_info"] = pool_info
                    
                    positions.append(position)
                    total_staked += staked
                    
                    # Aggregate rewards
                    for token, amount in rewards.items():
                        if token not in total_rewards:
                            total_rewards[token] = Decimal("0")
                        total_rewards[token] += amount
                        
            except Exception as e:
                logger.warning(f"Failed to get position for pool {pool_key}: {e}")
                continue
        
        return {
            "user_address": user_address,
            "total_gauges": len(positions),
            "total_staked": float(total_staked),
            "total_rewards": {token: float(amount) for token, amount in total_rewards.items()},
            "positions": positions,
        }
    
    def get_curve_gauge_apy(
        self,
        gauge_address: str,
        reward_token_price: Optional[Decimal] = None,
        lp_token_price: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Calculate APY (APR) for a Curve gauge based on current reward rate.
        
        Args:
            gauge_address: Curve gauge contract address
            reward_token_price: Price of reward token in USD (optional, for USD APY)
            lp_token_price: Price of LP token in USD (optional, for USD APY)
        
        Returns:
            Dictionary with APY information:
            - apy: APY as decimal (e.g., 0.05 for 5%)
            - apy_percentage: APY as percentage (e.g., 5.0)
            - usd_apy: USD-denominated APY (if prices provided)
            - reward_rate: Current reward rate per second
            - total_staked: Total LP tokens staked
            - reward_token: Reward token address
            - period_finish: When current reward period ends
        
        Example:
            apy_data = client.get_curve_gauge_apy("0xA5250C540914E012E22e623275E290c4dC993D11")
            print(f"APY: {apy_data['apy_percentage']}%")
            
            # With prices for USD APY
            apy_data = client.get_curve_gauge_apy(
                gauge_address="0xA5250C540914E012E22e623275E290c4dC993D11",
                reward_token_price=Decimal("0.5"),  # CRV price
                lp_token_price=Decimal("1.0")  # LP token price
            )
            print(f"USD APY: {apy_data['usd_apy_percentage']}%")
        """
        gauge_address = utils.to_checksum_address(gauge_address)
        
        if not self.w3.is_address(gauge_address):
            raise ContractCallError(f"Invalid gauge address: {gauge_address}")
        
        gauge = self._get_contract("curve_gauge", gauge_address)
        
        try:
            # Get gauge info
            gauge_info = self.get_curve_gauge_info(gauge_address)
            
            if not gauge_info.get("reward_tokens"):
                return {
                    "apy": Decimal("0"),
                    "apy_percentage": 0.0,
                    "usd_apy": None,
                    "usd_apy_percentage": None,
                    "reward_rate": 0,
                    "total_staked": 0,
                    "reward_token": None,
                    "period_finish": None,
                }
            
            # Use first reward token (typically CRV)
            reward_token = gauge_info["reward_tokens"][0]
            reward_data = next(
                (rd for rd in gauge_info.get("reward_data", []) if rd["token"] == reward_token),
                None
            )
            
            if not reward_data:
                return {
                    "apy": Decimal("0"),
                    "apy_percentage": 0.0,
                    "usd_apy": None,
                    "usd_apy_percentage": None,
                    "reward_rate": 0,
                    "total_staked": gauge_info["total_supply"],
                    "reward_token": reward_token,
                    "period_finish": None,
                }
            
            reward_rate = reward_data["rate"]  # Per second
            total_staked = gauge_info["total_supply"]
            period_finish = reward_data["period_finish"]
            
            # Get reward token decimals
            reward_token_contract = self._get_contract("erc20", reward_token)
            reward_decimals = reward_token_contract.functions.decimals().call()
            
            # Get LP token decimals
            lp_token = gauge_info["lp_token"]
            lp_token_contract = self._get_contract("erc20", lp_token)
            lp_decimals = lp_token_contract.functions.decimals().call()
            
            # Convert to Decimal
            reward_rate_decimal = utils.wei_to_decimal(reward_rate, reward_decimals)
            total_staked_decimal = utils.wei_to_decimal(total_staked, lp_decimals)
            
            # Calculate APY
            if total_staked_decimal > 0:
                # Annual reward = reward_rate * seconds_per_year
                seconds_per_year = Decimal("31536000")  # 365 * 24 * 60 * 60
                annual_reward = reward_rate_decimal * seconds_per_year
                
                # APY = annual_reward / total_staked
                apy = annual_reward / total_staked_decimal
            else:
                apy = Decimal("0")
            
            result = {
                "apy": apy,
                "apy_percentage": float(apy * 100),
                "reward_rate": float(reward_rate_decimal),
                "total_staked": float(total_staked_decimal),
                "reward_token": reward_token,
                "period_finish": period_finish,
            }
            
            # Calculate USD APY if prices provided
            if reward_token_price is not None and lp_token_price is not None:
                if total_staked_decimal > 0:
                    # Annual reward value in USD
                    annual_reward_usd = annual_reward * reward_token_price
                    
                    # Total staked value in USD
                    total_staked_usd = total_staked_decimal * lp_token_price
                    
                    # USD APY
                    usd_apy = annual_reward_usd / total_staked_usd if total_staked_usd > 0 else Decimal("0")
                    
                    result["usd_apy"] = float(usd_apy)
                    result["usd_apy_percentage"] = float(usd_apy * 100)
                else:
                    result["usd_apy"] = None
                    result["usd_apy_percentage"] = None
            else:
                result["usd_apy"] = None
                result["usd_apy_percentage"] = None
            
            return result
            
        except Exception as e:
            raise ContractCallError(f"Failed to calculate gauge APY: {str(e)}")
    
    def get_all_curve_gauges_apy(
        self,
        reward_token_prices: Optional[Dict[str, Decimal]] = None,
        lp_token_prices: Optional[Dict[str, Decimal]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get APY for all Curve gauges in the f(x) Protocol registry.
        
        Args:
            reward_token_prices: Dictionary mapping reward token addresses to USD prices
            lp_token_prices: Dictionary mapping LP token addresses to USD prices
        
        Returns:
            Dictionary mapping gauge addresses to APY data
        
        Example:
            apy_data = client.get_all_curve_gauges_apy()
            for gauge, data in apy_data.items():
                print(f"{gauge}: {data['apy_percentage']}%")
        """
        curve_pools = self.get_curve_pools_from_registry()
        apy_data = {}
        
        for pool_key, pool_data in curve_pools.items():
            gauge_address = pool_data.get("fx_gauge")
            if not gauge_address:
                continue
            
            try:
                # Get prices if provided
                reward_token_price = None
                lp_token_price = None
                
                if reward_token_prices:
                    # Try to find reward token price (typically CRV)
                    gauge_info = self.get_curve_gauge_info(gauge_address)
                    if gauge_info.get("reward_tokens"):
                        reward_token = gauge_info["reward_tokens"][0]
                        reward_token_price = reward_token_prices.get(reward_token)
                
                if lp_token_prices:
                    lp_token = pool_data.get("lp_token")
                    if lp_token:
                        lp_token_price = lp_token_prices.get(lp_token)
                
                apy = self.get_curve_gauge_apy(
                    gauge_address=gauge_address,
                    reward_token_price=reward_token_price,
                    lp_token_price=lp_token_price
                )
                
                apy_data[gauge_address] = {
                    "pool_id": pool_data.get("pool_id"),
                    "pool_name": pool_data.get("name", "Unknown"),
                    "pool_key": pool_key,
                    **apy
                }
                
            except Exception as e:
                logger.warning(f"Failed to get APY for gauge {gauge_address}: {e}")
                continue
        
        return apy_data


