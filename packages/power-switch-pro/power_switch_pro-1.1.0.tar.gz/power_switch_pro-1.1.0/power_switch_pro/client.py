"""Main client class for Power Switch Pro device."""

import http.client
from typing import Any, Dict, Optional, Union
from urllib.parse import urljoin

import requests
from requests.auth import HTTPDigestAuth

from .auth import AuthManager
from .autoping import AutoPingManager
from .config import ConfigManager
from .exceptions import (
    APIError,
    AuthenticationError,
    ConflictError,
    ConnectionError,
    ResourceNotFoundError,
)
from .meters import MeterManager
from .outlets import OutletManager
from .script import ScriptManager


class PowerSwitchPro:
    """
    Main client for interacting with Digital Loggers Power Switch Pro device.

    This class provides a high-level interface to the REST API.
    """

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        use_https: bool = False,
        verify_ssl: bool = True,
        port: Optional[int] = None,
    ):
        """
        Initialize Power Switch Pro client.

        Args:
            host: Device IP address or hostname
            username: Admin username
            password: Admin password
            use_https: Use HTTPS instead of HTTP (default: False)
            verify_ssl: Verify SSL certificates (default: True)
            port: Custom port number (optional)
        """
        # Increase HTTP header limit to handle Power Switch Pro devices
        # Some devices return >100 headers in certain responses (e.g., /config/ endpoint)
        http.client._MAXHEADERS = 200

        self.host = host
        self.username = username
        self.password = password
        self.use_https = use_https
        self.verify_ssl = verify_ssl

        # Determine port
        if port:
            self.port = port
        else:
            self.port = 443 if use_https else 80

        # Build base URL
        protocol = "https" if use_https else "http"
        if (use_https and self.port == 443) or (not use_https and self.port == 80):
            self.base_url = f"{protocol}://{host}/restapi/"
        else:
            self.base_url = f"{protocol}://{host}:{self.port}/restapi/"

        # Setup authentication
        self.auth = HTTPDigestAuth(username, password)

        # Setup session
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.verify = verify_ssl

        # Initialize managers
        self.outlets = OutletManager(self)
        self.auth_manager = AuthManager(self)
        self.config = ConfigManager(self)
        self.meters = MeterManager(self)
        self.autoping = AutoPingManager(self)
        self.script = ScriptManager(self)

    def _make_url(self, path: str) -> str:
        """
        Construct full URL from path.

        Args:
            path: API path (should end with /)

        Returns:
            Full URL
        """
        if not path.endswith("/"):
            path += "/"
        return urljoin(self.base_url, path)

    def _request(
        self,
        method: str,
        path: str,
        data: Optional[Union[Dict, str]] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
    ) -> requests.Response:
        """
        Make HTTP request to device.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            path: API path
            data: Request body data (form-encoded)
            params: URL parameters
            headers: Additional headers
            json_data: JSON request body

        Returns:
            Response object

        Raises:
            ConnectionError: If connection fails
            AuthenticationError: If authentication fails
            APIError: If API returns error
        """
        url = self._make_url(path)

        # Add CSRF protection header for state-modifying operations
        if method in ("POST", "PUT", "PATCH", "DELETE"):
            if headers is None:
                headers = {}
            headers["X-CSRF"] = "x"

        # Set Accept header to prefer JSON
        if headers is None:
            headers = {}
        if "Accept" not in headers:
            headers["Accept"] = "application/json"

        try:
            response = self.session.request(
                method=method,
                url=url,
                data=data,
                params=params,
                headers=headers,
                json=json_data,
                timeout=30,
            )

            # Handle HTTP errors
            if response.status_code == 401:
                raise AuthenticationError("Authentication failed")
            elif response.status_code == 404:
                raise ResourceNotFoundError(
                    f"Resource not found: {path}",
                    status_code=404,
                    response=response,
                )
            elif response.status_code == 409:
                raise ConflictError(
                    f"Conflict: {response.text}",
                    status_code=409,
                    response=response,
                )
            elif response.status_code >= 400:
                raise APIError(
                    f"API error: {response.status_code} - {response.text}",
                    status_code=response.status_code,
                    response=response,
                )

            return response

        except requests.exceptions.Timeout as e:
            raise ConnectionError(f"Connection timeout to {self.host}") from e
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(f"Failed to connect to {self.host}: {e}") from e
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {e}") from e

    def get(
        self,
        path: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> requests.Response:
        """Make GET request."""
        return self._request("GET", path, params=params, headers=headers)

    def post(
        self,
        path: str,
        data: Optional[Union[Dict, str]] = None,
        json_data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> requests.Response:
        """Make POST request."""
        return self._request(
            "POST", path, data=data, json_data=json_data, headers=headers
        )

    def put(
        self,
        path: str,
        data: Optional[Union[Dict, str]] = None,
        json_data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> requests.Response:
        """Make PUT request."""
        return self._request(
            "PUT", path, data=data, json_data=json_data, headers=headers
        )

    def patch(
        self,
        path: str,
        data: Optional[Union[Dict, str]] = None,
        json_data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> requests.Response:
        """Make PATCH request."""
        return self._request(
            "PATCH", path, data=data, json_data=json_data, headers=headers
        )

    def delete(
        self,
        path: str,
        headers: Optional[Dict] = None,
    ) -> requests.Response:
        """Make DELETE request."""
        return self._request("DELETE", path, headers=headers)

    @property
    def info(self) -> Dict[str, Any]:
        """
        Get device information.

        Returns:
            Dictionary with device info (serial, version, hostname, etc.)
        """
        response = self.get("config/", headers={"Range": "dli-depth=1"})
        data = response.json()

        # Extract relevant info and resolve $ref references
        info = {}
        for key in ["serial", "version", "hostname", "hardware_id"]:
            if key in data:
                value = data[key]
                # Resolve $ref if present
                if isinstance(value, dict) and "$ref" in value:
                    try:
                        ref_path = value["$ref"]
                        ref_response = self.get(f"config/{ref_path}")
                        info[key] = ref_response.json()
                    except Exception:
                        # If reference resolution fails, keep the reference
                        info[key] = value
                else:
                    info[key] = value

        return info

    def test_connection(self) -> bool:
        """
        Test connection to device.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.get("", headers={"Range": "dli-depth=0"})
            return True
        except Exception:
            return False
