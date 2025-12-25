"""Configuration management for Power Switch Pro."""

from typing import Any, Dict


class ConfigManager:
    """Manager for device configuration."""

    def __init__(self, client):
        """
        Initialize config manager.

        Args:
            client: PowerSwitchPro client instance
        """
        self.client = client

    def get_all(self, depth: int = 2) -> Dict[str, Any]:
        """
        Get all configuration.

        Args:
            depth: Depth limit for response (default: 2)

        Returns:
            Configuration dictionary
        """
        path = "config/"
        response = self.client.get(path, headers={"Range": f"dli-depth={depth}"})
        result: Dict[str, Any] = response.json()
        return result

    def get(self, key: str) -> Any:
        """
        Get specific configuration value.

        Args:
            key: Configuration key

        Returns:
            Configuration value
        """
        path = f"config/{key}/"
        response = self.client.get(path)
        return response.json()

    def set(self, key: str, value: Any) -> bool:
        """
        Set configuration value.

        Args:
            key: Configuration key
            value: New value

        Returns:
            True if successful
        """
        path = f"config/{key}/"
        if isinstance(value, bool):
            value = str(value).lower()
        response = self.client.put(path, data={"value": value})
        return response.status_code in (200, 204)

    def get_hostname(self) -> str:
        """Get device hostname."""
        return str(self.get("hostname"))

    def set_hostname(self, hostname: str) -> bool:
        """Set device hostname."""
        return self.set("hostname", hostname)

    def get_timezone(self) -> str:
        """Get device timezone."""
        return str(self.get("timezone"))

    def set_timezone(self, timezone: str) -> bool:
        """
        Set device timezone.

        Args:
            timezone: Timezone string (e.g., "UTC", "UTC-5")

        Returns:
            True if successful
        """
        return self.set("timezone", timezone)

    def get_http_port(self) -> int:
        """Get HTTP port."""
        return int(self.get("http_port"))

    def set_http_port(self, port: int) -> bool:
        """Set HTTP port."""
        return self.set("http_port", port)

    def get_https_port(self) -> int:
        """Get HTTPS port."""
        return int(self.get("https_port"))

    def set_https_port(self, port: int) -> bool:
        """Set HTTPS port."""
        return self.set("https_port", port)

    def get_ssh_enabled(self) -> bool:
        """Get SSH enabled status."""
        return bool(self.get("ssh_enabled"))

    def set_ssh_enabled(self, enabled: bool) -> bool:
        """Set SSH enabled status."""
        return self.set("ssh_enabled", enabled)

    def get_ssh_port(self) -> int:
        """Get SSH port."""
        return int(self.get("ssh_port"))

    def set_ssh_port(self, port: int) -> bool:
        """Set SSH port."""
        return self.set("ssh_port", port)

    def allow_plaintext_logins(self, allow: bool) -> bool:
        """
        Allow/disallow plaintext (Basic auth) logins.

        Args:
            allow: Whether to allow plaintext logins

        Returns:
            True if successful
        """
        return self.set("allow_plaintext_logins", allow)

    def get_refresh_enabled(self) -> bool:
        """Get web UI auto-refresh status."""
        return bool(self.get("refresh_enabled"))

    def set_refresh_enabled(self, enabled: bool) -> bool:
        """Set web UI auto-refresh status."""
        return self.set("refresh_enabled", enabled)

    def get_refresh_delay(self) -> int:
        """Get web UI refresh delay in minutes."""
        return int(self.get("refresh_delay_minutes"))

    def set_refresh_delay(self, minutes: int) -> bool:
        """Set web UI refresh delay in minutes."""
        return self.set("refresh_delay_minutes", minutes)

    def get_lockout_delay(self) -> int:
        """Get failed login lockout delay in seconds."""
        return int(self.get("lockout_delay"))

    def set_lockout_delay(self, seconds: int) -> bool:
        """Set failed login lockout delay in seconds."""
        return self.set("lockout_delay", seconds)

    def get_syslog_address(self) -> str:
        """Get syslog server IP address."""
        return str(self.get("syslog_ip_address"))

    def set_syslog_address(self, address: str) -> bool:
        """Set syslog server IP address."""
        return self.set("syslog_ip_address", address)
