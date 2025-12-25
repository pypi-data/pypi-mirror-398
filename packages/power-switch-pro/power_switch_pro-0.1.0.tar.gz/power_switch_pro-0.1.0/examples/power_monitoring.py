#!/usr/bin/env python3
"""
Power monitoring example for Power Switch Pro library.

This example demonstrates:
- Reading voltage, current, and power measurements
- Getting power factor readings
- Monitoring energy consumption
- Displaying real-time power statistics
"""

from power_switch_pro import PowerSwitchPro

# Connection parameters
HOST = "192.168.1.100"  # Change to your device IP
USERNAME = "admin"
PASSWORD = "admin"  # Change to your password


def main():
    """Power monitoring example."""
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

    # Get all meter values
    print("=== Power Monitoring ===\n")

    try:
        # Get voltage reading
        voltage = switch.meters.get_voltage()
        print(f"Voltage: {voltage:.2f} V")

        # Get current reading
        current = switch.meters.get_current()
        print(f"Current: {current:.2f} A")

        # Get power reading
        power = switch.meters.get_power()
        print(f"Power: {power:.2f} W")

        # Get total energy consumed
        energy = switch.meters.get_total_energy()
        print(f"Total Energy: {energy:.2f} kWh")

        print()

        # Get all available meter values
        print("=== All Meter Values ===\n")
        meters = switch.meters.get_all_values()
        for meter in meters:
            print(f"  {meter['name']}: {meter['value']}")

        print()

        # Monitor power for specific bus
        print("=== Bus 0 Detailed Readings ===\n")
        bus_values = switch.meters.get_bus_values(bus=0)
        for name, value in bus_values.items():
            print(f"  {name}: {value}")

    except Exception as e:
        print(f"Error reading meters: {e}")
        print("Note: Not all devices support all meter types")

    print("\nMonitoring example completed!")


if __name__ == "__main__":
    main()
