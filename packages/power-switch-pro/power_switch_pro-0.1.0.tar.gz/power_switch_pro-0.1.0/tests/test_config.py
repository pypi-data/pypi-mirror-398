"""Tests for configuration management."""

import responses


class TestConfigManager:
    """Test ConfigManager class."""

    @responses.activate
    def test_get_all(self, client, base_url):
        """Test getting all configuration."""
        responses.add(
            responses.GET,
            f"{base_url}config/",
            json={
                "hostname": "testdevice",
                "timezone": "UTC",
                "http_port": 80,
            },
            status=200,
        )

        config = client.config.get_all()
        assert config["hostname"] == "testdevice"
        assert config["timezone"] == "UTC"

    @responses.activate
    def test_get_all_custom_depth(self, client, base_url):
        """Test getting configuration with custom depth."""
        responses.add(
            responses.GET,
            f"{base_url}config/",
            json={"hostname": "testdevice"},
            status=200,
        )

        config = client.config.get_all(depth=1)
        assert "hostname" in config

    @responses.activate
    def test_get(self, client, base_url):
        """Test getting specific configuration value."""
        responses.add(
            responses.GET,
            f"{base_url}config/hostname/",
            json="testdevice",
            status=200,
        )

        hostname = client.config.get("hostname")
        assert hostname == "testdevice"

    @responses.activate
    def test_set(self, client, base_url):
        """Test setting configuration value."""
        responses.add(
            responses.PUT,
            f"{base_url}config/hostname/",
            status=200,
        )

        result = client.config.set("hostname", "newdevice")
        assert result is True

    @responses.activate
    def test_set_boolean(self, client, base_url):
        """Test setting boolean configuration value."""
        responses.add(
            responses.PUT,
            f"{base_url}config/ssh_enabled/",
            status=200,
        )

        result = client.config.set("ssh_enabled", True)
        assert result is True

    @responses.activate
    def test_get_hostname(self, client, base_url):
        """Test getting hostname."""
        responses.add(
            responses.GET,
            f"{base_url}config/hostname/",
            json="mydevice",
            status=200,
        )

        hostname = client.config.get_hostname()
        assert hostname == "mydevice"

    @responses.activate
    def test_set_hostname(self, client, base_url):
        """Test setting hostname."""
        responses.add(
            responses.PUT,
            f"{base_url}config/hostname/",
            status=200,
        )

        result = client.config.set_hostname("newdevice")
        assert result is True

    @responses.activate
    def test_get_timezone(self, client, base_url):
        """Test getting timezone."""
        responses.add(
            responses.GET,
            f"{base_url}config/timezone/",
            json="UTC-5",
            status=200,
        )

        timezone = client.config.get_timezone()
        assert timezone == "UTC-5"

    @responses.activate
    def test_set_timezone(self, client, base_url):
        """Test setting timezone."""
        responses.add(
            responses.PUT,
            f"{base_url}config/timezone/",
            status=200,
        )

        result = client.config.set_timezone("UTC")
        assert result is True

    @responses.activate
    def test_get_http_port(self, client, base_url):
        """Test getting HTTP port."""
        responses.add(
            responses.GET,
            f"{base_url}config/http_port/",
            json=8080,
            status=200,
        )

        port = client.config.get_http_port()
        assert port == 8080

    @responses.activate
    def test_set_http_port(self, client, base_url):
        """Test setting HTTP port."""
        responses.add(
            responses.PUT,
            f"{base_url}config/http_port/",
            status=200,
        )

        result = client.config.set_http_port(8080)
        assert result is True

    @responses.activate
    def test_get_https_port(self, client, base_url):
        """Test getting HTTPS port."""
        responses.add(
            responses.GET,
            f"{base_url}config/https_port/",
            json=8443,
            status=200,
        )

        port = client.config.get_https_port()
        assert port == 8443

    @responses.activate
    def test_set_https_port(self, client, base_url):
        """Test setting HTTPS port."""
        responses.add(
            responses.PUT,
            f"{base_url}config/https_port/",
            status=200,
        )

        result = client.config.set_https_port(8443)
        assert result is True

    @responses.activate
    def test_get_ssh_enabled(self, client, base_url):
        """Test getting SSH enabled status."""
        responses.add(
            responses.GET,
            f"{base_url}config/ssh_enabled/",
            json=True,
            status=200,
        )

        enabled = client.config.get_ssh_enabled()
        assert enabled is True

    @responses.activate
    def test_set_ssh_enabled(self, client, base_url):
        """Test setting SSH enabled status."""
        responses.add(
            responses.PUT,
            f"{base_url}config/ssh_enabled/",
            status=200,
        )

        result = client.config.set_ssh_enabled(False)
        assert result is True

    @responses.activate
    def test_get_ssh_port(self, client, base_url):
        """Test getting SSH port."""
        responses.add(
            responses.GET,
            f"{base_url}config/ssh_port/",
            json=2222,
            status=200,
        )

        port = client.config.get_ssh_port()
        assert port == 2222

    @responses.activate
    def test_set_ssh_port(self, client, base_url):
        """Test setting SSH port."""
        responses.add(
            responses.PUT,
            f"{base_url}config/ssh_port/",
            status=200,
        )

        result = client.config.set_ssh_port(2222)
        assert result is True

    @responses.activate
    def test_allow_plaintext_logins(self, client, base_url):
        """Test allowing plaintext logins."""
        responses.add(
            responses.PUT,
            f"{base_url}config/allow_plaintext_logins/",
            status=200,
        )

        result = client.config.allow_plaintext_logins(True)
        assert result is True

    @responses.activate
    def test_get_refresh_enabled(self, client, base_url):
        """Test getting refresh enabled status."""
        responses.add(
            responses.GET,
            f"{base_url}config/refresh_enabled/",
            json=True,
            status=200,
        )

        enabled = client.config.get_refresh_enabled()
        assert enabled is True

    @responses.activate
    def test_set_refresh_enabled(self, client, base_url):
        """Test setting refresh enabled status."""
        responses.add(
            responses.PUT,
            f"{base_url}config/refresh_enabled/",
            status=200,
        )

        result = client.config.set_refresh_enabled(False)
        assert result is True

    @responses.activate
    def test_get_refresh_delay(self, client, base_url):
        """Test getting refresh delay."""
        responses.add(
            responses.GET,
            f"{base_url}config/refresh_delay_minutes/",
            json=5,
            status=200,
        )

        delay = client.config.get_refresh_delay()
        assert delay == 5

    @responses.activate
    def test_set_refresh_delay(self, client, base_url):
        """Test setting refresh delay."""
        responses.add(
            responses.PUT,
            f"{base_url}config/refresh_delay_minutes/",
            status=200,
        )

        result = client.config.set_refresh_delay(10)
        assert result is True

    @responses.activate
    def test_get_lockout_delay(self, client, base_url):
        """Test getting lockout delay."""
        responses.add(
            responses.GET,
            f"{base_url}config/lockout_delay/",
            json=60,
            status=200,
        )

        delay = client.config.get_lockout_delay()
        assert delay == 60

    @responses.activate
    def test_set_lockout_delay(self, client, base_url):
        """Test setting lockout delay."""
        responses.add(
            responses.PUT,
            f"{base_url}config/lockout_delay/",
            status=200,
        )

        result = client.config.set_lockout_delay(30)
        assert result is True

    @responses.activate
    def test_get_syslog_address(self, client, base_url):
        """Test getting syslog address."""
        responses.add(
            responses.GET,
            f"{base_url}config/syslog_ip_address/",
            json="192.168.1.1",
            status=200,
        )

        address = client.config.get_syslog_address()
        assert address == "192.168.1.1"

    @responses.activate
    def test_set_syslog_address(self, client, base_url):
        """Test setting syslog address."""
        responses.add(
            responses.PUT,
            f"{base_url}config/syslog_ip_address/",
            status=200,
        )

        result = client.config.set_syslog_address("192.168.1.100")
        assert result is True
