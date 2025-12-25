"""
Lubit Helper Functions
"""

from typing import List


def get_hourly_market_ids(zone: str, date_str: str) -> List[str]:
    """
    Generate all 24 hourly market IDs for a zone and date.

    Args:
        zone: Bidding zone (e.g., "DK1")
        date_str: Date in YYYY-MM-DD format

    Returns:
        List of 24 market IDs

    Example:
        ids = get_hourly_market_ids("DK1", "2025-12-23")
        # ["DK1_2025-12-23_00:00-01:00_H", "DK1_2025-12-23_01:00-02:00_H", ...]
    """
    market_ids = []
    for hour in range(24):
        next_hour = (hour + 1) % 24
        time_slot = f"{hour:02d}:00-{next_hour:02d}:00"
        market_id = f"{zone}_{date_str}_{time_slot}_H"
        market_ids.append(market_id)
    return market_ids


def get_quarter_market_ids(zone: str, date_str: str) -> List[str]:
    """
    Generate all 96 quarter-hour market IDs for a zone and date.

    Args:
        zone: Bidding zone (e.g., "DK1")
        date_str: Date in YYYY-MM-DD format

    Returns:
        List of 96 market IDs

    Example:
        ids = get_quarter_market_ids("DK1", "2025-12-23")
        # ["DK1_2025-12-23_00:00-00:15_Q", "DK1_2025-12-23_00:15-00:30_Q", ...]
    """
    market_ids = []
    for quarter in range(96):
        start_minutes = quarter * 15
        end_minutes = (quarter + 1) * 15

        start_hour = start_minutes // 60
        start_min = start_minutes % 60
        end_hour = (end_minutes // 60) % 24
        end_min = end_minutes % 60

        time_slot = f"{start_hour:02d}:{start_min:02d}-{end_hour:02d}:{end_min:02d}"
        market_id = f"{zone}_{date_str}_{time_slot}_Q"
        market_ids.append(market_id)
    return market_ids


# Available bidding zones
BIDDING_ZONES = [
    "DK1", "DK2",           # Denmark
    "NO1", "NO2", "NO3", "NO4", "NO5",  # Norway
    "SE1", "SE2", "SE3", "SE4",  # Sweden
    "FI",                   # Finland
    "DE-LU",                # Germany/Luxembourg
    "AT",                   # Austria
    "NL",                   # Netherlands
    "BE",                   # Belgium
]
