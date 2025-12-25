#!/usr/bin/env python3
"""
Basic usage example for Power Switch Pro library.

This example demonstrates:
- Connecting to the device
- Getting device information
- Controlling outlets (on/off)
- Reading outlet states
"""

from power_switch_pro import PowerSwitchPro

# Connection parameters
HOST = "192.168.1.100"  # Change to your device IP
USERNAME = "admin"
PASSWORD = "admin"  # Change to your password


def main():
    """Basic usage example."""
    # Create client instance
    print(f"Connecting to Power Switch Pro at {HOST}...")
    switch = PowerSwitchPro(
        host=HOST,
        username=USERNAME,
        password=PASSWORD,
        use_https=True,
        verify_ssl=False,  # Set to True in production with valid certificate
    )

    # Test connection
    if not switch.test_connection():
        print("Failed to connect to device!")
        return

    print("Connected successfully!\n")

    # Get device information
    info = switch.info
    print("Device Information:")
    print(f"  Hostname: {info.get('hostname', 'N/A')}")
    print(f"  Serial: {info.get('serial', 'N/A')}")
    print(f"  Version: {info.get('version', 'N/A')}")
    print()

    # List all outlets
    print("Outlet Status:")
    for outlet in switch.outlets:
        state = "ON" if outlet.state else "OFF"
        print(f"  Outlet {outlet.index}: {outlet.name} - {state}")
    print()

    # Control specific outlet
    outlet_num = 0
    print(f"Controlling outlet {outlet_num}...")

    # Get outlet reference
    outlet = switch.outlets[outlet_num]

    # Turn off
    print(f"  Turning OFF outlet {outlet_num}...")
    outlet.off()

    # Wait a moment and check state
    import time

    time.sleep(1)
    print(f"  Current state: {'ON' if outlet.state else 'OFF'}")

    # Turn on
    print(f"  Turning ON outlet {outlet_num}...")
    outlet.on()
    time.sleep(1)
    print(f"  Current state: {'ON' if outlet.state else 'OFF'}")

    # Cycle (turn off, wait, turn on)
    print(f"  Cycling outlet {outlet_num}...")
    outlet.cycle()
    time.sleep(3)  # Wait for cycle to complete
    print(f"  Current state: {'ON' if outlet.state else 'OFF'}")

    print("\nExample completed successfully!")


if __name__ == "__main__":
    main()
