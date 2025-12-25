"""Power meter management for Power Switch Pro."""

from typing import Any, Dict, List


class MeterManager:
    """Manager for power meters and metrics."""

    def __init__(self, client):
        """
        Initialize meter manager.

        Args:
            client: PowerSwitchPro client instance
        """
        self.client = client

    def get_all_values(self) -> List[Dict[str, Any]]:
        """
        Get all meter values.

        Returns:
            List of meter dictionaries with names and values
        """
        path = "meter/values/all;/"
        response = self.client.get(path)
        data = response.json()

        # Convert to list of dicts if needed
        if isinstance(data, dict):
            meters = []
            for key, value in data.items():
                if not key.startswith("$"):
                    meters.append({"name": key, "value": value})
            return meters
        return data

    def get_value(self, meter_name: str) -> float:
        """
        Get specific meter value.

        Args:
            meter_name: Meter identifier (e.g., "bus.0.current")

        Returns:
            Meter value
        """
        path = f"meter/values/{meter_name}/value/"
        response = self.client.get(path)
        return response.json()

    def get_voltage(self, bus: int = 0) -> float:
        """
        Get voltage reading.

        Args:
            bus: Bus number (default: 0)

        Returns:
            Voltage in volts
        """
        return self.get_value(f"bus.{bus}.voltage")

    def get_current(self, bus: int = 0) -> float:
        """
        Get current reading.

        Args:
            bus: Bus number (default: 0)

        Returns:
            Current in amps
        """
        return self.get_value(f"bus.{bus}.current")

    def get_power(self, bus: int = 0) -> float:
        """
        Get power reading.

        Args:
            bus: Bus number (default: 0)

        Returns:
            Power in watts
        """
        try:
            return self.get_value(f"bus.{bus}.power")
        except Exception:
            # Calculate from voltage and current if power meter not available
            voltage = self.get_voltage(bus)
            current = self.get_current(bus)
            return voltage * current

    def get_total_energy(self, bus: int = 0) -> float:
        """
        Get total energy consumed.

        Args:
            bus: Bus number (default: 0)

        Returns:
            Total energy in kWh
        """
        return self.get_value(f"bus.{bus}.total_energy")

    def get_bus_values(self, bus: int = 0) -> Dict[str, float]:
        """
        Get all meter values for a specific bus.

        Args:
            bus: Bus number (default: 0)

        Returns:
            Dictionary of meter names and values
        """
        path = f"meter/values/all;bus={bus}/=name,value/"
        response = self.client.get(path)
        data = response.json()

        # Parse the response which is a flat array [name1, value1, name2, value2, ...]
        if isinstance(data, list) and len(data) % 2 == 0:
            result = {}
            for i in range(0, len(data), 2):
                result[data[i]] = data[i + 1]
            return result

        return {}

    def list_meters(self) -> List[Dict[str, Any]]:
        """
        Get list of all available meters.

        Returns:
            List of meter information dictionaries
        """
        path = "meter/values/all;/=name,value/"
        response = self.client.get(path)
        data = response.json()

        meters = []
        if isinstance(data, list) and len(data) % 2 == 0:
            for i in range(0, len(data), 2):
                meters.append(
                    {
                        "name": data[i],
                        "value": data[i + 1],
                    }
                )

        return meters
