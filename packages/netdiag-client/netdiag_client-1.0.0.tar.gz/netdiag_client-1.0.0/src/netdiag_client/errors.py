"""Exception classes for NetDiag client."""


class NetDiagError(Exception):
    """Base exception for all NetDiag client errors."""

    pass


class NetDiagApiError(NetDiagError):
    """Exception raised when the API returns an error response."""

    def __init__(self, status_code: int, message: str, body: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class NetDiagRateLimitError(NetDiagApiError):
    """Exception raised when rate limited by the API (HTTP 429)."""

    def __init__(self, retry_after_seconds: int | None = None, body: str | None = None):
        super().__init__(429, "Rate limit exceeded", body)
        self.retry_after_seconds = retry_after_seconds
