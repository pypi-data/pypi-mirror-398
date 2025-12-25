#!/usr/bin/env python3
"""
Device configuration example for Power Switch Pro library.

This example demonstrates:
- Getting device configuration
- Changing hostname
- Configuring network settings
- Adjusting timeout settings
"""

from power_switch_pro import PowerSwitchPro

# Connection parameters
HOST = "192.168.1.100"  # Change to your device IP
USERNAME = "admin"
PASSWORD = "admin"  # Change to your password


def main():
    """Device configuration example."""
    # Create client instance
    print(f"Connecting to Power Switch Pro at {HOST}...")
    switch = PowerSwitchPro(
        host=HOST,
        username=USERNAME,
        password=PASSWORD,
        use_https=True,
        verify_ssl=False,
    )

    if not switch.test_connection():
        print("Failed to connect to device!")
        return

    print("Connected successfully!\n")

    # Get all configuration (depth=2 for more details)
    print("=== Current Configuration ===\n")
    config = switch.config.get_all(depth=2)
    # Print first few config items as example
    print("Sample configuration items:")
    for key, value in list(config.items())[:10]:
        print(f"  {key}: {value}")
    print("  ... (more config items available)")
    print()

    # Get specific configuration values
    print("=== Specific Configuration Values ===\n")

    hostname = switch.config.get_hostname()
    print(f"Hostname: {hostname}")

    timezone = switch.config.get_timezone()
    print(f"Timezone: {timezone}")

    http_port = switch.config.get_http_port()
    print(f"HTTP Port: {http_port}")

    https_port = switch.config.get_https_port()
    print(f"HTTPS Port: {https_port}")

    ssh_enabled = switch.config.get_ssh_enabled()
    print(f"SSH Enabled: {ssh_enabled}")

    if ssh_enabled:
        ssh_port = switch.config.get_ssh_port()
        print(f"SSH Port: {ssh_port}")

    print()

    # Update configuration (examples - commented out for safety)
    print("=== Configuration Updates (Example - Not Executed) ===\n")

    # Change hostname
    # print("Changing hostname...")
    # switch.config.set_hostname("my-power-switch")

    # Change timezone
    # print("Changing timezone...")
    # switch.config.set_timezone("UTC-8")

    # Enable SSH
    # print("Enabling SSH...")
    # switch.config.set_ssh_enabled(True)
    # switch.config.set_ssh_port(2222)

    # Configure refresh settings
    # print("Configuring refresh settings...")
    # switch.config.set_refresh_enabled(True)
    # switch.config.set_refresh_delay(5)  # 5 minutes

    # Configure lockout delay
    # print("Configuring lockout delay...")
    # switch.config.set_lockout_delay(30)  # 30 seconds

    print("To actually change settings, uncomment the relevant lines above.")
    print()

    print("Device configuration example completed!")


if __name__ == "__main__":
    main()
