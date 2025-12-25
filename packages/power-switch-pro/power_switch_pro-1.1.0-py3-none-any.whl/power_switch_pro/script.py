"""Script execution management for Power Switch Pro."""

from typing import Any, Dict, List, Optional


class ScriptManager:
    """Manager for script execution."""

    def __init__(self, client):
        """
        Initialize script manager.

        Args:
            client: PowerSwitchPro client instance
        """
        self.client = client

    def start(
        self,
        function_name: str,
        source: Optional[str] = None,
    ) -> str:
        """
        Start script execution.

        Args:
            function_name: Name of the user function to execute
            source: Optional source code with function call and arguments

        Returns:
            Thread identifier as string

        Examples:
            # Run function without arguments
            thread_id = manager.start("test")

            # Run function with arguments
            thread_id = manager.start("test", 'test(1.5, "hello")')
        """
        path = "script/start/"

        if source:
            payload = [{"user_function": function_name, "source": source}]
        else:
            payload = [{"user_function": function_name}]

        response = self.client.post(
            path,
            json_data=payload,
            headers={"Content-Type": "application/json"},
        )

        return str(response.json())

    def get_status(self, thread_id: str) -> Dict[str, Any]:
        """
        Get script execution status.

        Args:
            thread_id: Thread identifier from start()

        Returns:
            Status dictionary
        """
        path = f"script/status/{thread_id}/"
        response = self.client.get(path)
        result: Dict[str, Any] = response.json()
        return result

    def stop(self, thread_id: str) -> bool:
        """
        Stop script execution.

        Args:
            thread_id: Thread identifier from start()

        Returns:
            True if successful
        """
        path = f"script/stop/{thread_id}/"
        response = self.client.post(path)
        return response.status_code in (200, 204)

    def list_functions(self) -> List[str]:
        """
        Get list of available user functions.

        Returns:
            List of function names
        """
        path = "script/functions/"
        response = self.client.get(path)
        data = response.json()

        if isinstance(data, dict):
            return list(data.keys())
        elif isinstance(data, list):
            return data
        return []
