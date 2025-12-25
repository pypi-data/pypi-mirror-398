from fx_sdk import ProtocolClient, constants, utils

# Initialize read-only client (no private key)
client = ProtocolClient("https://eth.llamarpc.com")

# Read balances for ANY wallet address
vitalik_address = "0xcab03D02d3b7DFa31848d07C276ecE781304d9aC"

# Get specific token balance
fxusd_balance = client.get_fxusd_balance(vitalik_address)
print(f"fxUSD: {fxusd_balance}")

# Get all protocol balances
all_balances = client.get_all_balances(vitalik_address)
for token, balance in all_balances.items():
    print(f"{token}: {balance}")

# Get any ERC20 token balance
custom_balance = client.get_token_balance(
    constants.FXN, 
    vitalik_address
)