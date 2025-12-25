"""Pytest configuration and fixtures."""

import pytest
import responses

from power_switch_pro import PowerSwitchPro


@pytest.fixture
def mock_host():
    """Return test host address."""
    return "192.168.0.100"


@pytest.fixture
def mock_credentials():
    """Return test credentials."""
    return {"username": "admin", "password": "1234"}


@pytest.fixture
def client(mock_host, mock_credentials):
    """Return PowerSwitchPro client instance."""
    return PowerSwitchPro(
        host=mock_host,
        username=mock_credentials["username"],
        password=mock_credentials["password"],
    )


@pytest.fixture
def base_url(mock_host):
    """Return base API URL."""
    return f"http://{mock_host}/restapi/"


@pytest.fixture
def mock_responses():
    """Return responses mock."""
    with responses.RequestsMock() as rsps:
        yield rsps
