"""
Constants for the f(x) Protocol SDK.
Includes contract addresses, chain IDs, and ABI paths.
"""

# Network configuration
ETHEREUM_MAINNET_CHAIN_ID = 1

# Contract Addresses
# V2 Core Contracts
FXUSD = "0x085780639CC2cACd35E474e71f4d000e2405d8f6"
FXUSD_BASE_POOL = "0x65C9A641afCEB9C0E6034e558A319488FA0FA3be"
PEG_KEEPER = "0x50562fe7e870420F5AAe480B7F94EB4ace2fcd70"
POOL_MANAGER = "0x250893CA4Ba5d05626C785e8da758026928FCD24"
RESERVE_POOL = "0x297dD69725911FE5F08B8F8C5EDdDb724D7D11df"
REVENUE_POOL = "0x361f88157073B8522deF857761484CA7b1D5c8be"
LIQUIDITY_GAUGE = "0xF62F458D2F6dd2AD074E715655064d7632e136D6"
GAUGE_REWARDER = "0x5Ac1A882E6CeDc58511b7e42b02BAB42E2c02956"
FXUSD_BASE_POOL_GAUGE = "0xEd92dDe3214c24Ae04F5f96927E3bE8f8DbC3289"

# V2 Router & Diamond
DIAMOND_ROUTER = "0x33636D49FbefBE798e15e7F356E8DBef543CC708"

# V2 Supporting & Markets
STETH_PRICE_ORACLE = "0x3716352d57C2e48EEdB56Ee0712Ef29E0c2f3069"
MULTI_PATH_CONVERTER = "0x12AF4529129303D7FbD2563E242C4a2890525912"
WSTETH_POOL = "0x6Ecfa38FeE8a5277B91eFdA204c235814F0122E8"
AAVE_FUNDING_POOL = "0x69Ea7311A33f4bFE39949b387d2347fFaC8C70b8"
STETH_GATEWAY = "0x9bF5fFABbF97De0a47843A7Ba0A9DDB40f2e2ed5"

# Savings & Stability Pool
SAVING_FXUSD = "0x7743e50F534a7f9F1791DdE7dCD89F7783Eefc39"
FXSP = "0x65C9A641afCEB9C0E6034e558A319488FA0FA3be"  # Same as Base Pool Proxy

# Vesting Contracts
VESTING_FXN = "0x2290eeFEa24A6E43b26C27187742bD1FEDC10BDB"
VESTING_FETH = "0x1236193C71128f9e7b6BB56F506676adD8589009"
VESTING_FXUSD = "0xc054F64143CB04b765773D5B66992f611C497352"

# V1 Migration
SFRXETH_MARKET = "0x714B853b3bA73E439c652CfE79660F329E6ebB42"
WSTETH_MARKET = "0xAD9A0E7C08bc9F747dF97a3E7E7f620632CB6155"

# V1 Legacy - Tokens
FETH = "0x53805A76E1f5ebbFE7115F16f9c87C2f7e633726"
RUSD = "0x65D72AA8DA931F047169112fcf34f52DbaAE7D18"
ARUSD = "0xC752C6DaA143e1a0ba3E7Df06f3117182432b991"
BTCUSD = "0x9D11ab23d33aD026C466CE3c124928fDb69Ba20E"
CVXUSD = "0x9f0D5E33617A1Db6f1CBd5580834422684f09269"

# V1 Legacy - xTokens
XETH = "0xe063F04f280c60aECa68b38341C2eEcBeC703ae2"
XCVX = "0xB90D347e10a085B591955Cbd0603aC7866fCADC8"
XWBTC = "0x9f23562ec47249761222EF7Ac02b327a8C45Ba7D"
XEETH = "0xACB3604AaDF26e6C0bb8c720420380629A328d2C"  # xeETH
XEZETH = "0x2e5A5AF7eE900D34BCFB70C47023bf1d6bE35CF5"
XSTETH = "0x5a097b014C547718e79030a077A91Ae37679EfF5"
XFRXETH = "0x2bb0C32101456F5960d4e994Bac183Fe0dc6C82c"

# Collateral Assets (Used in V2 Pools)
STETH = "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84"
WSTETH = "0x7f39C581F595B53c5cb19bd0b3f8dA6c935E2Ca0"
FRXETH = "0x5E8422345238F34275888049021821E8E08CAa1f"
SFRXETH = "0xac3e018457b222d93114458476f3e3416abbe38f"

# Liquidity Gauges (Convex Dual Farms)
GAUGES = {
    "ETH_FXN": "0xA5250C540914E012E22e623275E290c4dC993D11",
    "FXN_CVXFXN": "0xfEFafB9446d84A9e58a3A2f2DDDd7219E8c94FbB",
    "FXN_SDFXN": "0x5b1D12365BEc01b8b672eE45912d1bbc86305dba",
    "CRVUSD_FXUSD": "0xF4Bd6D66bAFEA1E0500536d52236f64c3e8a2a84",
    "PYUSD_FXUSD": "0xeD113B925AC3f972161Be012cdFEE33470040E6a",
    "DOLA_FXUSD": "0x61F32964C39Cca4353144A6DB2F8Efdb3216b35B",
    "GRAI_FXUSD": "0xfa4761512aaf899b010438a10C60D01EBdc0eFcA",
    "FRAX_FXUSD": "0x31b630B21065664dDd2dBa0eD3a60D8ff59501F0",
    "GHO_FXUSD": "0xf0A3ECed42Dbd8353569639c0eaa833857aA0A75",
    "MKUSD_FXUSD": "0xDbA9a415bae1983a945ba078150CAe8b690c9229",
    "ULTRA_FXUSD": "0x0d3e9A29E856CF00d670368a7ab0512cb0c29FAC",
    "FXUSD_RUSD": "0x697DDb8e742047561C8e4bB69d2DDB1b8Bb42b60",
    "ALUSD_FXUSD": "0x9c7003bC16F2A1AA47451C858FEe6480B755363e",
    "EUSD_FXUSD": "0x5801Bb8f568979C722176Df36b1a74654A9C52b5",
    "RGUSD_FXUSD": "0x4CA79F4FE25BCD329445CDBE7E065427ACa98380",
    "MIM_FXUSD": "0xDF7fbDBAE50C7931a11765FAEd9fe1A002605B55",
    "ZUNUSD_FXUSD": "0x9516c367952430371A733E5eBb587E01eE082F99",
    "USDC_FXUSD": "0xf1E141C804BA39b4a031fDF46e8c08dBa7a0df60",
    "USD0_FXUSD": "0x0B700C60de435D522081cC5eB12B63875FE7e65a",
    "FXUSD_RUSD_BTCUSD": "0x7a505e920d5d7E4b402D9Ee345fB7E8Cdc265262",
    "FXUSD_USDN": "0xa295829c082C4d21fE37dbC8C96bFa0ef6dbaa92",
    "REUSD_FXUSD": "0x8d9186Fa822624bad50a5cB2545048CB26b4E65E",
    "FXSAVE_SCRVUSD": "0x6FcFe767c479ef1f2d8c7A4b27e2aBaDD355910F",
    "MSUSD_FXUSD": "0x2122a2bee97545595550b85379AC7676Fd21a5B4",
    "FXUSD_USDC_USDAF_BOLD": "0xE534E5e86382d64133ecd6b7f717C69BEC8B40CA",
    "DOLA_FXSAVE": "0x7d4674b837429c44914961cb9F21dD6dEFd0eee0",
    "FXUSD_GAUGE": "0xABc8cBbA768DA396626FAD97D0e61104aC1e7068",
    "YNUSDX_FXUSD": "0xeD9ED685F553B0827a58a918E64eC02E6FD55799",
    "YNRWAX_FXUSD": "0x0BbfD53Ec934e5d4d3d55dD860642aDD395De979",
    "FXUSD_FRXUSD": "0xA3c0f7360b922136cc8B89063BE1e8daF70427bD",
}

# Governance & Utility
FXN = "0x365AccFCa291e7D3914637ABf1F7635dB165Bb09"
VEFXN = "0xEC6B8A3F3605B083F7044C0F31f2cac0caf1d469"
GAUGE_CONTROLLER = "0xe60eB8098B34eD775ac44B1ddE864e098C6d7f37"

# V1 Infrastructure
FRACTIONAL_TOKEN_PROXY = "0x53805A76E1f5ebbFE7115F16f9c87C2f7e633726"
LEVERAGED_TOKEN_PROXY = "0xe063F04f280c60aECa68b38341C2eEcBeC703ae2"
STETH_TREASURY_PROXY = "0x0e5CAA5c889Bdf053c9A76395f62267E653AFbb0"
MARKET_PROXY = "0xe7b9c7c9cA85340b8c06fb805f7775e3015108dB"
REBALANCE_POOL_REGISTRY = "0x4eEfea49e4D876599765d5375cF7314cD14C9d38"
REBALANCE_POOL_IMPLEMENTATION = "0xD670175FD40D517da9f7529BAA11276b7011947C"

# Proxy Admins
FX_PROXY_ADMIN = "0x9B54B7703551D9d0ced177A78367560a8B2eDDA4"
CUSTOM_PROXY_ADMIN = "0xd41d29fc53fE5Ce9f0fB2328E54d35A2a03a324B"

# Curve Finance
CURVE_REGISTRY = "0x90E00ACe148ca3b23Ac1bC8C240C2a7Dd9c2d7f5"
CURVE_META_REGISTRY = "0xF98B45FA17DE75FB1aD0e7aFD971b0ca00e379fC"
CURVE_ADDRESS_PROVIDER = "0x0000000022D53366457F9d5E68Ec105046FC4383"
CURVE_FACTORY = "0xB9fC157394Af804a3578134A6585C0dc9cc990d4"  # Crypto Pool Factory (verified address)
CRV_TOKEN = "0xD533a949740bb3306d119CC777fa900bA034cd52"

# Convex Finance
CONVEX_BOOSTER = "0xF403C135812408BFbE8713b5A23a04b3D48AAE31"
CONVEX_VOTER_PROXY = "0x989AEb4d175e16225E39E87d0D97A3360524AD80"
CONVEX_CVX = "0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B"
CONVEX_CVXCRV = "0x62B9c7356A2Dc64a1969e19C23e4f579F9810Aa7"
CONVEX_CRV_DEPOSITOR = "0x8014595F2AB54cD7c604B00E9fb932176fDc86Ae"
CONVEX_CVX_REWARDS = "0xCF50b810E57Ac33B91dCF525C6ddd9881B139332"
CONVEX_CVXCRV_REWARDS = "0x3Fe65692bfCD0e6CF84cB1E7d24108E434A7587e"

# Convex Vault Factory (f(x) Protocol specific)
CONVEX_VAULT_FACTORY = "0xAffe966B27ba3E4Ebb8A0eC124C7b7019CC762f8"
# Event emitter for AddUserVault events
CONVEX_VAULT_REGISTRY = "0xdb95d646012bb87ac2e6cd63eab2c42323c1f5af"

# cvxFXN Staking
CVXFXN_TOKEN = "0x183395DbD0B5e93323a7286D1973150697FFFCB3"
CVXFXN_DEPOSIT = "0x56B3c8eF8A095f8637B6A84942aA898326B82b91"  # Deposit contract for converting FXN to cvxFXN
CVXFXN_STAKE = "0xEC60Cd4a5866fb3B0DD317A46d3B474a24e06beF"  # Stake contract for staking cvxFXN

# Convex Pools (f(x) Protocol related)
# Note: Pools are differentiated by both the staked token AND what they redeem to
# Format: {staked_token}_{redeems_to} for unique identification
CONVEX_POOLS = {
    "fxusd_stability_fxn": {
        "pool_id": 37,
        "name": "fxUSD V2 Stability Pool (Earns FXN)",
        "staked_token": FXUSD_BASE_POOL,  # fxBASE (LP token)
        "base_token": FXUSD,  # fxUSD
        "redeems_to": "fxUSD",  # What asset this pool redeems to
        "earns": "FXN",  # What rewards this pool earns
        "fx_gauge": "0x215D87bd3c7482E2348338815E059DE07Daf798A",
        "stability_pool": None,  # Not applicable for V2
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/37",
    },
    "fxusd_stability_wsteth": {
        "pool_id": 36,
        "name": "fxUSD V2 Stability Pool (Earns wstETH)",
        "staked_token": FXUSD_BASE_POOL,  # fxBASE (LP token) (same as FXN pool)
        "base_token": FXUSD,  # fxUSD (same as FXN pool)
        "redeems_to": "fxUSD",  # What asset this pool redeems to (same as FXN pool)
        "earns": "wstETH",  # What rewards this pool earns (different from FXN pool)
        "fx_gauge": "0xEd92dDe3214c24Ae04F5f96927E3bE8f8DbC3289",
        "stability_pool": None,  # Not applicable for V2
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/36",
    },
    "feth_stability_wsteth": {
        "pool_id": 0,
        "name": "fETH Stability Pool (Redeems to wstETH)",
        "staked_token": FETH,  # fETH (same as xETH pool)
        "base_token": STETH,  # stETH (same as xETH pool)
        "redeems_to": "wstETH",  # What asset this pool redeems to (different from xETH pool)
        "fx_gauge": None,  # Uses stability pool address
        "stability_pool": "0xc6dEe5913e010895F3702bc43a40d661B13a40BD",
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/0",
    },
    "feth_stability_xeth": {
        "pool_id": 1,
        "name": "fETH Stability Pool (Redeems to xETH)",
        "staked_token": FETH,  # fETH (same as wstETH pool)
        "base_token": STETH,  # stETH (same as wstETH pool)
        "redeems_to": "xETH",  # What asset this pool redeems to (different from wstETH pool)
        "fx_gauge": None,  # Uses stability pool address
        "stability_pool": "0xB87A8332dFb1C76Bb22477dCfEdDeB69865cA9f9",
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/1",
    },
    "rusd_stability_weeth": {
        "pool_id": 19,
        "name": "rUSD Stability Pool (Redeems to weETH)",
        "staked_token": "0x9216272158F563488FfC36AFB877acA2F265C560",  # F(x) staked token (same as xeETH pool)
        "base_token": "0xcd5fe23c85820f7b72d0926fc9b05b43e359b7ee",  # Base token (same as xeETH pool)
        "redeems_to": "weETH",  # What asset this pool redeems to (different from xeETH pool)
        "fx_gauge": None,  # Uses stability pool address
        "stability_pool": "0xc2DeF1E39FF35367F2F2a312a793477C576fD4c3",
        "rusd_token": RUSD,  # rUSD token address (for reference)
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/19",
    },
    "rusd_stability_ezeth": {
        "pool_id": 23,
        "name": "rUSD Stability Pool (Redeems to ezETH)",
        "staked_token": "0x50B4DC15b34E31671c9cA40F9eb05D7eBd6b13f9",  # F(x) staked token (same as xezETH pool)
        "base_token": "0xbf5495efe5db9ce00f80364c8b423567e58d2110",  # Base token (same as xezETH pool)
        "redeems_to": "ezETH",  # What asset this pool redeems to (different from xezETH pool)
        "fx_gauge": None,  # Uses stability pool address
        "stability_pool": "0xf58c499417e36714e99803Cb135f507a95ae7169",
        "rusd_token": RUSD,  # rUSD token address (for reference)
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/23",
    },
    "rusd_stability_xezeth": {
        "pool_id": 24,
        "name": "rUSD Stability Pool (Redeems to xezETH)",
        "staked_token": "0x50B4DC15b34E31671c9cA40F9eb05D7eBd6b13f9",  # F(x) staked token (same as ezETH pool)
        "base_token": "0xbf5495efe5db9ce00f80364c8b423567e58d2110",  # Base token (same as ezETH pool)
        "redeems_to": "xezETH",  # What asset this pool redeems to (different from ezETH pool)
        "fx_gauge": None,  # Uses stability pool address
        "stability_pool": "0xBa947cba270D30967369Bf1f73884Be2533d7bDB",
        "rusd_token": RUSD,  # rUSD token address (for reference)
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/24",
    },
    "btcusd_stability_wbtc": {
        "pool_id": 25,
        "name": "btcUSD Stability Pool (Redeems to WBTC)",
        "staked_token": "0x576b4779727F5998577bb4e25bf726abE742b9F7",  # F(x) staked token (same as xWBTC pool)
        "base_token": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",  # WBTC (base token) (same as xWBTC pool)
        "redeems_to": "WBTC",  # What asset this pool redeems to (different from xWBTC pool)
        "fx_gauge": None,  # Uses stability pool address
        "stability_pool": "0xf291EC9C2F87A41386fd94eC4BCdC3270eD04482",
        "btcusd_token": BTCUSD,  # btcUSD token address (for reference)
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/25",
    },
    "btcusd_stability_xwbtc": {
        "pool_id": 26,
        "name": "btcUSD Stability Pool (Redeems to xWBTC)",
        "staked_token": "0x576b4779727F5998577bb4e25bf726abE742b9F7",  # F(x) staked token (same as WBTC pool)
        "base_token": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",  # WBTC (base token) (same as WBTC pool)
        "redeems_to": "xWBTC",  # What asset this pool redeems to (different from WBTC pool)
        "fx_gauge": None,  # Uses stability pool address
        "stability_pool": "0xBB549046497364A1E26F94f7e93685Dc29FAd8c0",
        "btcusd_token": BTCUSD,  # btcUSD token address (for reference)
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/26",
    },
    "rusd_stability_xeeth": {
        "pool_id": 20,
        "name": "rUSD Stability Pool (Redeems to xeETH)",
        "staked_token": "0x9216272158F563488FfC36AFB877acA2F265C560",  # F(x) staked token (same as weETH pool)
        "base_token": "0xcd5fe23c85820f7b72d0926fc9b05b43e359b7ee",  # Base token (same as weETH pool)
        "redeems_to": "xeETH",  # What asset this pool redeems to (different from weETH pool)
        "fx_gauge": None,  # Uses stability pool address
        "stability_pool": "0x7EB0ed173480299e1310d55E04Ece401c2B06626",
        "rusd_token": RUSD,  # rUSD token address (for reference)
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/20",
    },
    "cvxusd_stability_acvx": {
        "pool_id": 33,
        "name": "cvxUSD Stability Pool (Redeems to aCVX)",
        "staked_token": "0x9Fcb2c47DaB11e38fec4b8c886F63741bfED4c41",  # F(x) staked token (same as xCVX pool)
        "base_token": "0xb0903ab70a7467ee5756074b31ac88aebb8fb777",  # Base token (same as xCVX pool)
        "redeems_to": "aCVX",  # What asset this pool redeems to (different from xCVX pool)
        "fx_gauge": None,  # Uses stability pool address
        "stability_pool": "0x0AB9Dc99a33Cd02A776a9117f211803Fb69Fd7C4",
        "cvxusd_token": CVXUSD,  # cvxUSD token address (for reference)
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/33",
    },
    "cvxusd_stability_xcvx": {
        "pool_id": 34,
        "name": "cvxUSD Stability Pool (Redeems to xCVX)",
        "staked_token": "0x9Fcb2c47DaB11e38fec4b8c886F63741bfED4c41",  # F(x) staked token (same as aCVX pool)
        "base_token": "0xb0903ab70a7467ee5756074b31ac88aebb8fb777",  # Base token (same as aCVX pool)
        "redeems_to": "xCVX",  # What asset this pool redeems to (different from aCVX pool)
        "fx_gauge": None,  # Uses stability pool address
        "stability_pool": "0xA04d761adad1029e4f2F60ac973a76c5307EfceA",
        "cvxusd_token": CVXUSD,  # cvxUSD token address (for reference)
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/34",
    },
    "eth_fxn_curve": {
        "pool_id": 6,
        "name": "ETH/FXN Curve Pool",
        "pool_type": "curve_lp",  # Different from stability pools
        "staked_token": "0xE06A65e09Ae18096B99770A809BA175FA05960e2",  # Curve LP token
        "base_token": None,  # Curve pools have multiple underlying tokens
        "redeems_to": "Curve LP",  # Curve LP tokens, not a single asset
        "fx_gauge": "0xA5250C540914E012E22e623275E290c4dC993D11",  # ETH/FXN gauge
        "stability_pool": None,  # Not a stability pool
        "curve_pool": "ETH/FXN",  # Curve pool pair
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/6",
    },
    "fxn_cvxfxn_curve": {
        "pool_id": 7,
        "name": "FXN/cvxFXN Curve Pool",
        "pool_type": "curve_lp",  # Different from stability pools
        "staked_token": "0x1062FD8eD633c1f080754c19317cb3912810B5e5",  # Curve LP token
        "base_token": None,  # Curve pools have multiple underlying tokens
        "redeems_to": "Curve LP",  # Curve LP tokens, not a single asset
        "fx_gauge": "0xfEFafB9446d84A9e58a3A2f2DDDd7219E8c94FbB",  # FXN/cvxFXN gauge
        "stability_pool": None,  # Not a stability pool
        "curve_pool": "FXN/cvxFXN",  # Curve pool pair
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/7",
    },
    "fxn_sdfxn_curve": {
        "pool_id": 8,
        "name": "FXN/sdFXN Curve Pool",
        "pool_type": "curve_lp",  # Different from stability pools
        "staked_token": "0x28Ca243dc0aC075dD012fCf9375C25D18A844d96",  # Curve LP token
        "base_token": None,  # Curve pools have multiple underlying tokens
        "redeems_to": "Curve LP",  # Curve LP tokens, not a single asset
        "fx_gauge": "0x5b1D12365BEc01b8b672eE45912d1bbc86305dba",  # FXN/sdFXN gauge
        "stability_pool": None,  # Not a stability pool
        "curve_pool": "FXN/sdFXN",  # Curve pool pair
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/8",
    },
    "crvusd_fxusd_curve": {
        "pool_id": 9,
        "name": "crvUSD/fxUSD Curve Pool",
        "pool_type": "curve_lp",  # Different from stability pools
        "staked_token": "0x8fFC7b89412eFD0D17EDEa2018F6634eA4C2FCb2",  # Curve LP token
        "base_token": None,  # Curve pools have multiple underlying tokens
        "redeems_to": "Curve LP",  # Curve LP tokens, not a single asset
        "fx_gauge": "0xF4Bd6D66bAFEA1E0500536d52236f64c3e8a2a84",  # crvUSD/fxUSD gauge
        "stability_pool": None,  # Not a stability pool
        "curve_pool": "crvUSD/fxUSD",  # Curve pool pair
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/9",
    },
    "pyusd_fxusd_curve": {
        "pool_id": 10,
        "name": "pyUSD/fxUSD Curve Pool",
        "pool_type": "curve_lp",  # Different from stability pools
        "staked_token": "0xd6982da59F1D26476E259559508f4135135cf9b8",  # Curve LP token
        "base_token": None,  # Curve pools have multiple underlying tokens
        "redeems_to": "Curve LP",  # Curve LP tokens, not a single asset
        "fx_gauge": "0xeD113B925AC3f972161Be012cdFEE33470040E6a",  # pyUSD/fxUSD gauge
        "stability_pool": None,  # Not a stability pool
        "curve_pool": "pyUSD/fxUSD",  # Curve pool pair
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/10",
    },
    "dola_fxusd_curve": {
        "pool_id": 11,
        "name": "DOLA/fxUSD Curve Pool",
        "pool_type": "curve_lp",  # Different from stability pools
        "staked_token": "0x189B4e49B5cAf33565095097b4B960F14032C7D0",  # Curve LP token
        "base_token": None,  # Curve pools have multiple underlying tokens
        "redeems_to": "Curve LP",  # Curve LP tokens, not a single asset
        "fx_gauge": "0x61F32964C39Cca4353144A6DB2F8Efdb3216b35B",  # DOLA/fxUSD gauge
        "stability_pool": None,  # Not a stability pool
        "curve_pool": "DOLA/fxUSD",  # Curve pool pair
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/11",
    },
    "grai_fxusd_curve": {
        "pool_id": 12,
        "name": "GRAI/fxUSD Curve Pool",
        "pool_type": "curve_lp",  # Different from stability pools
        "staked_token": "0x69Cf42F15F9325986154b61A013da6E8feC82CCF",  # Curve LP token
        "base_token": None,  # Curve pools have multiple underlying tokens
        "redeems_to": "Curve LP",  # Curve LP tokens, not a single asset
        "fx_gauge": "0xfa4761512aaf899b010438a10C60D01EBdc0eFcA",  # GRAI/fxUSD gauge
        "stability_pool": None,  # Not a stability pool
        "curve_pool": "GRAI/fxUSD",  # Curve pool pair
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/12",
    },
    "frax_fxusd_curve": {
        "pool_id": 13,
        "name": "FRAX/fxUSD Curve Pool",
        "pool_type": "curve_lp",  # Different from stability pools
        "staked_token": "0x1EE81c56e42EC34039D993d12410d437DdeA341E",  # Curve LP token
        "base_token": None,  # Curve pools have multiple underlying tokens
        "redeems_to": "Curve LP",  # Curve LP tokens, not a single asset
        "fx_gauge": "0x31b630B21065664dDd2dBa0eD3a60D8ff59501F0",  # FRAX/fxUSD gauge
        "stability_pool": None,  # Not a stability pool
        "curve_pool": "FRAX/fxUSD",  # Curve pool pair
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/13",
    },
    "gho_fxusd_curve": {
        "pool_id": 14,
        "name": "GHO/fxUSD Curve Pool",
        "pool_type": "curve_lp",  # Different from stability pools
        "staked_token": "0x74345504Eaea3D9408fC69Ae7EB2d14095643c5b",  # Curve LP token
        "base_token": None,  # Curve pools have multiple underlying tokens
        "redeems_to": "Curve LP",  # Curve LP tokens, not a single asset
        "fx_gauge": "0xf0A3ECed42Dbd8353569639c0eaa833857aA0A75",  # GHO/fxUSD gauge
        "stability_pool": None,  # Not a stability pool
        "curve_pool": "GHO/fxUSD",  # Curve pool pair
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/14",
    },
    "mkusd_fxusd_curve": {
        "pool_id": 15,
        "name": "mkUSD/fxUSD Curve Pool",
        "pool_type": "curve_lp",  # Different from stability pools
        "staked_token": "0xcA554E2e2948a211D4650Fe0F4E271f01f9cB5F1",  # Curve LP token
        "base_token": None,  # Curve pools have multiple underlying tokens
        "redeems_to": "Curve LP",  # Curve LP tokens, not a single asset
        "fx_gauge": "0xDbA9a415bae1983a945ba078150CAe8b690c9229",  # mkUSD/fxUSD gauge
        "stability_pool": None,  # Not a stability pool
        "curve_pool": "mkUSD/fxUSD",  # Curve pool pair
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/15",
    },
    "ultra_fxusd_curve": {
        "pool_id": 16,
        "name": "ULTRA/fxUSD Curve Pool",
        "pool_type": "curve_lp",  # Different from stability pools
        "staked_token": "0xF33aB11E5C4e55DAcB13644f0C0A9d1e199A796F",  # Curve LP token
        "base_token": None,  # Curve pools have multiple underlying tokens
        "redeems_to": "Curve LP",  # Curve LP tokens, not a single asset
        "fx_gauge": "0x0d3e9A29E856CF00d670368a7ab0512cb0c29FAC",  # ULTRA/fxUSD gauge
        "stability_pool": None,  # Not a stability pool
        "curve_pool": "ULTRA/fxUSD",  # Curve pool pair
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/16",
    },
    "fxusd_rusd_curve": {
        "pool_id": 21,
        "name": "fxUSD/rUSD Curve Pool",
        "pool_type": "curve_lp",  # Different from stability pools
        "staked_token": "0x2116BFaD62b383043230501f6a124c6EA60CcfA5",  # Curve LP token
        "base_token": None,  # Curve pools have multiple underlying tokens
        "redeems_to": "Curve LP",  # Curve LP tokens, not a single asset
        "fx_gauge": "0x697DDb8e742047561C8e4bB69d2DDB1b8Bb42b60",  # fxUSD/rUSD gauge
        "stability_pool": None,  # Not a stability pool
        "curve_pool": "fxUSD/rUSD",  # Curve pool pair
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/21",
    },
    "alusd_fxusd_curve": {
        "pool_id": 22,
        "name": "alUSD/fxUSD Curve Pool",
        "pool_type": "curve_lp",  # Different from stability pools
        "staked_token": "0x27cB9629aE3Ee05cb266B99cA4124EC999303c9D",  # Curve LP token
        "base_token": None,  # Curve pools have multiple underlying tokens
        "redeems_to": "Curve LP",  # Curve LP tokens, not a single asset
        "fx_gauge": "0x9c7003bC16F2A1AA47451C858FEe6480B755363e",  # alUSD/fxUSD gauge
        "stability_pool": None,  # Not a stability pool
        "curve_pool": "alUSD/fxUSD",  # Curve pool pair
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/22",
    },
    "mim_fxusd_curve": {
        "pool_id": 27,
        "name": "MIM/fxUSD Curve Pool",
        "pool_type": "curve_lp",  # Different from stability pools
        "staked_token": "0xD7Bf9bb6Bd088317Effd116E2B70ea3A054cBceb",  # Curve LP token
        "base_token": None,  # Curve pools have multiple underlying tokens
        "redeems_to": "Curve LP",  # Curve LP tokens, not a single asset
        "fx_gauge": "0xDF7fbDBAE50C7931a11765FAEd9fe1A002605B55",  # MIM/fxUSD gauge
        "stability_pool": None,  # Not a stability pool
        "curve_pool": "MIM/fxUSD",  # Curve pool pair
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/27",
    },
    "rgusd_fxusd_curve": {
        "pool_id": 28,
        "name": "rgUSD/fxUSD Curve Pool",
        "pool_type": "curve_lp",  # Different from stability pools
        "staked_token": "0x6fC7eA6CA8Cd2759803eb78159C931a8FF5E0557",  # Curve LP token
        "base_token": None,  # Curve pools have multiple underlying tokens
        "redeems_to": "Curve LP",  # Curve LP tokens, not a single asset
        "fx_gauge": "0x4CA79F4FE25BCD329445CDBE7E065427ACa98380",  # rgUSD/fxUSD gauge
        "stability_pool": None,  # Not a stability pool
        "curve_pool": "rgUSD/fxUSD",  # Curve pool pair
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/28",
    },
    "eusd_fxusd_curve": {
        "pool_id": 29,
        "name": "eUSD/fxUSD Curve Pool",
        "pool_type": "curve_lp",  # Different from stability pools
        "staked_token": "0x16b54e3aC8e3ba088333985035b869847e36E770",  # Curve LP token
        "base_token": None,  # Curve pools have multiple underlying tokens
        "redeems_to": "Curve LP",  # Curve LP tokens, not a single asset
        "fx_gauge": "0x5801Bb8f568979C722176Df36b1a74654A9C52b5",  # eUSD/fxUSD gauge
        "stability_pool": None,  # Not a stability pool
        "curve_pool": "eUSD/fxUSD",  # Curve pool pair
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/29",
    },
    "zunusd_fxusd_curve": {
        "pool_id": 31,
        "name": "zunUSD/fxUSD Curve Pool",
        "pool_type": "curve_lp",  # Different from stability pools
        "staked_token": "0x13eA95Ce68185e334d3747539845A3b7643a8cab",  # Curve LP token
        "base_token": None,  # Curve pools have multiple underlying tokens
        "redeems_to": "Curve LP",  # Curve LP tokens, not a single asset
        "fx_gauge": "0x9516c367952430371A733E5eBb587E01eE082F99",  # zunUSD/fxUSD gauge
        "stability_pool": None,  # Not a stability pool
        "curve_pool": "zunUSD/fxUSD",  # Curve pool pair
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/31",
    },
    "usdc_fxusd_curve": {
        "pool_id": 32,
        "name": "USDC/fxUSD Curve Pool",
        "pool_type": "curve_lp",  # Different from stability pools
        "staked_token": "0x5018BE882DccE5E3F2f3B0913AE2096B9b3fB61f",  # Curve LP token
        "base_token": None,  # Curve pools have multiple underlying tokens
        "redeems_to": "Curve LP",  # Curve LP tokens, not a single asset
        "fx_gauge": "0xf1E141C804BA39b4a031fDF46e8c08dBa7a0df60",  # USDC/fxUSD gauge
        "stability_pool": None,  # Not a stability pool
        "curve_pool": "USDC/fxUSD",  # Curve pool pair
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/32",
    },
    "reusd_fxusd_curve": {
        "pool_id": 38,
        "name": "reUSD/fxUSD Curve Pool",
        "pool_type": "curve_lp",  # Different from stability pools
        "staked_token": "0xb0ef04ACE97d350E24Efa5139d2590D26a61A8Dc",  # Curve LP token
        "base_token": None,  # Curve pools have multiple underlying tokens
        "redeems_to": "Curve LP",  # Curve LP tokens, not a single asset
        "fx_gauge": "0x8d9186Fa822624bad50a5cB2545048CB26b4E65E",  # reUSD/fxUSD gauge
        "stability_pool": None,  # Not a stability pool
        "curve_pool": "reUSD/fxUSD",  # Curve pool pair
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/38",
    },
    "msusd_fxusd_curve": {
        "pool_id": 41,
        "name": "msUSD/fxUSD Curve Pool",
        "pool_type": "curve_lp",  # Different from stability pools
        "staked_token": "0x138Bb0f3208bd729a561F3786DDb97BBc69e6628",  # Curve LP token
        "base_token": None,  # Curve pools have multiple underlying tokens
        "redeems_to": "Curve LP",  # Curve LP tokens, not a single asset
        "fx_gauge": "0x2122a2bee97545595550b85379AC7676Fd21a5B4",  # msUSD/fxUSD gauge
        "stability_pool": None,  # Not a stability pool
        "curve_pool": "msUSD/fxUSD",  # Curve pool pair
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/41",
    },
    "fxsave_scrvusd_curve": {
        "pool_id": 40,
        "name": "fxSAVE/scrvUSD Curve Pool",
        "pool_type": "curve_lp",  # Different from stability pools
        "staked_token": "0xb6E4821c6fCABe32f5F452dfD3Ef20Ce2A3a48E2",  # Curve LP token
        "base_token": None,  # Curve pools have multiple underlying tokens
        "redeems_to": "Curve LP",  # Curve LP tokens, not a single asset
        "fx_gauge": "0x6FcFe767c479ef1f2d8c7A4b27e2aBaDD355910F",  # fxSAVE/scrvUSD gauge
        "stability_pool": None,  # Not a stability pool
        "curve_pool": "fxSAVE/scrvUSD",  # Curve pool pair
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/40",
    },
    "fxusd_rusd_btcusd_curve": {
        "pool_id": 35,
        "name": "fxUSD/rUSD/btcUSD Curve Pool",
        "pool_type": "curve_lp",  # Different from stability pools
        "staked_token": "0x52bF165abd26106D810733CC29FAfF68b96DECe8",  # Curve LP token
        "base_token": None,  # Curve pools have multiple underlying tokens
        "redeems_to": "Curve LP",  # Curve LP tokens, not a single asset
        "fx_gauge": "0x7a505e920d5d7E4b402D9Ee345fB7E8Cdc265262",  # fxUSD/rUSD/btcUSD gauge
        "stability_pool": None,  # Not a stability pool
        "curve_pool": "fxUSD/rUSD/btcUSD",  # Curve tri-pool
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/35",
    },
    "fxusd_usdn_curve": {
        "pool_id": 39,
        "name": "fxUSD/USDN Curve Pool",
        "pool_type": "curve_lp",  # Different from stability pools
        "staked_token": "0xB6aF437ceEa0DBeA524115eFC905F0F44fd1eBAF",  # Curve LP token
        "base_token": None,  # Curve pools have multiple underlying tokens
        "redeems_to": "Curve LP",  # Curve LP tokens, not a single asset
        "fx_gauge": "0xa295829c082C4d21fE37dbC8C96bFa0ef6dbaa92",  # fxUSD/USDN gauge
        "stability_pool": None,  # Not a stability pool
        "curve_pool": "fxUSD/USDN",  # Curve pool pair
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/39",
    },
    "fxusd_usdc_usdaf_bold_curve": {
        "pool_id": 42,
        "name": "fxUSD/USDC/USDaf/BOLD Curve Pool",
        "pool_type": "curve_lp",  # Different from stability pools
        "staked_token": "0x8B878AFE454e31CF0A79c6D7cf2f077DD286C12f",  # Curve LP token
        "base_token": None,  # Curve pools have multiple underlying tokens
        "redeems_to": "Curve LP",  # Curve LP tokens, not a single asset
        "fx_gauge": "0xE534E5e86382d64133ecd6b7f717C69BEC8B40CA",  # fxUSD/USDC/USDaf/BOLD gauge
        "stability_pool": None,  # Not a stability pool
        "curve_pool": "fxUSD/USDC/USDaf/BOLD",  # Curve multi-pool
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/42",
    },
    "dola_fxsave_curve": {
        "pool_id": 43,
        "name": "DOLA/fxSAVE Curve Pool",
        "pool_type": "curve_lp",  # Different from stability pools
        "staked_token": "0x2b854e225d7282854819327D0CA5b8D8AA8CAaED",  # Curve LP token
        "base_token": None,  # Curve pools have multiple underlying tokens
        "redeems_to": "Curve LP",  # Curve LP tokens, not a single asset
        "fx_gauge": "0x7d4674b837429c44914961cb9F21dD6dEFd0eee0",  # DOLA/fxSAVE gauge
        "stability_pool": None,  # Not a stability pool
        "curve_pool": "DOLA/fxSAVE",  # Curve pool pair
        "convex_url": "https://fx.convexfinance.com/stake/ethereum/43",
    }
}

# Address Map for Convenience
CONTRACTS = {
    "fxUSD": FXUSD,
    "fxUSD_BasePool": FXUSD_BASE_POOL,
    "PegKeeper": PEG_KEEPER,
    "PoolManager": POOL_MANAGER,
    "ReservePool": RESERVE_POOL,
    "RevenuePool": REVENUE_POOL,
    "DiamondRouter": DIAMOND_ROUTER,
    "stETH_Oracle": STETH_PRICE_ORACLE,
    "MultiPathConverter": MULTI_PATH_CONVERTER,
    "wstETH_Pool": WSTETH_POOL,
    "sfrxETH_Market": SFRXETH_MARKET,
    "wstETH_Market": WSTETH_MARKET,
    "fETH": FETH,
    "rUSD": RUSD,
    "arUSD": ARUSD,
    "btcUSD": BTCUSD,
    "cvxUSD": CVXUSD,
    "xETH": XETH,
    "xCVX": XCVX,
    "xWBTC": XWBTC,
    "xeETH": XEETH,
    "xezETH": XEZETH,
    "xstETH": XSTETH,
    "xfrxETH": XFRXETH,
    "FXN": FXN,
    "veFXN": VEFXN,
    "GaugeController": GAUGE_CONTROLLER,
    "RebalancePoolRegistry": REBALANCE_POOL_REGISTRY,
    "stETH_Treasury": STETH_TREASURY_PROXY,
    "stETH_Gateway": STETH_GATEWAY,
    "Vesting_FXN": VESTING_FXN,
    "Vesting_fETH": VESTING_FETH,
    "Vesting_fxUSD": VESTING_FXUSD,
    "Saving_fxUSD": SAVING_FXUSD,
    "fxSP": FXSP,
    "RebalancePoolImplementation": REBALANCE_POOL_IMPLEMENTATION,
    "stETH": STETH,
    "wstETH": WSTETH,
    "frxETH": FRXETH,
    "sfrxETH": SFRXETH,
    # Curve Finance
    "CurveRegistry": CURVE_REGISTRY,
    "CurveMetaRegistry": CURVE_META_REGISTRY,
    "CurveAddressProvider": CURVE_ADDRESS_PROVIDER,
    "CurveFactory": CURVE_FACTORY,
    "CRV": CRV_TOKEN,
    # Convex Finance
    "ConvexBooster": CONVEX_BOOSTER,
    "ConvexVoterProxy": CONVEX_VOTER_PROXY,
    "ConvexVaultFactory": CONVEX_VAULT_FACTORY,
    "CVX": CONVEX_CVX,
    "cvxCRV": CONVEX_CVXCRV,
    "cvxFXN": CVXFXN_TOKEN,
    "cvxFXN_Deposit": CVXFXN_DEPOSIT,
    "cvxFXN_Stake": CVXFXN_STAKE,
}

