"""Authentication and user management for Power Switch Pro."""

from typing import Any, Dict, List, Optional


class AuthManager:
    """Manager for authentication and users."""

    def __init__(self, client):
        """
        Initialize auth manager.

        Args:
            client: PowerSwitchPro client instance
        """
        self.client = client

    def list_users(self) -> List[Dict[str, Any]]:
        """
        Get list of all users.

        Returns:
            List of user dictionaries
        """
        path = "auth/users/"
        response = self.client.get(path)
        users_data = response.json()

        # If it's an object with numeric keys, convert to list
        if isinstance(users_data, dict):
            users = []
            for idx in sorted([k for k in users_data.keys() if k.isdigit()], key=int):
                users.append(users_data[idx])
            return users
        result: List[Dict[str, Any]] = users_data
        return result

    def get_user(self, user_id: int) -> Dict[str, Any]:
        """
        Get user by ID.

        Args:
            user_id: User index

        Returns:
            User dictionary
        """
        path = f"auth/users/{user_id}/"
        response = self.client.get(path)
        result: Dict[str, Any] = response.json()
        return result

    def get_user_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get user by name.

        Args:
            name: Username

        Returns:
            User dictionary or None if not found
        """
        path = f"auth/users/one;name={name}/"
        try:
            response = self.client.get(path)
            result: Dict[str, Any] = response.json()
            return result
        except Exception:
            return None

    def add_user(
        self,
        name: str,
        password: str,
        is_allowed: bool = True,
        is_admin: bool = False,
        outlet_access: Optional[List[bool]] = None,
    ) -> Dict[str, Any]:
        """
        Add a new user.

        Args:
            name: Username
            password: User password
            is_allowed: Whether user is allowed to login
            is_admin: Whether user is admin
            outlet_access: List of outlet access permissions (one per outlet)

        Returns:
            Created user dictionary
        """
        path = "auth/users/"

        # Build outlet access list if not provided
        if outlet_access is None:
            # Default to no access
            outlet_access = [False] * 8

        data = {
            "name": name,
            "password": password,
            "is_allowed": is_allowed,
            "is_admin": is_admin,
            "outlet_access": ",".join(str(v).lower() for v in outlet_access),
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

    def update_user(
        self,
        user_id: int,
        name: Optional[str] = None,
        password: Optional[str] = None,
        is_allowed: Optional[bool] = None,
        outlet_access: Optional[List[bool]] = None,
    ) -> bool:
        """
        Update user information.

        Args:
            user_id: User index
            name: New username (optional)
            password: New password (optional)
            is_allowed: New allowed status (optional)
            outlet_access: New outlet access permissions (optional)

        Returns:
            True if successful
        """
        path = f"auth/users/{user_id}/"

        data = {}
        if name is not None:
            data["name"] = name
        if password is not None:
            data["password"] = password
        if is_allowed is not None:
            data["is_allowed"] = str(is_allowed).lower()
        if outlet_access is not None:
            data["outlet_access"] = ",".join(str(v).lower() for v in outlet_access)

        response = self.client.patch(path, data=data)
        return response.status_code in (200, 204)

    def delete_user(self, user_id: int) -> bool:
        """
        Delete user.

        Args:
            user_id: User index

        Returns:
            True if successful
        """
        path = f"auth/users/{user_id}/"
        response = self.client.delete(path)
        return response.status_code in (200, 204)

    def delete_user_by_name(self, name: str) -> bool:
        """
        Delete user by name.

        Args:
            name: Username

        Returns:
            True if successful
        """
        path = f"auth/users/name={name}/"
        response = self.client.delete(path)
        return response.status_code in (200, 204)

    def change_admin_password(self, old_password: str, new_password: str) -> bool:
        """
        Change administrator password.

        Args:
            old_password: Current password
            new_password: New password

        Returns:
            True if successful
        """
        path = "auth/users/is_admin=true/"
        data = {
            "old_password": old_password,
            "new_password": new_password,
        }
        response = self.client.patch(path, data=data)
        return response.status_code in (200, 204)
