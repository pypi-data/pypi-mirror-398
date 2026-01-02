"""Integration tests for NetDiagClient against the production API."""

import re
import pytest
from netdiag_client import (
    NetDiagClient,
    NetDiagError,
    CheckRequest,
    Status,
)


@pytest.fixture(scope="module")
def client():
    """Create a client for all tests."""
    with NetDiagClient(api_key="test-key") as c:
        yield c


class TestCheck:
    """Tests for check() method."""

    def test_returns_response_for_valid_hostname(self, client: NetDiagClient):
        result = client.check("google.com")

        assert result is not None
        assert result.target == "google.com"
        assert result.run_id
        assert len(result.locations) > 0

    def test_returns_all_regions(self, client: NetDiagClient):
        result = client.check("google.com")

        regions = [loc.region for loc in result.locations]

        assert "us-west" in regions
        assert "eu-central" in regions
        assert "ap-southeast" in regions

    def test_returns_all_check_types(self, client: NetDiagClient):
        result = client.check("google.com")

        for location in result.locations:
            assert location.ping is not None, f"{location.region} missing ping"
            assert location.dns is not None, f"{location.region} missing dns"
            assert location.tls is not None, f"{location.region} missing tls"
            assert location.http is not None, f"{location.region} missing http"

    def test_normalizes_url_with_https(self, client: NetDiagClient):
        result = client.check("https://google.com/search?q=test")

        assert result.target == "google.com"

    def test_normalizes_url_with_http(self, client: NetDiagClient):
        result = client.check("http://example.com/path")

        assert result.target == "example.com"

    def test_accepts_check_request(self, client: NetDiagClient):
        result = client.check(CheckRequest(
            target="cloudflare.com",
            ping_count=2,
        ))

        assert result is not None
        assert result.target == "cloudflare.com"

    def test_returns_only_specified_region(self, client: NetDiagClient):
        result = client.check(CheckRequest(
            target="google.com",
            regions="us-west",
        ))

        assert len(result.locations) == 1
        assert result.locations[0].region == "us-west"

    def test_raises_for_empty_target(self, client: NetDiagClient):
        with pytest.raises(NetDiagError):
            client.check("")


class TestCheckPrometheus:
    """Tests for check_prometheus() method."""

    def test_returns_prometheus_format(self, client: NetDiagClient):
        result = client.check_prometheus("google.com")

        assert result is not None
        assert len(result) > 0
        assert "netdiag_" in result
        assert "google.com" in result

    def test_accepts_check_request(self, client: NetDiagClient):
        result = client.check_prometheus(CheckRequest(
            target="cloudflare.com",
            regions="eu-central",
        ))

        assert "cloudflare.com" in result
        assert "eu-central" in result


class TestIsHealthy:
    """Tests for is_healthy() method."""

    def test_returns_true_for_healthy_target(self, client: NetDiagClient):
        result = client.is_healthy("google.com")

        assert result is True

    def test_matches_status_from_check(self, client: NetDiagClient):
        response = client.check("cloudflare.com")
        is_healthy = client.is_healthy("cloudflare.com")

        assert is_healthy == (response.status == Status.HEALTHY)


class TestGetStatus:
    """Tests for get_status() method."""

    def test_returns_healthy_for_healthy_target(self, client: NetDiagClient):
        result = client.get_status("google.com")

        assert result == Status.HEALTHY

    def test_returns_valid_status(self, client: NetDiagClient):
        result = client.get_status("github.com")

        assert result in [Status.HEALTHY, Status.WARNING, Status.UNHEALTHY]


class TestResponseModel:
    """Tests for response model parsing."""

    def test_has_valid_timestamps(self, client: NetDiagClient):
        result = client.check("google.com")

        assert result.started_at
        assert result.completed_at

    def test_has_quorum(self, client: NetDiagClient):
        result = client.check("google.com")

        assert result.quorum
        assert re.match(r"\d+/\d+", result.quorum)  # e.g., "3/3"

    def test_has_dns_propagation_status(self, client: NetDiagClient):
        result = client.check("google.com")

        assert result.dns_propagation_status
        assert result.dns_propagation_status in ["consistent", "mismatched", "unknown"]

    def test_ping_result_has_latency(self, client: NetDiagClient):
        result = client.check("google.com")

        ping = result.locations[0].ping
        assert ping is not None
        assert ping.latency_ms is not None
        assert ping.latency_ms > 0
        assert ping.message

    def test_dns_result_has_resolved_addresses(self, client: NetDiagClient):
        result = client.check("google.com")

        dns = result.locations[0].dns
        assert dns is not None
        assert len(dns.resolved_addresses) > 0

    def test_tls_result_has_certificate_info(self, client: NetDiagClient):
        result = client.check("google.com")

        tls = result.locations[0].tls
        assert tls is not None
        assert tls.certificate_valid is True
        assert tls.days_until_expiry is not None
        assert tls.days_until_expiry > 0
        assert tls.subject
        assert tls.issuer

    def test_http_result_has_status_code(self, client: NetDiagClient):
        result = client.check("google.com")

        http = result.locations[0].http
        assert http is not None
        assert http.status_code == 200
        assert http.response_time_ms is not None
        assert http.response_time_ms > 0


class TestConstructor:
    """Tests for client construction."""

    def test_creates_client_with_defaults(self):
        client = NetDiagClient()
        assert client is not None
        client.close()

    def test_creates_client_with_api_key(self):
        client = NetDiagClient(api_key="test-api-key")
        assert client is not None
        client.close()

    def test_creates_client_with_custom_base_url(self):
        client = NetDiagClient(base_url="https://api.netdiag.dev")
        assert client is not None
        client.close()

    def test_works_as_context_manager(self):
        with NetDiagClient() as client:
            assert client is not None
