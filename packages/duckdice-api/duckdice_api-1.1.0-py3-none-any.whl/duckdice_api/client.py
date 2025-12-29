import requests
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from .models import PlayResponse, UserInfo, CurrencyStats
from .exceptions import (
    DuckDiceError,
    AuthenticationError,
    HTTPError,
    NetworkError,
    ValidationError,
)


@dataclass
class DuckDiceConfig:
    """Configuration for DuckDice API client.

    Attributes:
        api_key: API key for bot endpoints.
        base_url: Base URL for the DuckDice API.
        timeout: Request timeout in seconds.
    """

    api_key: str
    base_url: str = "https://duckdice.io/api"
    timeout: int = 30


class DuckDiceAPI:
    """Refactored Client for DuckDice bot API.

    Uses structured models for responses and specific exceptions for errors.
    """

    def __init__(self, config: DuckDiceConfig) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "DuckDiceBot/1.1.0"})

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
    ) -> Any:
        url = f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}"
        params = params.copy() if params else {}
        params.setdefault("api_key", self.config.api_key)

        try:
            resp = self.session.request(
                method, url, params=params, json=json, timeout=self.config.timeout
            )
        except requests.RequestException as exc:
            raise NetworkError(f"Network request failed: {exc}") from exc

        if not resp.ok:
            detail = ""
            try:
                detail = str(resp.json())
            except Exception:
                detail = resp.text

            if resp.status_code == 401 or resp.status_code == 403:
                raise AuthenticationError(f"Authentication failed: {detail}", resp.status_code, detail)
            
            raise HTTPError(f"HTTP {resp.status_code}: {detail}", resp.status_code, detail)

        try:
            return resp.json()
        except ValueError:
            return resp.text

    def get_user_info(self) -> UserInfo:
        """Get bot user info (GET /api/bot/user-info).

        Returns:
            UserInfo model containing profile, balances, and bonuses.
        """
        data = self._request("GET", "/bot/user-info")
        return UserInfo.from_dict(data)

    def get_currency_stats(self, symbol: str) -> CurrencyStats:
        """Get currency stats (GET /api/bot/stats/<SYMBOL>).

        Args:
            symbol: Currency symbol (e.g. "BTC").

        Returns:
            CurrencyStats model with volume, bets, and balances.
        """
        data = self._request("GET", f"/bot/stats/{symbol}")
        return CurrencyStats.from_dict(data)

    def get_faucet_balance(self, symbol: str) -> str:
        """Helper to get only the faucet balance for a currency.

        Args:
            symbol: Currency symbol (e.g. "XLM").

        Returns:
            The faucet balance as a string.
        """
        stats = self.get_currency_stats(symbol)
        return stats.faucet_balance

    def _prepare_bet_payload(
        self,
        symbol: str,
        amount: str,
        user_wagering_bonus_hash: Optional[str] = None,
        faucet: Optional[bool] = None,
        tle_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Internal helper to prepare common bet payload fields."""
        if not symbol:
            raise ValidationError("Currency symbol is required")
        if not amount:
            raise ValidationError("Bet amount is required")

        payload: Dict[str, Any] = {
            "symbol": symbol.upper(),
            "amount": amount,
        }
        if user_wagering_bonus_hash:
            payload["userWageringBonusHash"] = user_wagering_bonus_hash
        if faucet is not None:
            payload["faucet"] = bool(faucet)
        if tle_hash:
            payload["tleHash"] = tle_hash
        return payload

    def play_dice(
        self,
        symbol: str,
        amount: str,
        chance: str,
        is_high: bool,
        user_wagering_bonus_hash: Optional[str] = None,
        faucet: Optional[bool] = None,
        tle_hash: Optional[str] = None,
    ) -> PlayResponse:
        """Place an Original Dice bet (POST /api/dice/play).

        Args:
            symbol: Currency symbol (e.g. "BTC").
            amount: Bet amount as decimal string.
            chance: Win chance in percent (e.g. "49.5").
            is_high: True for high, False for low.
            user_wagering_bonus_hash: Optional wagering bonus hash.
            faucet: Optional faucet flag.
            tle_hash: Optional TLE hash.

        Returns:
            PlayResponse model containing bet result and user info.
        """
        payload = self._prepare_bet_payload(
            symbol=symbol,
            amount=amount,
            user_wagering_bonus_hash=user_wagering_bonus_hash,
            faucet=faucet,
            tle_hash=tle_hash,
        )
        payload["chance"] = chance
        payload["isHigh"] = bool(is_high)

        data = self._request("POST", "/dice/play", json=payload)
        return PlayResponse.from_dict(data)

    def play_range_dice(
        self,
        symbol: str,
        amount: str,
        range_vals: List[int],
        is_in: bool,
        user_wagering_bonus_hash: Optional[str] = None,
        faucet: Optional[bool] = None,
        tle_hash: Optional[str] = None,
    ) -> PlayResponse:
        """Place a Range Dice bet (POST /api/range-dice/play).

        Args:
            symbol: Currency symbol (e.g. "BTC").
            amount: Bet amount as decimal string.
            range_vals: Two-integer list representing the range (e.g. [0, 5000]).
            is_in: True for "In", False for "Out".
            user_wagering_bonus_hash: Optional wagering bonus hash.
            faucet: Optional faucet flag.
            tle_hash: Optional TLE hash.

        Returns:
            PlayResponse model containing bet result and user info.
        """
        if not isinstance(range_vals, list) or len(range_vals) != 2:
            raise ValidationError("range_vals must be a list of two integers")

        payload = self._prepare_bet_payload(
            symbol=symbol,
            amount=amount,
            user_wagering_bonus_hash=user_wagering_bonus_hash,
            faucet=faucet,
            tle_hash=tle_hash,
        )
        payload["range"] = range_vals
        payload["isIn"] = bool(is_in)

        data = self._request("POST", "/range-dice/play", json=payload)
        return PlayResponse.from_dict(data)
