# Power Switch Pro Examples

This directory contains practical examples demonstrating how to use the Power Switch Pro library.

## Prerequisites

Before running these examples:

1. Install the library:
   ```bash
   pip install power-switch-pro
   ```

2. Update the connection parameters in each example:
   - `HOST`: Your Power Switch Pro IP address
   - `USERNAME`: Your username (default: "admin")
   - `PASSWORD`: Your password

3. Ensure your device has REST API enabled (firmware 1.7.0+)

## Examples

### basic_usage.py
Demonstrates fundamental operations:
- Connecting to the device
- Getting device information
- Controlling outlets (on/off/cycle)
- Reading outlet states

```bash
python basic_usage.py
```

### power_monitoring.py
Shows power monitoring capabilities:
- Reading voltage, current, and power
- Getting power factor readings
- Monitoring energy consumption
- Displaying meter statistics

```bash
python power_monitoring.py
```

**Note**: Power monitoring features require hardware with metering capability.

### autoping_config.py
Demonstrates AutoPing configuration:
- Listing AutoPing entries
- Adding new monitoring entries
- Updating ping settings
- Enabling/disabling entries
- Managing AutoPing rules

```bash
python autoping_config.py
```

### device_config.py
Shows device configuration management:
- Getting device settings
- Viewing network configuration
- Adjusting timeout settings
- Managing device parameters

```bash
python device_config.py
```

**Warning**: Configuration changes are commented out by default to prevent accidental modifications.

## Safety Notes

⚠️ **Important**: These examples may control real hardware. Always:

1. Test in a safe environment first
2. Understand what each command does before running
3. Be cautious with outlet control commands
4. Keep device credentials secure
5. Use HTTPS with valid SSL certificates in production

## Customization

Each example can be customized for your specific use case:

- Adjust timing delays in `basic_usage.py`
- Modify monitoring intervals in `power_monitoring.py`
- Customize AutoPing rules in `autoping_config.py`
- Adapt configuration settings in `device_config.py`

## Troubleshooting

### Connection Issues
- Verify the device IP address is correct
- Ensure the device is on the same network
- Check that REST API is enabled on your device
- Verify credentials are correct

### SSL Certificate Warnings
If using self-signed certificates:
```python
switch = PowerSwitchPro(
    host=HOST,
    username=USERNAME,
    password=PASSWORD,
    use_https=True,
    verify_ssl=False,  # Only for self-signed certificates
)
```

For production environments, use valid SSL certificates and set `verify_ssl=True`.

### Feature Not Available
Some features require specific hardware or firmware versions:
- Power monitoring requires devices with metering capability
- AutoPing requires firmware 1.7.0+
- Some configuration options vary by model

## Additional Resources

- [Full Documentation](https://power-switch-pro.readthedocs.io)
- [API Reference](https://power-switch-pro.readthedocs.io/en/latest/api.html)
- [GitHub Repository](https://github.com/bryankemp/power_switch_pro)
- [Digital Loggers Website](https://www.digital-loggers.com)

## Contributing

Have an example to share? Contributions are welcome! Please see the main [CONTRIBUTING.md](../CONTRIBUTING.md) file for guidelines.
