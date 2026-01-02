# netdiag-client

Official Python client for [NetDiag API](https://netdiag.dev) - network diagnostics (HTTP, DNS, TLS, ping) as a service. Run distributed health checks from multiple regions worldwide.

## Installation

```bash
pip install netdiag-client
```

## Quick Start

```python
from netdiag_client import NetDiagClient

client = NetDiagClient()

# Run a full diagnostic check
result = client.check("example.com")

print(f"Status: {result.status}")           # Status.HEALTHY, Status.WARNING, or Status.UNHEALTHY
print(f"Quorum: {result.quorum}")           # e.g., "3/4" (3 of 4 regions healthy)
print(f"DNS: {result.dns_propagation_status}")  # "consistent" or "mismatched"

# Inspect per-region results
for location in result.locations:
    print(f"{location.region}: {location.status}")
    if location.ping:
        print(f"  Ping: {location.ping.latency_ms}ms")
    if location.http:
        print(f"  HTTP: {location.http.status_code}")
```

## API Reference

### Constructor

```python
# Default configuration
client = NetDiagClient()

# With API key (increases rate limits)
client = NetDiagClient(api_key="your-api-key")

# Full options
client = NetDiagClient(
    base_url="https://api.netdiag.dev",  # API base URL
    api_key="your-api-key",              # API key for authentication
    timeout=30.0,                         # Request timeout in seconds
)
```

### Context Manager

```python
with NetDiagClient() as client:
    result = client.check("example.com")
    print(result.status)
# Client is automatically closed
```

### Methods

#### `check(target) -> CheckResponse`

Run network diagnostics against a target.

```python
# Simple usage
result = client.check("example.com")

# URLs are accepted (host is extracted automatically)
result = client.check("https://example.com/path")

# With options
from netdiag_client import CheckRequest

result = client.check(CheckRequest(
    target="example.com",
    port=443,
    regions="us-west,eu-central",
    ping_count=10,
    ping_timeout=5,
    dns="8.8.8.8",
))
```

#### `check_prometheus(target) -> str`

Run diagnostics and get results in Prometheus exposition format.

```python
metrics = client.check_prometheus("example.com")
# Returns Prometheus-formatted metrics
```

#### `is_healthy(target) -> bool`

Quick check if a target is healthy.

```python
if client.is_healthy("example.com"):
    print("All systems operational")
```

#### `get_status(target) -> Status`

Get the health status of a target.

```python
from netdiag_client import Status

status = client.get_status("example.com")
if status == Status.HEALTHY:
    print("Target is healthy")
```

## Error Handling

```python
from netdiag_client import (
    NetDiagClient,
    NetDiagApiError,
    NetDiagRateLimitError,
)

client = NetDiagClient()

try:
    result = client.check("example.com")
except NetDiagRateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after_seconds}s")
except NetDiagApiError as e:
    print(f"API error: {e.status_code} - {e}")
```

## Type Hints

Full type hints included for IDE support:

```python
from netdiag_client import (
    CheckRequest,
    CheckResponse,
    LocationResult,
    Status,
)
```

## Requirements

- Python 3.10+
- httpx

## Documentation

Full documentation available at [netdiag.dev/docs/python](https://netdiag.dev/docs/python)

## License

MIT
