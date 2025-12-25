"""
Basic usage example for Lubit Python client
"""

from lubit import LubitClient, LubitAPIError

# Initialize client
client = LubitClient(
    api_key="lbt_pk_your_key_here",
    api_secret="lbt_sk_your_secret_here"
)

# Example 1: Get balance
print("=== Balance ===")
try:
    balance = client.get_balance()
    print(f"EUR Balance: {balance['eur_balance']}")
    print(f"vEUR Balance: {balance['veur_balance']}")
    print(f"Open Positions: {balance['open_positions']}")
except LubitAPIError as e:
    print(f"Error: {e}")

# Example 2: List markets
print("\n=== Markets ===")
try:
    markets = client.get_markets(zone="DK1", status="active")
    print(f"Found {len(markets)} active DK1 markets")
    for m in markets[:5]:
        print(f"  {m['market_id']}: {m.get('total_volume', 0)} EUR")
except LubitAPIError as e:
    print(f"Error: {e}")

# Example 3: Get market details
print("\n=== Market Details ===")
try:
    market_id = "DK1_2025-12-23_14:00-15:00_H"
    market = client.get_market(market_id)
    print(f"Market: {market.get('market_id')}")
    print(f"UP odds: {market.get('up_odds', 'N/A')}x")
    print(f"DOWN odds: {market.get('down_odds', 'N/A')}x")
    print(f"FLAT odds: {market.get('flat_odds', 'N/A')}x")
except LubitAPIError as e:
    print(f"Error: {e}")

# Example 4: Place a position (uncomment to execute)
# print("\n=== Place Position ===")
# try:
#     result = client.place_position(
#         market_id="DK1_2025-12-23_14:00-15:00_H",
#         side="up",
#         amount=10,
#         currency="vEUR"  # Use vEUR for testing
#     )
#     print(f"Position placed! ID: {result['position_id']}")
#     print(f"Implied odds: {result['implied_odds']}x")
#     print(f"Potential return: {result['potential_return']}")
# except LubitAPIError as e:
#     print(f"Error: {e}")
