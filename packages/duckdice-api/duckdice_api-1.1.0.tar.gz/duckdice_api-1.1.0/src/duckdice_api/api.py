from .client import DuckDiceAPI, DuckDiceConfig
from .exceptions import DuckDiceError

# Alias for backward compatibility
DuckDiceAPIException = DuckDiceError

__all__ = ["DuckDiceAPI", "DuckDiceConfig", "DuckDiceAPIException"]

