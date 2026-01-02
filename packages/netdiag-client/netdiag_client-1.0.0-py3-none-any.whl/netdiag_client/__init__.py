"""
NetDiag - Official Python client for NetDiag API.

Network diagnostics (HTTP, DNS, TLS, ping) as a service.
Run distributed health checks from multiple regions worldwide.
"""

from .client import NetDiagClient
from .types import (
    Status,
    ErrorCode,
    ErrorInfo,
    CheckRequest,
    CheckResponse,
    LocationResult,
    PingResult,
    DnsResult,
    TlsResult,
    HttpResult,
)
from .errors import (
    NetDiagError,
    NetDiagApiError,
    NetDiagRateLimitError,
)

__version__ = "1.0.0"

__all__ = [
    # Client
    "NetDiagClient",
    # Types
    "Status",
    "ErrorCode",
    "ErrorInfo",
    "CheckRequest",
    "CheckResponse",
    "LocationResult",
    "PingResult",
    "DnsResult",
    "TlsResult",
    "HttpResult",
    # Errors
    "NetDiagError",
    "NetDiagApiError",
    "NetDiagRateLimitError",
]
