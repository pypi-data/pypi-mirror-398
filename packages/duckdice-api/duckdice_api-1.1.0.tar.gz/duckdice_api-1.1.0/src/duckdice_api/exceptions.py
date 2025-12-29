from typing import Any, Optional


class DuckDiceError(Exception):
    """Base exception for DuckDice API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, response_text: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class AuthenticationError(DuckDiceError):
    """Raised when API key is invalid or unauthorized."""


class HTTPError(DuckDiceError):
    """Raised for non-200 HTTP responses."""


class NetworkError(DuckDiceError):
    """Raised for connection or timeout issues."""


class ValidationError(DuckDiceError):
    """Raised for invalid request parameters."""
