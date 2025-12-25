"""Tests for PowerSwitchPro client."""

import pytest
import responses
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import Timeout

from power_switch_pro import PowerSwitchPro
from power_switch_pro.exceptions import (
    APIError,
    AuthenticationError,
    ConflictError,
    ConnectionError,
    ResourceNotFoundError,
)


class TestPowerSwitchProInit:
    """Test PowerSwitchPro initialization."""

    def test_init_default_http(self):
        """Test initialization with default HTTP settings."""
        client = PowerSwitchPro("192.168.0.100", "admin", "1234")
        assert client.host == "192.168.0.100"
        assert client.username == "admin"
        assert client.password == "1234"
        assert client.use_https is False
        assert client.port == 80
        assert client.base_url == "http://192.168.0.100/restapi/"

    def test_init_with_https(self):
        """Test initialization with HTTPS."""
        client = PowerSwitchPro("192.168.0.100", "admin", "1234", use_https=True)
        assert client.use_https is True
        assert client.port == 443
        assert client.base_url == "https://192.168.0.100/restapi/"

    def test_init_with_custom_port(self):
        """Test initialization with custom port."""
        client = PowerSwitchPro("192.168.0.100", "admin", "1234", port=8080)
        assert client.port == 8080
        assert client.base_url == "http://192.168.0.100:8080/restapi/"


class TestPowerSwitchProRequests:
    """Test HTTP request methods."""

    @responses.activate
    def test_get_request(self, client, base_url):
        """Test GET request."""
        responses.add(
            responses.GET,
            f"{base_url}test/",
            json={"result": "success"},
            status=200,
        )

        response = client.get("test/")
        assert response.status_code == 200
        assert response.json() == {"result": "success"}

    @responses.activate
    def test_post_request(self, client, base_url):
        """Test POST request."""
        responses.add(
            responses.POST,
            f"{base_url}test/",
            json={"result": "created"},
            status=201,
        )

        response = client.post("test/", data={"key": "value"})
        assert response.status_code == 201

    @responses.activate
    def test_put_request(self, client, base_url):
        """Test PUT request."""
        responses.add(responses.PUT, f"{base_url}test/", json={}, status=200)

        response = client.put("test/", data={"key": "value"})
        assert response.status_code == 200

    @responses.activate
    def test_patch_request(self, client, base_url):
        """Test PATCH request."""
        responses.add(responses.PATCH, f"{base_url}test/", json={}, status=200)

        response = client.patch("test/", data={"key": "value"})
        assert response.status_code == 200

    @responses.activate
    def test_delete_request(self, client, base_url):
        """Test DELETE request."""
        responses.add(responses.DELETE, f"{base_url}test/", status=204)

        response = client.delete("test/")
        assert response.status_code == 204

    @responses.activate
    def test_csrf_header_added(self, client, base_url):
        """Test that CSRF header is added to state-modifying requests."""
        responses.add(responses.POST, f"{base_url}test/", json={}, status=200)

        client.post("test/")
        assert len(responses.calls) == 1
        assert "X-CSRF" in responses.calls[0].request.headers


class TestPowerSwitchProErrors:
    """Test error handling."""

    @responses.activate
    def test_authentication_error(self, client, base_url):
        """Test authentication error handling."""
        responses.add(responses.GET, f"{base_url}test/", status=401)

        with pytest.raises(AuthenticationError):
            client.get("test/")

    @responses.activate
    def test_resource_not_found(self, client, base_url):
        """Test 404 error handling."""
        responses.add(responses.GET, f"{base_url}test/", status=404)

        with pytest.raises(ResourceNotFoundError):
            client.get("test/")

    @responses.activate
    def test_conflict_error(self, client, base_url):
        """Test 409 conflict error handling."""
        responses.add(responses.PUT, f"{base_url}test/", status=409)

        with pytest.raises(ConflictError):
            client.put("test/", data={})

    @responses.activate
    def test_general_api_error(self, client, base_url):
        """Test general API error handling."""
        responses.add(responses.GET, f"{base_url}test/", status=500)

        with pytest.raises(APIError):
            client.get("test/")

    @responses.activate
    def test_timeout_error(self, client, base_url):
        """Test timeout error handling."""
        responses.add(
            responses.GET,
            f"{base_url}test/",
            body=Timeout("Connection timeout"),
        )

        with pytest.raises(ConnectionError):
            client.get("test/")

    @responses.activate
    def test_connection_error(self, client, base_url):
        """Test connection error handling."""
        responses.add(
            responses.GET,
            f"{base_url}test/",
            body=RequestsConnectionError("Connection failed"),
        )

        with pytest.raises(ConnectionError):
            client.get("test/")


class TestPowerSwitchProInfo:
    """Test device info methods."""

    @responses.activate
    def test_get_info(self, client, base_url):
        """Test getting device info."""
        responses.add(
            responses.GET,
            f"{base_url}config/",
            json={
                "serial": "TEST123",
                "version": "1.2.3",
                "hostname": "testdevice",
                "hardware_id": "HW001",
            },
            status=200,
        )

        info = client.info
        assert info["serial"] == "TEST123"
        assert info["version"] == "1.2.3"
        assert info["hostname"] == "testdevice"

    @responses.activate
    def test_test_connection_success(self, client, base_url):
        """Test successful connection test."""
        # test_connection() calls get("") which urljoin resolves to root
        responses.add(responses.GET, "http://192.168.0.100/", json={}, status=200)

        assert client.test_connection() is True

    @responses.activate
    def test_test_connection_failure(self, client, base_url):
        """Test failed connection test."""
        responses.add(responses.GET, f"{base_url}", status=500)

        assert client.test_connection() is False


class TestPowerSwitchProURLConstruction:
    """Test URL construction."""

    def test_make_url_adds_trailing_slash(self, client):
        """Test that trailing slash is added."""
        url = client._make_url("test")
        assert url.endswith("/")

    def test_make_url_preserves_trailing_slash(self, client):
        """Test that existing trailing slash is preserved."""
        url = client._make_url("test/")
        assert url.endswith("/")
        assert url.count("/restapi/") == 1
