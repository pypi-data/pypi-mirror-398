"""AutoPing management for Power Switch Pro."""

from typing import Any, Dict, List, Optional


class AutoPingManager:
    """Manager for AutoPing functionality."""

    def __init__(self, client):
        """
        Initialize AutoPing manager.

        Args:
            client: PowerSwitchPro client instance
        """
        self.client = client

    def list_entries(self) -> List[Dict[str, Any]]:
        """
        Get list of all AutoPing entries.

        Returns:
            List of AutoPing entry dictionaries
        """
        path = "autoping/"
        response = self.client.get(path)
        data = response.json()

        # Convert to list if needed
        if isinstance(data, dict):
            entries = []
            for idx in sorted([k for k in data.keys() if k.isdigit()], key=int):
                entries.append(data[idx])
            return entries
        result: List[Dict[str, Any]] = data
        return result

    def get_entry(self, entry_id: int) -> Dict[str, Any]:
        """
        Get AutoPing entry by ID.

        Args:
            entry_id: Entry index

        Returns:
            AutoPing entry dictionary
        """
        path = f"autoping/{entry_id}/"
        response = self.client.get(path)
        result: Dict[str, Any] = response.json()
        return result

    def add_entry(
        self,
        host: str,
        outlet: int,
        enabled: bool = True,
        interval: int = 60,
        retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Add AutoPing entry.

        Args:
            host: Host to ping (IP address or hostname)
            outlet: Outlet index to control
            enabled: Whether entry is enabled
            interval: Ping interval in seconds
            retries: Number of retries before cycling outlet

        Returns:
            Created entry dictionary
        """
        path = "autoping/"

        data = {
            "host": host,
            "outlet": outlet,
            "enabled": str(enabled).lower(),
            "interval": interval,
            "retries": retries,
        }

        response = self.client.post(
            path,
            data=data,
            headers={"Prefer": "return=representation"},
        )

        if response.status_code == 201:
            result: Dict[str, Any] = response.json()
            return result
        return {}

    def update_entry(
        self,
        entry_id: int,
        host: Optional[str] = None,
        outlet: Optional[int] = None,
        enabled: Optional[bool] = None,
        interval: Optional[int] = None,
        retries: Optional[int] = None,
    ) -> bool:
        """
        Update AutoPing entry.

        Args:
            entry_id: Entry index
            host: New host (optional)
            outlet: New outlet (optional)
            enabled: New enabled status (optional)
            interval: New interval (optional)
            retries: New retries count (optional)

        Returns:
            True if successful
        """
        path = f"autoping/{entry_id}/"

        data: Dict[str, Any] = {}
        if host is not None:
            data["host"] = host
        if outlet is not None:
            data["outlet"] = outlet
        if enabled is not None:
            data["enabled"] = str(enabled).lower()
        if interval is not None:
            data["interval"] = str(interval)
        if retries is not None:
            data["retries"] = str(retries)

        response = self.client.patch(path, data=data)
        return response.status_code in (200, 204)

    def delete_entry(self, entry_id: int) -> bool:
        """
        Delete AutoPing entry.

        Args:
            entry_id: Entry index

        Returns:
            True if successful
        """
        path = f"autoping/{entry_id}/"
        response = self.client.delete(path)
        return response.status_code in (200, 204)

    def enable_entry(self, entry_id: int) -> bool:
        """
        Enable AutoPing entry.

        Args:
            entry_id: Entry index

        Returns:
            True if successful
        """
        return self.update_entry(entry_id, enabled=True)

    def disable_entry(self, entry_id: int) -> bool:
        """
        Disable AutoPing entry.

        Args:
            entry_id: Entry index

        Returns:
            True if successful
        """
        return self.update_entry(entry_id, enabled=False)
