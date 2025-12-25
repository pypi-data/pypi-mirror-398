"""
Lubit API Client
"""

import requests
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from .exceptions import LubitAPIError


@dataclass
class LubitConfig:
    """Configuration for Lubit API client."""
    base_url: str = "https://api.lubit.com"
    api_key: str = ""
    api_secret: str = ""
    timeout: int = 30


class LubitClient:
    """
    Python client for Lubit API.

    Example:
        client = LubitClient(
            api_key="lbt_pk_xxx",
            api_secret="lbt_sk_xxx"
        )

        # Get all DK1 markets for today
        markets = client.get_markets(zone="DK1")

        # Place a position
        result = client.place_position(
            market_id="DK1_2025-12-23_14:00-15:00_H",
            side="up",
            amount=25,
            currency="EUR"
        )
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = "https://api.lubit.com"
    ):
        self.config = LubitConfig(
            base_url=base_url,
            api_key=api_key,
            api_secret=api_secret
        )
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": api_key,
            "X-API-Secret": api_secret,
            "Content-Type": "application/json"
        })

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make API request and return JSON response."""
        url = f"{self.config.base_url}{endpoint}"

        response = self.session.request(
            method=method,
            url=url,
            params=params,
            json=json,
            timeout=self.config.timeout
        )

        data = response.json()

        if not data.get("success", False):
            error = data.get("error", "Unknown error")
            raise LubitAPIError(error, response.status_code)

        return data

    # ==================
    # Market Endpoints
    # ==================

    def get_markets(
        self,
        zone: Optional[str] = None,
        country: Optional[str] = None,
        date: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict]:
        """
        Get list of markets with optional filters.

        Args:
            zone: Bidding zone (DK1, DK2, NO1, etc.)
            country: Country code (DK, NO, SE, etc.)
            date: Date in YYYY-MM-DD format
            status: Market status (active, closed, settled)

        Returns:
            List of market dictionaries

        Example:
            markets = client.get_markets(zone="DK1", date="2025-12-23")
            for m in markets:
                print(f"{m['market_id']}: {m['total_volume']} EUR")
        """
        params = {}
        if zone:
            params["zone"] = zone
        if country:
            params["country"] = country
        if date:
            params["date"] = date
        if status:
            params["status"] = status

        data = self._request("GET", "/markets", params=params)
        return data.get("markets", [])

    def get_market(self, market_id: str) -> Dict:
        """
        Get detailed information about a specific market.

        Args:
            market_id: Market identifier (e.g., DK1_2025-12-23_14:00-15:00_H)

        Returns:
            Market dictionary with volumes, odds, and probabilities

        Example:
            market = client.get_market("DK1_2025-12-23_14:00-15:00_H")
            print(f"UP odds: {market['up_odds']}x")
        """
        data = self._request("GET", "/market", params={"id": market_id})
        return data.get("market", {})

    def get_market_history(self, market_id: str) -> Dict:
        """
        Get trading history for a market.

        Args:
            market_id: Market identifier

        Returns:
            Dictionary with stats and position history
        """
        data = self._request("GET", "/market_history", params={"id": market_id})
        return {
            "stats": data.get("stats", {}),
            "history": data.get("history", [])
        }

    # ==================
    # Trading Endpoints
    # ==================

    def place_position(
        self,
        market_id: str,
        side: str,
        amount: float,
        currency: str = "EUR"
    ) -> Dict:
        """
        Place a single position on a market.

        Args:
            market_id: Market identifier
            side: Position side ("up", "down", "flat")
            amount: Amount in EUR or vEUR (minimum 1)
            currency: "EUR" or "vEUR" (default: EUR)

        Returns:
            Dictionary with position_id, implied_odds, potential_return

        Example:
            result = client.place_position(
                market_id="DK1_2025-12-23_14:00-15:00_H",
                side="up",
                amount=25
            )
            print(f"Position {result['position_id']} placed!")
            print(f"Potential return: {result['potential_return']} EUR")
        """
        if side not in ["up", "down", "flat", "yes", "no"]:
            raise ValueError(f"Invalid side: {side}. Use up/down/flat or yes/no")

        if amount < 1:
            raise ValueError("Amount must be at least 1")

        data = self._request("POST", "/place_position", json={
            "market_id": market_id,
            "side": side,
            "amount": amount,
            "currency": currency
        })

        return {
            "position_id": data.get("position_id"),
            "implied_odds": data.get("implied_odds"),
            "potential_return": data.get("potential_return"),
            "message": data.get("message")
        }

    def place_bulk_positions(
        self,
        positions: List[Dict],
        currency: str = "EUR"
    ) -> Dict:
        """
        Place multiple positions in a single transaction.

        All positions are atomic - either all succeed or all fail.
        Maximum 24 positions per request.

        Args:
            positions: List of position dicts with market_id, side, amount
            currency: "EUR" or "vEUR" (default: EUR)

        Returns:
            Dictionary with results, total_amount, balance_after

        Example:
            positions = [
                {"market_id": "DK1_2025-12-23_00:00-01:00_H", "side": "up", "amount": 10},
                {"market_id": "DK1_2025-12-23_01:00-02:00_H", "side": "down", "amount": 15},
                {"market_id": "DK1_2025-12-23_02:00-03:00_H", "side": "flat", "amount": 20},
            ]
            result = client.place_bulk_positions(positions)
            print(f"Placed {len(result['results'])} positions")
            print(f"Total: {result['total_amount']} EUR")
        """
        if len(positions) > 24:
            raise ValueError("Maximum 24 positions per bulk request")

        # Add currency to each position if not present
        for pos in positions:
            if "currency" not in pos:
                pos["currency"] = currency

        data = self._request("POST", "/place_bulk_positions", json={
            "positions": positions
        })

        return {
            "results": data.get("results", []),
            "total_amount": data.get("total_amount"),
            "balance_after": data.get("balance_after"),
            "message": data.get("message")
        }

    # ==================
    # Account Endpoints
    # ==================

    def get_balance(self) -> Dict:
        """
        Get user's current balance.

        Returns:
            Dictionary with eur_balance, veur_balance, open_positions

        Example:
            balance = client.get_balance()
            print(f"EUR: {balance['eur_balance']}")
            print(f"vEUR: {balance['veur_balance']}")
        """
        data = self._request("GET", "/user-balance")
        return {
            "eur_balance": data.get("eur_balance", 0),
            "eurc_balance": data.get("eurc_balance", 0),
            "veur_balance": data.get("veur_balance", 0),
            "open_positions": data.get("open_positions", 0),
            "locked_in_positions": data.get("locked_in_positions", 0)
        }

    def get_transactions(
        self,
        currency: Optional[str] = None,
        transaction_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Get transaction history.

        Args:
            currency: Filter by currency (EUR, vEUR, USD)
            transaction_type: Filter by type (bet, deposit, withdrawal, payout)

        Returns:
            List of transaction dictionaries

        Example:
            transactions = client.get_transactions(currency="EUR")
            for t in transactions:
                print(f"{t['created_at']}: {t['amount']} {t['currency']}")
        """
        params = {}
        if currency:
            params["currency"] = currency
        if transaction_type:
            params["transactionType"] = transaction_type

        data = self._request("GET", "/transactions", params=params)
        return data.get("transactions", [])
