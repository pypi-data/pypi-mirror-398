"""Tests for authentication and user management."""

import responses


class TestAuthManager:
    """Test AuthManager class."""

    @responses.activate
    def test_list_users(self, client, base_url):
        """Test listing all users."""
        responses.add(
            responses.GET,
            f"{base_url}auth/users/",
            json={
                "0": {"name": "admin", "is_admin": True},
                "1": {"name": "user1", "is_admin": False},
            },
            status=200,
        )

        users = client.auth_manager.list_users()
        assert len(users) == 2
        assert users[0]["name"] == "admin"

    @responses.activate
    def test_list_users_array_response(self, client, base_url):
        """Test listing users when API returns array."""
        responses.add(
            responses.GET,
            f"{base_url}auth/users/",
            json=[
                {"name": "admin", "is_admin": True},
                {"name": "user1", "is_admin": False},
            ],
            status=200,
        )

        users = client.auth_manager.list_users()
        assert len(users) == 2

    @responses.activate
    def test_get_user(self, client, base_url):
        """Test getting user by ID."""
        responses.add(
            responses.GET,
            f"{base_url}auth/users/0/",
            json={"name": "admin", "is_admin": True, "is_allowed": True},
            status=200,
        )

        user = client.auth_manager.get_user(0)
        assert user["name"] == "admin"
        assert user["is_admin"] is True

    @responses.activate
    def test_get_user_by_name(self, client, base_url):
        """Test getting user by name."""
        responses.add(
            responses.GET,
            f"{base_url}auth/users/one;name=testuser/",
            json={"name": "testuser", "is_admin": False},
            status=200,
        )

        user = client.auth_manager.get_user_by_name("testuser")
        assert user["name"] == "testuser"

    @responses.activate
    def test_get_user_by_name_not_found(self, client, base_url):
        """Test getting user by name when not found."""
        responses.add(
            responses.GET,
            f"{base_url}auth/users/one;name=notfound/",
            status=404,
        )

        user = client.auth_manager.get_user_by_name("notfound")
        assert user is None

    @responses.activate
    def test_add_user(self, client, base_url):
        """Test adding a new user."""
        responses.add(
            responses.POST,
            f"{base_url}auth/users/",
            json={
                "name": "newuser",
                "password": "secret",
                "is_allowed": True,
                "is_admin": False,
                "outlet_access": [
                    True,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                ],
            },
            status=201,
        )

        user = client.auth_manager.add_user(
            name="newuser",
            password="secret",
            outlet_access=[True, False, False, False, False, False, False, False],
        )

        assert user["name"] == "newuser"

    @responses.activate
    def test_add_user_default_access(self, client, base_url):
        """Test adding user with default outlet access."""
        responses.add(
            responses.POST,
            f"{base_url}auth/users/",
            json={
                "name": "newuser",
                "password": "secret",
                "is_allowed": True,
                "is_admin": False,
                "outlet_access": [
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                ],
            },
            status=201,
        )

        user = client.auth_manager.add_user(
            name="newuser",
            password="secret",
        )

        assert user["name"] == "newuser"

    @responses.activate
    def test_add_user_admin(self, client, base_url):
        """Test adding an admin user."""
        responses.add(
            responses.POST,
            f"{base_url}auth/users/",
            json={
                "name": "newadmin",
                "password": "secret",
                "is_allowed": True,
                "is_admin": True,
                "outlet_access": [
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                ],
            },
            status=201,
        )

        user = client.auth_manager.add_user(
            name="newadmin",
            password="secret",
            is_admin=True,
        )

        assert user["is_admin"] is True

    @responses.activate
    def test_update_user(self, client, base_url):
        """Test updating user information."""
        responses.add(
            responses.PATCH,
            f"{base_url}auth/users/1/",
            status=200,
        )

        result = client.auth_manager.update_user(
            user_id=1,
            name="updated_name",
            password="new_password",
        )

        assert result is True

    @responses.activate
    def test_update_user_all_fields(self, client, base_url):
        """Test updating all user fields."""
        responses.add(
            responses.PATCH,
            f"{base_url}auth/users/1/",
            status=200,
        )

        result = client.auth_manager.update_user(
            user_id=1,
            name="updated",
            password="newpass",
            is_allowed=False,
            outlet_access=[True, True, False, False, False, False, False, False],
        )

        assert result is True

    @responses.activate
    def test_delete_user(self, client, base_url):
        """Test deleting user by ID."""
        responses.add(
            responses.DELETE,
            f"{base_url}auth/users/2/",
            status=200,
        )

        result = client.auth_manager.delete_user(2)
        assert result is True

    @responses.activate
    def test_delete_user_by_name(self, client, base_url):
        """Test deleting user by name."""
        responses.add(
            responses.DELETE,
            f"{base_url}auth/users/name=testuser/",
            status=200,
        )

        result = client.auth_manager.delete_user_by_name("testuser")
        assert result is True

    @responses.activate
    def test_change_admin_password(self, client, base_url):
        """Test changing admin password."""
        responses.add(
            responses.PATCH,
            f"{base_url}auth/users/is_admin=true/",
            status=200,
        )

        result = client.auth_manager.change_admin_password("oldpass", "newpass")
        assert result is True
