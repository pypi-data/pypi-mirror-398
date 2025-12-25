Quick Start Guide
=================

This guide will help you get started with the Power Switch Pro library.

Basic Connection
----------------

First, import the library and create a connection to your device:

.. code-block:: python

    from power_switch_pro import PowerSwitchPro

    # Connect to device
    switch = PowerSwitchPro(
        host="192.168.0.100",
        username="admin",
        password="1234"
    )

    # Test connection
    if switch.test_connection():
        print("Connected successfully!")

Controlling Outlets
-------------------

Turn outlets on and off:

.. code-block:: python

    # Turn on outlet 1 (index 0)
    switch.outlets[0].on()

    # Turn off outlet 2
    switch.outlets[1].off()

    # Cycle outlet 3 (power cycle)
    switch.outlets[2].cycle()

    # Get outlet state
    if switch.outlets[0].state:
        print("Outlet 1 is ON")

Working with Multiple Outlets
------------------------------

Get states of all outlets:

.. code-block:: python

    # Get all outlet states
    states = switch.outlets.get_all_states()
    print(f"All states: {states}")

    # Get specific outlets
    states = switch.outlets.get_states([0, 1, 4])
    print(f"Outlets 1, 2, and 5: {states}")

    # List all outlets with info
    outlets = switch.outlets.list_all()
    for outlet in outlets:
        print(f"Outlet {outlet['id']}: {outlet['name']} - {'ON' if outlet['state'] else 'OFF'}")

Bulk Operations
---------------

Perform operations on multiple outlets at once:

.. code-block:: python

    # Turn off all unlocked outlets
    switch.outlets.bulk_operation('off', locked=False)

    # Cycle all outlets named 'server'
    switch.outlets.bulk_operation('cycle', name='server')

Monitoring Power
----------------

Read power metrics:

.. code-block:: python

    # Get voltage
    voltage = switch.meters.get_voltage()
    print(f"Voltage: {voltage}V")

    # Get current
    current = switch.meters.get_current()
    print(f"Current: {current}A")

    # Get power
    power = switch.meters.get_power()
    print(f"Power: {power}W")

    # Get total energy consumed
    energy = switch.meters.get_total_energy()
    print(f"Total energy: {energy} kWh")

Managing Outlets
----------------

Configure outlet settings:

.. code-block:: python

    # Get/set outlet name
    outlet = switch.outlets[0]
    print(f"Current name: {outlet.name}")
    outlet.name = "Web Server"

    # Lock/unlock outlet
    outlet.locked = True  # Lock outlet
    outlet.locked = False  # Unlock outlet

Device Information
------------------

Get device details:

.. code-block:: python

    # Get device info
    info = switch.info
    print(f"Serial: {info['serial']}")
    print(f"Version: {info['version']}")
    print(f"Hostname: {info['hostname']}")

    # Get configuration
    hostname = switch.config.get_hostname()
    print(f"Device hostname: {hostname}")

Error Handling
--------------

Handle errors appropriately:

.. code-block:: python

    from power_switch_pro import (
        AuthenticationError,
        ConnectionError,
        APIError
    )

    try:
        switch = PowerSwitchPro("192.168.0.100", "admin", "wrong_password")
        switch.outlets[0].on()
    except AuthenticationError:
        print("Invalid credentials")
    except ConnectionError:
        print("Cannot connect to device")
    except APIError as e:
        print(f"API error: {e}")

Next Steps
----------

* See the :doc:`api` for complete API reference
* Check out :doc:`examples` for more code examples
* Read about :doc:`contributing` to help improve the library
