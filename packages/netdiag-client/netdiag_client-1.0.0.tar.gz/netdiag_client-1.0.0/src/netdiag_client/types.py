"""Type definitions for NetDiag API responses."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Literal


class Status(str, Enum):
    """Health status using traffic light model."""

    HEALTHY = "Healthy"
    WARNING = "Warning"
    UNHEALTHY = "Unhealthy"


class ErrorCode(str, Enum):
    """Error codes for programmatic handling of diagnostic failures."""

    # General (100s)
    NONE = "None"
    UNKNOWN_ERROR = "UnknownError"
    TIMEOUT = "Timeout"

    # Ping (200s)
    PING_NO_RESPONSE = "PingNoResponse"
    PING_ICMP_BLOCKED = "PingIcmpBlocked"
    PING_HOST_UNREACHABLE = "PingHostUnreachable"

    # DNS (300s)
    DNS_NXDOMAIN = "DnsNxDomain"
    DNS_TIMEOUT = "DnsTimeout"
    DNS_SERVER_FAILURE = "DnsServerFailure"
    DNS_NO_RECORDS = "DnsNoRecords"

    # TLS (400s)
    TLS_CONNECTION_FAILED = "TlsConnectionFailed"
    TLS_CERTIFICATE_EXPIRED = "TlsCertificateExpired"
    TLS_HANDSHAKE_FAILED = "TlsHandshakeFailed"

    # HTTP (500s)
    HTTP_CONNECTION_FAILED = "HttpConnectionFailed"
    HTTP_TIMEOUT = "HttpTimeout"
    HTTP_CONNECTION_REFUSED = "HttpConnectionRefused"


@dataclass
class ErrorInfo:
    """Structured error information with code and message."""

    code: ErrorCode
    message: str
    details: str | None = None


@dataclass
class CheckRequest:
    """Request parameters for multi-region network diagnostics."""

    target: str
    """Target hostname or IP address to diagnose."""

    port: int | None = None
    """Optional TCP port number for TLS/HTTP checks (80, 443, 8080, 8443)."""

    ping_count: int | None = None
    """Number of ICMP ping packets to send (1-100). Defaults to 4."""

    ping_timeout: int | None = None
    """Timeout in seconds for each ping attempt (1-30). Defaults to 5."""

    dns: str | None = None
    """Optional custom DNS server to use for resolution."""

    regions: str | None = None
    """Comma-separated list of region codes to run checks from."""


@dataclass
class PingResult:
    """ICMP ping result containing latency and reachability information."""

    status: Status
    latency_ms: float | None
    min_rtt_ms: float | None
    max_rtt_ms: float | None
    packet_loss_percent: float | None
    message: str
    error: ErrorInfo | None = None
    tcp_fallback_used: bool = False


@dataclass
class DnsResult:
    """DNS resolution result containing resolved IP addresses."""

    status: Status
    resolved_addresses: list[str]
    message: str
    error: ErrorInfo | None = None


@dataclass
class TlsResult:
    """TLS/SSL certificate validation result."""

    status: Status
    certificate_valid: bool
    days_until_expiry: int | None
    expires_at: str | None
    subject: str | None
    issuer: str | None
    protocol: str | None
    message: str
    error: ErrorInfo | None = None


@dataclass
class HttpResult:
    """HTTP/HTTPS request result containing response status and performance metrics."""

    status: Status
    status_code: int | None
    reason_phrase: str | None
    response_time_ms: int | None
    message: str
    error: ErrorInfo | None = None


@dataclass
class LocationResult:
    """Diagnostics results from a specific geographic location/region."""

    region: str
    status: Status
    ping: PingResult | None
    dns: DnsResult | None
    tls: TlsResult | None
    http: HttpResult | None


@dataclass
class CheckResponse:
    """Complete diagnostics response containing results from all network checks."""

    run_id: str
    target: str
    status: Status
    quorum: str
    dns_propagation_status: str
    started_at: str
    completed_at: str
    locations: list[LocationResult]
