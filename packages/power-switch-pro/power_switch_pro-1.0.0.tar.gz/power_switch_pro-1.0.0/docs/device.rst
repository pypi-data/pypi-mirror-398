Digital Loggers Power Switch Pro
=================================

About the Device
----------------

The Digital Loggers Power Switch Pro is a network-controlled power distribution unit (PDU) that allows remote control and monitoring of power outlets via a RESTful API. The device is designed for data centers, labs, and automated testing environments where remote power management is essential.

Key Features
~~~~~~~~~~~~

* **Remote Outlet Control**: Turn outlets on, off, or cycle them remotely
* **Power Monitoring**: Real-time voltage, current, power, and energy measurements
* **AutoPing**: Automatically monitor hosts and power cycle outlets if they become unresponsive
* **User Management**: Multi-user support with per-outlet access controls
* **Scriptable**: Execute custom scripts on the device
* **RESTful API**: Standards-based HTTP REST API with JSON support
* **Secure**: HTTP Digest authentication and CSRF protection

Device Models
~~~~~~~~~~~~~

This library is designed to work with Digital Loggers Power Switch Pro models including:

* LPC (Web Power Switch Pro)
* Pro Switch
* Ethernet Power Controller III and later models

Supported Firmware
------------------

This library was developed and tested against the DLI REST API specification:

**API Version**: 20221009T204818Z (October 9, 2022)

The REST API has been available since firmware version 1.7.0 and later. For best compatibility, we recommend using the latest firmware available from Digital Loggers.

.. note::
   While this library targets the API specification from October 2022, it should work with earlier and later firmware versions that support the REST API. Some features may not be available on older firmware versions.

Checking Your Firmware Version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can check your device's firmware version using this library:

.. code-block:: python

    from power_switch_pro import PowerSwitchPro

    switch = PowerSwitchPro("192.168.0.100", "admin", "1234")
    info = switch.info
    print(f"Firmware version: {info['version']}")

Hardware Specifications
-----------------------

Typical specifications for Power Switch Pro devices:

* **Outlets**: 8 individually controlled outlets (model-dependent)
* **Current Rating**: 15A per outlet, 20A total (US models)
* **Voltage**: 100-240V AC (model-dependent)
* **Network**: 10/100 Ethernet
* **Protocols**: HTTP, HTTPS, SSH, Telnet
* **Power Monitoring**: Real-time voltage, current, and power factor monitoring
* **Dimensions**: Rack-mountable (1U or 2U depending on model)

Default Configuration
---------------------

Out of the box, most Power Switch Pro devices come with:

* **IP Address**: 192.168.0.100 (DHCP if available)
* **HTTP Port**: 80
* **HTTPS Port**: 443
* **Username**: admin
* **Password**: 1234 (should be changed immediately)

First-Time Setup
~~~~~~~~~~~~~~~~

1. Connect the device to your network
2. Access the device via web browser at http://192.168.0.100
3. Login with default credentials (admin/1234)
4. Change the admin password
5. Configure network settings as needed
6. Test the connection with this library

Network Configuration
---------------------

Static IP Configuration
~~~~~~~~~~~~~~~~~~~~~~~

To set a static IP address:

.. code-block:: python

    from power_switch_pro import PowerSwitchPro

    switch = PowerSwitchPro("192.168.0.100", "admin", "new_password")
    
    # Note: Network configuration requires accessing the web UI
    # or using the device's network configuration endpoints
    # This library focuses on outlet control and monitoring

Security Considerations
-----------------------

Authentication
~~~~~~~~~~~~~~

The device supports two authentication methods:

* **HTTP Digest Authentication** (recommended, default)
* **HTTP Basic Authentication** (must be enabled in config)

This library uses HTTP Digest Authentication by default for better security.

HTTPS Support
~~~~~~~~~~~~~

For encrypted communications:

.. code-block:: python

    from power_switch_pro import PowerSwitchPro

    # Use HTTPS
    switch = PowerSwitchPro(
        host="192.168.0.100",
        username="admin",
        password="password",
        use_https=True,
        verify_ssl=False  # Set to True in production with valid cert
    )

Best Practices
~~~~~~~~~~~~~~

1. **Change default password immediately**
2. **Use HTTPS in production environments**
3. **Create separate user accounts for different operators**
4. **Use outlet locking to prevent accidental changes to critical outlets**
5. **Enable SSH key authentication instead of passwords**
6. **Regularly update firmware**
7. **Use dedicated management network if possible**

AutoPing Feature
----------------

AutoPing is a built-in feature that monitors hosts via ICMP ping and automatically power cycles outlets if a host becomes unresponsive.

Configuration Example
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from power_switch_pro import PowerSwitchPro

    switch = PowerSwitchPro("192.168.0.100", "admin", "1234")
    
    # Monitor a server and restart it if unresponsive
    switch.autoping.add_entry(
        host="192.168.0.50",
        outlet=0,
        enabled=True,
        interval=60,    # Check every 60 seconds
        retries=3       # Try 3 times before cycling
    )

Power Monitoring
----------------

The device includes built-in power monitoring capabilities:

Measured Parameters
~~~~~~~~~~~~~~~~~~~

* **Voltage**: Line voltage (V)
* **Current**: Current draw per bus (A)
* **Power**: Real power consumption (W)
* **Energy**: Cumulative energy usage (kWh)
* **Power Factor**: For models that support it

Reading Measurements
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from power_switch_pro import PowerSwitchPro

    switch = PowerSwitchPro("192.168.0.100", "admin", "1234")
    
    # Get all measurements
    voltage = switch.meters.get_voltage()
    current = switch.meters.get_current()
    power = switch.meters.get_power()
    energy = switch.meters.get_total_energy()
    
    print(f"Load: {power}W at {voltage}V, {current}A")
    print(f"Total energy: {energy} kWh")

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Cannot connect to device**
    * Verify network connectivity (ping the device)
    * Check firewall settings
    * Ensure correct IP address
    * Verify device is powered on

**Authentication failures**
    * Verify username and password
    * Check if account is enabled
    * Ensure account has appropriate permissions

**Outlets not responding**
    * Check if outlet is locked
    * Verify user has access to that outlet
    * Check physical connections
    * Verify outlet is not in a failed state

**Power monitoring shows zero**
    * Some models don't support power monitoring
    * Check if load is connected
    * Verify measurements on web UI

Getting Help
~~~~~~~~~~~~

* Check device web UI for detailed status
* Review device system logs
* Consult Digital Loggers documentation
* Check this library's GitHub issues
* Contact Digital Loggers support for hardware issues

Additional Resources
--------------------

* `Digital Loggers Website <https://www.digital-loggers.com/>`_
* `Product Documentation <https://www.digital-loggers.com/pdfs.html>`_
* `Support Forum <https://www.digital-loggers.com/forum/>`_
* `REST API Documentation <https://www.digital-loggers.com/restapi.pdf>`_

Firmware Updates
----------------

To update device firmware:

1. Download latest firmware from Digital Loggers website
2. Access device web UI
3. Navigate to System → Firmware Update
4. Upload firmware file
5. Wait for update to complete (do not power off)
6. Verify new version after reboot

.. warning::
   Always backup your configuration before updating firmware. Firmware updates should not be interrupted as this may brick the device.
