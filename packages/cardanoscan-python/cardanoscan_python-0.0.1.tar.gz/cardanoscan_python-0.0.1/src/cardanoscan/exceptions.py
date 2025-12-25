from typing import Optional


class CardanoscanError(Exception):
    """Base SDK error."""


class TransportError(CardanoscanError):
    """Network/transport layer error."""


class HTTPStatusError(CardanoscanError):
    """Non-2xx HTTP responses."""
    def __init__(self, status_code: int, message: str, body: Optional[object] = None):
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code
        self.body = body


class AuthenticationError(CardanoscanError):
    """Auth errors (401/403)."""


class RateLimitError(CardanoscanError):
    """429 or rate-limiting responses."""


class TimeoutError(CardanoscanError):
    """Timeouts."""
