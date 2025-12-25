"""
Bulk trading example for Lubit Python client
"""

from lubit import LubitClient, LubitAPIError, get_hourly_market_ids

# Initialize client
client = LubitClient(
    api_key="lbt_pk_your_key_here",
    api_secret="lbt_sk_your_secret_here"
)

# Generate market IDs for all hours of a day
date = "2025-12-23"
zone = "DK1"
market_ids = get_hourly_market_ids(zone, date)

print(f"Generated {len(market_ids)} market IDs for {zone} on {date}")
print(f"First: {market_ids[0]}")
print(f"Last: {market_ids[-1]}")

# Create positions for multiple markets
# Strategy: UP for morning peak, DOWN for night, FLAT for midday
positions = []

for i, market_id in enumerate(market_ids[:12]):  # First 12 hours
    hour = i

    if hour < 6:
        side = "down"   # Night hours - expect low prices
    elif hour < 10:
        side = "up"     # Morning peak
    else:
        side = "flat"   # Midday

    positions.append({
        "market_id": market_id,
        "side": side,
        "amount": 5
    })

print(f"\n=== Placing {len(positions)} positions ===")

# Place bulk positions (uncomment to execute)
# try:
#     result = client.place_bulk_positions(positions, currency="vEUR")
#     print(f"Placed {len(result['results'])} positions")
#     print(f"Total amount: {result['total_amount']} vEUR")
#     print(f"Balance after: {result['balance_after']} vEUR")
#
#     for r in result['results']:
#         print(f"  {r['market_id']}: {r['side']} - odds {r['implied_odds']}x")
# except LubitAPIError as e:
#     print(f"Error: {e}")

# Preview positions instead
for pos in positions:
    print(f"  {pos['market_id']}: {pos['side']} - {pos['amount']} vEUR")
