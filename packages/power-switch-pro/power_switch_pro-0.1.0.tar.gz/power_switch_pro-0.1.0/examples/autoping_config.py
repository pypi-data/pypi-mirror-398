#!/usr/bin/env python3
"""
AutoPing configuration example for Power Switch Pro library.

This example demonstrates:
- Listing AutoPing entries
- Adding new AutoPing entries
- Updating AutoPing settings
- Enabling/disabling AutoPing entries
- Deleting AutoPing entries
"""

from power_switch_pro import PowerSwitchPro

# Connection parameters
HOST = "192.168.1.100"  # Change to your device IP
USERNAME = "admin"
PASSWORD = "admin"  # Change to your password


def main():
    """AutoPing configuration example."""
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

    # List existing AutoPing entries
    print("=== Current AutoPing Entries ===\n")
    entries = switch.autoping.list_entries()
    if entries:
        for i, entry in enumerate(entries):
            print(f"Entry {i}:")
            print(f"  Host: {entry.get('host', 'N/A')}")
            print(f"  Outlet: {entry.get('outlet', 'N/A')}")
            print(f"  Enabled: {entry.get('enabled', 'N/A')}")
            print(f"  Interval: {entry.get('interval', 'N/A')}s")
            print(f"  Retries: {entry.get('retries', 'N/A')}")
            print()
    else:
        print("No AutoPing entries configured\n")

    # Add a new AutoPing entry
    print("=== Adding New AutoPing Entry ===\n")
    new_entry = switch.autoping.add_entry(
        host="192.168.1.50",  # Host to monitor
        outlet=0,  # Outlet to control
        enabled=True,
        interval=60,  # Ping every 60 seconds
        retries=3,  # Retry 3 times before action
    )
    print(f"Added entry: {new_entry}")
    print()

    # Get specific entry
    print("=== Getting Specific Entry ===\n")
    entry_id = 0
    entry = switch.autoping.get_entry(entry_id)
    print(f"Entry {entry_id}: {entry}")
    print()

    # Update an entry
    print("=== Updating Entry ===\n")
    success = switch.autoping.update_entry(entry_id, interval=120, retries=5)
    print(f"Update {'succeeded' if success else 'failed'}")
    print()

    # Disable an entry
    print("=== Disabling Entry ===\n")
    success = switch.autoping.disable_entry(entry_id)
    print(f"Disable {'succeeded' if success else 'failed'}")
    print()

    # Re-enable an entry
    print("=== Enabling Entry ===\n")
    success = switch.autoping.enable_entry(entry_id)
    print(f"Enable {'succeeded' if success else 'failed'}")
    print()

    # Delete an entry (commented out for safety)
    # print("=== Deleting Entry ===\n")
    # success = switch.autoping.delete_entry(entry_id)
    # print(f"Delete {'succeeded' if success else 'failed'}")
    # print()

    print("AutoPing configuration example completed!")


if __name__ == "__main__":
    main()
