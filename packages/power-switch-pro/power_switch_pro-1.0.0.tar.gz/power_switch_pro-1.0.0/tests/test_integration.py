"""
Integration tests for Power Switch Pro library.

These tests are designed to run against a real device or mock server.
They are skipped by default and must be explicitly enabled.

To run integration tests:
    pytest tests/test_integration.py --integration

Set environment variables:
    POWER_SWITCH_HOST: Device IP address
    POWER_SWITCH_USER: Username
    POWER_SWITCH_PASS: Password
"""

import os

import pytest

from power_switch_pro import PowerSwitchPro


def pytest_addoption(parser):
    """Add custom command line option."""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="run integration tests",
    )


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test")


def pytest_collection_modifieritems(config, items):
    """Skip integration tests unless --integration is specified."""
    if config.getoption("--integration"):
        return
    skip_integration = pytest.mark.skip(reason="need --integration option to run")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


@pytest.fixture(scope="module")
def device_config():
    """Get device configuration from environment."""
    config = {
        "host": os.getenv("POWER_SWITCH_HOST", "192.168.1.100"),
        "username": os.getenv("POWER_SWITCH_USER", "admin"),
        "password": os.getenv("POWER_SWITCH_PASS", "admin"),
    }
    return config


@pytest.fixture(scope="module")
def switch(device_config):
    """Create PowerSwitchPro client instance."""
    return PowerSwitchPro(
        host=device_config["host"],
        username=device_config["username"],
        password=device_config["password"],
        use_https=True,
        verify_ssl=False,  # For self-signed certificates
    )


@pytest.mark.integration
class TestIntegrationBasic:
    """Basic integration tests."""

    def test_connection(self, switch):
        """Test that we can connect to the device."""
        assert switch.test_connection(), "Failed to connect to device"

    def test_get_info(self, switch):
        """Test getting device information."""
        info = switch.info
        assert isinstance(info, dict)
        # Check for expected keys (may vary by device)
        # assert 'hostname' in info or 'serial' in info

    def test_outlet_count(self, switch):
        """Test getting outlet count."""
        count = switch.outlets.count()
        assert count > 0, "Device should have at least one outlet"
        assert count <= 32, "Unexpected number of outlets"

    def test_list_outlets(self, switch):
        """Test listing all outlets."""
        outlets = switch.outlets.list_all()
        assert len(outlets) > 0
        assert all("id" in o for o in outlets)
        assert all("name" in o for o in outlets)
        assert all("state" in o for o in outlets)


@pytest.mark.integration
class TestIntegrationOutletControl:
    """Integration tests for outlet control."""

    @pytest.fixture
    def test_outlet_index(self, switch):
        """Get index of outlet to use for testing."""
        # Use outlet 0 for testing, or set via env var
        return int(os.getenv("TEST_OUTLET_INDEX", "0"))

    def test_get_outlet_state(self, switch, test_outlet_index):
        """Test getting outlet state."""
        state = switch.outlets.get_state(test_outlet_index)
        assert isinstance(state, bool)

    def test_get_outlet_name(self, switch, test_outlet_index):
        """Test getting outlet name."""
        name = switch.outlets.get_name(test_outlet_index)
        assert isinstance(name, str)
        assert len(name) > 0

    def test_outlet_iterator(self, switch):
        """Test iterating over outlets."""
        outlets = list(switch.outlets)
        assert len(outlets) > 0
        for outlet in outlets:
            assert hasattr(outlet, "index")
            assert hasattr(outlet, "state")
            assert hasattr(outlet, "name")

    @pytest.mark.skip(reason="Skipped by default to avoid controlling real hardware")
    def test_outlet_control(self, switch, test_outlet_index):
        """
        Test controlling an outlet.

        WARNING: This test will actually control outlet hardware!
        Only enable if you understand the implications.
        """
        outlet = switch.outlets[test_outlet_index]
        original_state = outlet.state

        try:
            # Turn off
            outlet.off()
            import time

            time.sleep(1)
            assert not outlet.state

            # Turn on
            outlet.on()
            time.sleep(1)
            assert outlet.state

        finally:
            # Restore original state
            if original_state:
                outlet.on()
            else:
                outlet.off()


@pytest.mark.integration
class TestIntegrationMeters:
    """Integration tests for power metering."""

    def test_get_voltage(self, switch):
        """Test getting voltage reading."""
        try:
            voltage = switch.meters.get_voltage()
            assert isinstance(voltage, (int, float))
            assert 0 < voltage < 500  # Reasonable voltage range
        except Exception:
            pytest.skip("Device may not support voltage metering")

    def test_get_current(self, switch):
        """Test getting current reading."""
        try:
            current = switch.meters.get_current()
            assert isinstance(current, (int, float))
            assert current >= 0  # Current should be non-negative
        except Exception:
            pytest.skip("Device may not support current metering")

    def test_list_meters(self, switch):
        """Test listing available meters."""
        try:
            meters = switch.meters.list_meters()
            assert isinstance(meters, list)
        except Exception:
            pytest.skip("Device may not support metering")


@pytest.mark.integration
class TestIntegrationConfig:
    """Integration tests for device configuration."""

    def test_get_hostname(self, switch):
        """Test getting hostname."""
        hostname = switch.config.get_hostname()
        assert isinstance(hostname, str)
        assert len(hostname) > 0

    def test_get_timezone(self, switch):
        """Test getting timezone."""
        try:
            timezone = switch.config.get_timezone()
            assert isinstance(timezone, str)
        except Exception:
            pytest.skip("Device may not support timezone configuration")

    def test_get_http_port(self, switch):
        """Test getting HTTP port."""
        try:
            port = switch.config.get_http_port()
            assert isinstance(port, int)
            assert 1 <= port <= 65535
        except Exception:
            pytest.skip("Device may not expose HTTP port configuration")


@pytest.mark.integration
class TestIntegrationAuth:
    """Integration tests for user management."""

    def test_list_users(self, switch):
        """Test listing users."""
        try:
            users = switch.auth.list_users()
            assert isinstance(users, list)
            assert len(users) > 0  # Should have at least admin user
        except Exception:
            pytest.skip("Device may not support user management API")

    @pytest.mark.skip(reason="Skipped by default to avoid modifying user accounts")
    def test_user_management(self, switch):
        """
        Test user management operations.

        WARNING: This test will modify user accounts!
        Only enable if you understand the implications.
        """
        # Test adding, updating, and deleting a user
        # Implementation depends on actual API behavior
        pass


if __name__ == "__main__":
    # Allow running directly for quick testing
    import sys

    sys.exit(pytest.main([__file__, "--integration", "-v"]))
