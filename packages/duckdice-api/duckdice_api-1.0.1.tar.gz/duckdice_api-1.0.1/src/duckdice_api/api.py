"""DuckDice API Client

This module provides a small, well-documented client for the DuckDice
Bot API (https://duckdice.io/bot-api). It implements the commonly used
endpoints such as placing bets and retrieving user/currency statistics.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import requests


class DuckDiceAPIException(Exception):
    """Base exception for DuckDice API errors."""


@dataclass
class DuckDiceConfig:
    """Configuration for DuckDice API client.

    Attributes:
        api_key: API key for bot endpoints.
        base_url: Base URL for the DuckDice API (default: https://duckdice.io/api).
        timeout: Request timeout in seconds.
    """

    api_key: str
    base_url: str = "https://duckdice.io/api"
    timeout: int = 30


class DuckDiceAPI:
    """Client for DuckDice bot API.

    Example:
        from duckdice_api import DuckDiceAPI, DuckDiceConfig

        cfg = DuckDiceConfig(api_key="your_api_key")
        client = DuckDiceAPI(cfg)

    """

    def __init__(self, config: DuckDiceConfig) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "DuckDiceBot/1.0.0"})

    def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None, json: Optional[Any] = None) -> Any:
        url = f"{self.config.base_url.rstrip('/')}/{path.lstrip('/') }"
        params = params.copy() if params else {}
        params.setdefault("api_key", self.config.api_key)
        try:
            resp = self.session.request(method, url, params=params, json=json, timeout=self.config.timeout)
        except requests.RequestException as exc:
            raise DuckDiceAPIException(f"request failed: {exc}") from exc

        if not resp.ok:
            # try to include server JSON message when available
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise DuckDiceAPIException(f"HTTP {resp.status_code}: {detail}")

        try:
            return resp.json()
        except ValueError:
            return resp.text

    # --- Betting endpoints ---
    def play_dice(self, symbol: str, amount: str, chance: str, is_high: bool, user_wagering_bonus_hash: Optional[str] = None, faucet: Optional[bool] = None, tle_hash: Optional[str] = None) -> Dict[str, Any]:
        """Place an Original Dice bet (POST /api/dice/play).

        Args:
            symbol: Currency symbol (e.g. "XLM").
            amount: Bet amount as decimal string.
            chance: Win chance in percent as string (e.g. "77.77").
            is_high: True for high, False for low.
            user_wagering_bonus_hash: optional wagering bonus hash.
            faucet: optional faucet flag.
            tle_hash: optional TLE hash.

        Returns:
            Parsed JSON response from the API.
        """
        payload: Dict[str, Any] = {
            "symbol": symbol,
            "amount": amount,
            "chance": chance,
            "isHigh": bool(is_high),
        }
        if user_wagering_bonus_hash:
            payload["userWageringBonusHash"] = user_wagering_bonus_hash
        if faucet is not None:
            payload["faucet"] = bool(faucet)
        if tle_hash:
            payload["tleHash"] = tle_hash

        return self._request("POST", "/api/dice/play", json=payload)

    def play_range_dice(self, symbol: str, amount: str, range_vals: List[int], is_in: bool, user_wagering_bonus_hash: Optional[str] = None, faucet: Optional[bool] = None, tle_hash: Optional[str] = None) -> Dict[str, Any]:
        """Place a Range Dice bet (POST /api/range-dice/play).

        Args:
            range_vals: two-integer list representing the range (e.g. [0,9998]).
        """
        payload: Dict[str, Any] = {
            "symbol": symbol,
            "amount": amount,
            "range": range_vals,
            "isIn": bool(is_in),
        }
        if user_wagering_bonus_hash:
            payload["userWageringBonusHash"] = user_wagering_bonus_hash
        if faucet is not None:
            payload["faucet"] = bool(faucet)
        if tle_hash:
            payload["tleHash"] = tle_hash

        return self._request("POST", "/api/range-dice/play", json=payload)

    # --- Read endpoints ---
    def get_currency_stats(self, symbol: str) -> Dict[str, Any]:
        """Get currency stats (GET /api/bot/stats/<SYMBOL>).

        Returns bets/wins/profit/volume and balances for the provided symbol.
        """
        return self._request("GET", f"/api/bot/stats/{symbol}")

    def get_user_info(self) -> Dict[str, Any]:
        """Get bot user info (GET /api/bot/user-info).

        Returns user profile, balances, wagering bonuses and TLEs.
        """
        return self._request("GET", "/api/bot/user-info")

