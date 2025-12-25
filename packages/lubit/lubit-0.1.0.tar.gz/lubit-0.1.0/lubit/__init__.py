"""
Lubit API Python Client
=======================

Official Python client for the Lubit Energy Prediction Market API.

Usage:
    from lubit import LubitClient

    client = LubitClient(
        api_key="lbt_pk_your_key",
        api_secret="lbt_sk_your_secret"
    )

    # Get markets
    markets = client.get_markets(zone="DK1", date="2025-12-23")

    # Place a position
    result = client.place_position(
        market_id="DK1_2025-12-23_14:00-15:00_H",
        side="up",
        amount=25
    )
"""

from .client import LubitClient, LubitConfig
from .exceptions import LubitAPIError
from .helpers import get_hourly_market_ids, get_quarter_market_ids

__version__ = "0.1.0"
__all__ = [
    "LubitClient",
    "LubitConfig",
    "LubitAPIError",
    "get_hourly_market_ids",
    "get_quarter_market_ids",
]
