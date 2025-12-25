Examples
========

This page contains practical examples for common use cases.

Automated Server Monitoring
----------------------------

Monitor servers and automatically restart them if they become unresponsive:

.. code-block:: python

    from power_switch_pro import PowerSwitchPro
    import time

    switch = PowerSwitchPro("192.168.0.100", "admin", "1234")

    # Configure AutoPing for automatic monitoring
    switch.autoping.add_entry(
        host="192.168.0.50",
        outlet=0,
        enabled=True,
        interval=60,  # Check every 60 seconds
        retries=3     # Retry 3 times before cycling
    )

    print("Server monitoring enabled")

Scheduled Power Cycling
-----------------------

Power cycle devices on a schedule:

.. code-block:: python

    from power_switch_pro import PowerSwitchPro
    import schedule
    import time

    switch = PowerSwitchPro("192.168.0.100", "admin", "1234")

    def cycle_outlet(outlet_id):
        """Cycle a specific outlet."""
        print(f"Cycling outlet {outlet_id}")
        switch.outlets[outlet_id].cycle()
        print(f"Outlet {outlet_id} cycled")

    # Schedule daily reboot at 3 AM
    schedule.every().day.at("03:00").do(cycle_outlet, outlet_id=0)

    # Run scheduler
    while True:
        schedule.run_pending()
        time.sleep(60)

Power Usage Monitoring
----------------------

Log power consumption over time:

.. code-block:: python

    from power_switch_pro import PowerSwitchPro
    import time
    import csv
    from datetime import datetime

    switch = PowerSwitchPro("192.168.0.100", "admin", "1234")

    # Log power data to CSV
    with open('power_log.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Timestamp', 'Voltage', 'Current', 'Power', 'Energy'])
        
        for _ in range(100):  # Log 100 samples
            timestamp = datetime.now().isoformat()
            voltage = switch.meters.get_voltage()
            current = switch.meters.get_current()
            power = switch.meters.get_power()
            energy = switch.meters.get_total_energy()
            
            writer.writerow([timestamp, voltage, current, power, energy])
            print(f"{timestamp}: {power}W")
            
            time.sleep(60)  # Sample every minute

Bulk Outlet Control
-------------------

Control multiple outlets based on conditions:

.. code-block:: python

    from power_switch_pro import PowerSwitchPro

    switch = PowerSwitchPro("192.168.0.100", "admin", "1234")

    # Get all outlet info
    outlets = switch.outlets.list_all()

    # Turn off all outlets named 'test'
    for outlet in outlets:
        if 'test' in outlet['name'].lower():
            print(f"Turning off {outlet['name']}")
            switch.outlets[outlet['id']].off()

    # Or use bulk operations
    switch.outlets.bulk_operation('off', name='test')

User Management Script
----------------------

Manage device users programmatically:

.. code-block:: python

    from power_switch_pro import PowerSwitchPro

    switch = PowerSwitchPro("192.168.0.100", "admin", "1234")

    # Create users for each team member
    team_users = [
        ("alice", "alice_pass", [True, True, False, False, False, False, False, False]),
        ("bob", "bob_pass", [False, False, True, True, False, False, False, False]),
        ("charlie", "charlie_pass", [False, False, False, False, True, True, True, True]),
    ]

    for name, password, outlets in team_users:
        try:
            user = switch.auth_manager.add_user(
                name=name,
                password=password,
                outlet_access=outlets
            )
            print(f"Created user: {name}")
        except Exception as e:
            print(f"Failed to create {name}: {e}")

    # List all users
    users = switch.auth_manager.list_users()
    for user in users:
        print(f"User: {user['name']}, Admin: {user['is_admin']}")

Error Recovery
--------------

Implement robust error handling:

.. code-block:: python

    from power_switch_pro import (
        PowerSwitchPro,
        AuthenticationError,
        ConnectionError,
        APIError
    )
    import time

    def safe_outlet_control(host, username, password, outlet_id, action):
        """
        Safely control an outlet with retry logic.
        
        Args:
            host: Device IP
            username: Username
            password: Password
            outlet_id: Outlet index
            action: 'on', 'off', or 'cycle'
        """
        max_retries = 3
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                switch = PowerSwitchPro(host, username, password)
                outlet = switch.outlets[outlet_id]
                
                if action == 'on':
                    outlet.on()
                elif action == 'off':
                    outlet.off()
                elif action == 'cycle':
                    outlet.cycle()
                
                print(f"Successfully performed {action} on outlet {outlet_id}")
                return True
                
            except AuthenticationError:
                print("Authentication failed - check credentials")
                return False
                
            except ConnectionError as e:
                print(f"Connection error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    
            except APIError as e:
                print(f"API error: {e}")
                return False
        
        print("Failed after all retries")
        return False

    # Use the function
    safe_outlet_control("192.168.0.100", "admin", "1234", 0, "cycle")

Configuration Backup
--------------------

Backup and restore device configuration:

.. code-block:: python

    from power_switch_pro import PowerSwitchPro
    import json

    switch = PowerSwitchPro("192.168.0.100", "admin", "1234")

    # Backup configuration
    config = {
        'device_info': switch.info,
        'outlets': switch.outlets.list_all(),
        'users': switch.auth_manager.list_users(),
        'autoping': switch.autoping.list_entries(),
        'config': switch.config.get_all(depth=3)
    }

    with open('switch_backup.json', 'w') as f:
        json.dump(config, f, indent=2, default=str)

    print("Configuration backed up to switch_backup.json")

    # Restore outlet names
    with open('switch_backup.json', 'r') as f:
        backup = json.load(f)
    
    for outlet in backup['outlets']:
        switch.outlets[outlet['id']].name = outlet['name']
        switch.outlets[outlet['id']].locked = outlet['locked']

Context Manager Pattern
-----------------------

Use context managers for cleaner code:

.. code-block:: python

    from power_switch_pro import PowerSwitchPro
    from contextlib import contextmanager

    @contextmanager
    def power_switch_context(host, username, password):
        """Context manager for power switch operations."""
        switch = PowerSwitchPro(host, username, password)
        try:
            yield switch
        finally:
            # Cleanup if needed
            pass

    # Use with context manager
    with power_switch_context("192.168.0.100", "admin", "1234") as switch:
        # All operations within this block
        switch.outlets[0].on()
        voltage = switch.meters.get_voltage()
        print(f"Voltage: {voltage}V")
