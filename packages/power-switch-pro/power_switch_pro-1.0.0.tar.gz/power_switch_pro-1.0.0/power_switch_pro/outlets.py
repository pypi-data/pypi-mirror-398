"""Outlet management for Power Switch Pro."""

from typing import Any, Dict, List, Optional


class Outlet:
    """Represents a single power outlet."""

    def __init__(self, manager: "OutletManager", outlet_id: int):
        """
        Initialize outlet.

        Args:
            manager: Parent OutletManager instance
            outlet_id: Outlet index (0-based)
        """
        self.manager = manager
        self.outlet_id = outlet_id
        self.client = manager.client

    def on(self) -> bool:
        """
        Turn outlet on.

        Returns:
            True if successful
        """
        return self.manager.on(self.outlet_id)

    def off(self) -> bool:
        """
        Turn outlet off.

        Returns:
            True if successful
        """
        return self.manager.off(self.outlet_id)

    def cycle(self) -> bool:
        """
        Cycle outlet (off, then on).

        Returns:
            True if successful
        """
        return self.manager.cycle(self.outlet_id)

    @property
    def state(self) -> bool:
        """
        Get outlet state.

        Returns:
            True if on, False if off
        """
        return self.manager.get_state(self.outlet_id)

    @state.setter
    def state(self, value: bool):
        """Set outlet state."""
        if value:
            self.on()
        else:
            self.off()

    @property
    def physical_state(self) -> bool:
        """
        Get physical outlet state.

        Returns:
            True if physically on, False if off
        """
        return self.manager.get_physical_state(self.outlet_id)

    @property
    def name(self) -> str:
        """Get outlet name."""
        return self.manager.get_name(self.outlet_id)

    @name.setter
    def name(self, value: str):
        """Set outlet name."""
        self.manager.set_name(self.outlet_id, value)

    @property
    def locked(self) -> bool:
        """Get outlet lock status."""
        return self.manager.get_locked(self.outlet_id)

    @locked.setter
    def locked(self, value: bool):
        """Set outlet lock status."""
        self.manager.set_locked(self.outlet_id, value)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Outlet {self.outlet_id}: {self.name} ({'ON' if self.state else 'OFF'})>"
        )


class OutletManager:
    """Manager for power outlets."""

    def __init__(self, client):
        """
        Initialize outlet manager.

        Args:
            client: PowerSwitchPro client instance
        """
        self.client = client

    def __getitem__(self, outlet_id: int) -> Outlet:
        """
        Get outlet by index.

        Args:
            outlet_id: Outlet index (0-based)

        Returns:
            Outlet instance
        """
        return Outlet(self, outlet_id)

    def on(self, outlet_id: int) -> bool:
        """
        Turn on outlet.

        Args:
            outlet_id: Outlet index (0-based)

        Returns:
            True if successful
        """
        path = f"relay/outlets/{outlet_id}/state/"
        response = self.client.put(path, data={"value": "true"})
        return response.status_code in (200, 204)

    def off(self, outlet_id: int) -> bool:
        """
        Turn off outlet.

        Args:
            outlet_id: Outlet index (0-based)

        Returns:
            True if successful
        """
        path = f"relay/outlets/{outlet_id}/state/"
        response = self.client.put(path, data={"value": "false"})
        return response.status_code in (200, 204)

    def cycle(self, outlet_id: int) -> bool:
        """
        Cycle outlet (turn off, then on).

        Args:
            outlet_id: Outlet index (0-based)

        Returns:
            True if successful
        """
        path = f"relay/outlets/{outlet_id}/cycle/"
        response = self.client.post(path)
        return response.status_code in (200, 204)

    def get_state(self, outlet_id: int) -> bool:
        """
        Get outlet state.

        Args:
            outlet_id: Outlet index (0-based)

        Returns:
            True if on, False if off
        """
        path = f"relay/outlets/{outlet_id}/state/"
        response = self.client.get(path)
        return bool(response.json())

    def get_physical_state(self, outlet_id: int) -> bool:
        """
        Get physical outlet state.

        Args:
            outlet_id: Outlet index (0-based)

        Returns:
            True if physically on, False if off
        """
        path = f"relay/outlets/{outlet_id}/physical_state/"
        response = self.client.get(path)
        return bool(response.json())

    def get_name(self, outlet_id: int) -> str:
        """
        Get outlet name.

        Args:
            outlet_id: Outlet index (0-based)

        Returns:
            Outlet name
        """
        path = f"relay/outlets/{outlet_id}/name/"
        response = self.client.get(path)
        return str(response.json())

    def set_name(self, outlet_id: int, name: str) -> bool:
        """
        Set outlet name.

        Args:
            outlet_id: Outlet index (0-based)
            name: New outlet name

        Returns:
            True if successful
        """
        path = f"relay/outlets/{outlet_id}/name/"
        response = self.client.put(path, data={"value": name})
        return response.status_code in (200, 204)

    def get_locked(self, outlet_id: int) -> bool:
        """
        Get outlet lock status.

        Args:
            outlet_id: Outlet index (0-based)

        Returns:
            True if locked, False otherwise
        """
        path = f"relay/outlets/{outlet_id}/locked/"
        response = self.client.get(path)
        return bool(response.json())

    def set_locked(self, outlet_id: int, locked: bool) -> bool:
        """
        Set outlet lock status.

        Args:
            outlet_id: Outlet index (0-based)
            locked: Lock status

        Returns:
            True if successful
        """
        path = f"relay/outlets/{outlet_id}/locked/"
        response = self.client.put(path, data={"value": str(locked).lower()})
        return response.status_code in (200, 204)

    def get_all_states(self) -> List[bool]:
        """
        Get states of all outlets.

        Returns:
            List of outlet states
        """
        path = "relay/outlets/all;/state/"
        response = self.client.get(path)
        result: List[bool] = response.json()
        return result

    def get_states(self, outlet_ids: List[int]) -> List[bool]:
        """
        Get states of specific outlets.

        Args:
            outlet_ids: List of outlet indices

        Returns:
            List of outlet states
        """
        indices = ",".join(str(i) for i in outlet_ids)
        path = f"relay/outlets/={indices}/state/"
        response = self.client.get(path)
        result: List[bool] = response.json()
        return result

    def bulk_operation(
        self, action: str, locked: Optional[bool] = None, **filters
    ) -> bool:
        """
        Perform bulk operation on outlets matching filters.

        Args:
            action: Action to perform ('on', 'off', 'cycle')
            locked: Filter by locked status (optional)
            **filters: Additional filters (e.g., name='lamp')

        Returns:
            True if successful

        Examples:
            # Turn off all unlocked outlets
            manager.bulk_operation('off', locked=False)

            # Cycle all outlets named 'server'
            manager.bulk_operation('cycle', name='server')
        """
        # Build matrix URI
        filter_parts = []
        if locked is not None:
            filter_parts.append(f"locked={str(locked).lower()}")
        for key, value in filters.items():
            if isinstance(value, bool):
                value = str(value).lower()
            filter_parts.append(f"{key}={value}")

        filter_str = ";".join(filter_parts)
        if filter_str:
            filter_str = ";" + filter_str

        if action == "cycle":
            path = f"relay/outlets/all{filter_str}/cycle/"
            response = self.client.post(path)
        else:
            path = f"relay/outlets/all{filter_str}/state/"
            value = "true" if action == "on" else "false"
            response = self.client.put(path, data={"value": value})

        return response.status_code in (200, 204, 207)

    def count(self) -> int:
        """
        Get number of outlets.

        Returns:
            Number of outlets
        """
        path = "relay/outlets/"
        response = self.client.get(path, headers={"Range": "dli-depth=1"})
        data = response.json()
        # Count numeric keys (outlet indices)
        return len([k for k in data.keys() if k.isdigit()])

    def list_all(self) -> List[Dict[str, Any]]:
        """
        Get information about all outlets.

        Returns:
            List of outlet information dictionaries
        """
        outlets = []
        count = self.count()

        for i in range(count):
            try:
                outlet = {
                    "id": i,
                    "name": self.get_name(i),
                    "state": self.get_state(i),
                    "locked": self.get_locked(i),
                }
                outlets.append(outlet)
            except Exception:  # nosec B112
                # Skip outlets that don't exist or can't be accessed
                continue

        return outlets
