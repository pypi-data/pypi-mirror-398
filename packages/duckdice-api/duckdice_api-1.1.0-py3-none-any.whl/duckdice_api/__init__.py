"""DuckDice API Python Wrapper"""

from .client import DuckDiceAPI, DuckDiceConfig
from .models import (
    Bet,
    UserInfo,
    CurrencyStats,
    BalanceInfo,
    WageringBonus,
    PlayResponse,
)
from .exceptions import (
    DuckDiceError,
    AuthenticationError,
    HTTPError,
    NetworkError,
    ValidationError,
)

# Aliases for backward compatibility if needed in some contexts
DuckDiceAPIException = DuckDiceError

__version__ = "1.1.0"
__all__ = [
    "DuckDiceAPI",
    "DuckDiceConfig",
    "DuckDiceError",
    "DuckDiceAPIException",
    "AuthenticationError",
    "HTTPError",
    "NetworkError",
    "ValidationError",
    "Bet",
    "UserInfo",
    "CurrencyStats",
    "BalanceInfo",
    "WageringBonus",
    "PlayResponse",
]
