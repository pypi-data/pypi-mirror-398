"""Tests for AutoPing management."""

import responses


class TestAutoPingManager:
    """Test AutoPingManager class."""

    @responses.activate
    def test_list_entries(self, client, base_url):
        """Test listing all AutoPing entries."""
        responses.add(
            responses.GET,
            f"{base_url}autoping/",
            json={
                "0": {"host": "192.168.1.100", "outlet": 0, "enabled": "true"},
                "1": {"host": "192.168.1.200", "outlet": 1, "enabled": "false"},
            },
            status=200,
        )

        entries = client.autoping.list_entries()
        assert len(entries) == 2
        assert entries[0]["host"] == "192.168.1.100"

    @responses.activate
    def test_list_entries_array(self, client, base_url):
        """Test listing entries when API returns array."""
        responses.add(
            responses.GET,
            f"{base_url}autoping/",
            json=[
                {"host": "192.168.1.100", "outlet": 0},
            ],
            status=200,
        )

        entries = client.autoping.list_entries()
        assert len(entries) == 1

    @responses.activate
    def test_get_entry(self, client, base_url):
        """Test getting specific AutoPing entry."""
        responses.add(
            responses.GET,
            f"{base_url}autoping/0/",
            json={"host": "192.168.1.50", "outlet": 0, "enabled": "true"},
            status=200,
        )

        entry = client.autoping.get_entry(0)
        assert entry["host"] == "192.168.1.50"
        assert entry["outlet"] == 0

    @responses.activate
    def test_add_entry(self, client, base_url):
        """Test adding AutoPing entry."""
        responses.add(
            responses.POST,
            f"{base_url}autoping/",
            json={"host": "192.168.1.75", "outlet": 2},
            status=201,
        )

        entry = client.autoping.add_entry(
            host="192.168.1.75",
            outlet=2,
            enabled=True,
            interval=60,
            retries=3,
        )
        assert entry["host"] == "192.168.1.75"
        assert entry["outlet"] == 2

    @responses.activate
    def test_update_entry(self, client, base_url):
        """Test updating AutoPing entry."""
        responses.add(
            responses.PATCH,
            f"{base_url}autoping/0/",
            status=200,
        )

        result = client.autoping.update_entry(0, host="192.168.1.99")
        assert result is True

    @responses.activate
    def test_update_entry_multiple_fields(self, client, base_url):
        """Test updating multiple fields in AutoPing entry."""
        responses.add(
            responses.PATCH,
            f"{base_url}autoping/1/",
            status=204,
        )

        result = client.autoping.update_entry(
            1, host="192.168.1.88", enabled=False, interval=120
        )
        assert result is True

    @responses.activate
    def test_delete_entry(self, client, base_url):
        """Test deleting AutoPing entry."""
        responses.add(
            responses.DELETE,
            f"{base_url}autoping/2/",
            status=200,
        )

        result = client.autoping.delete_entry(2)
        assert result is True

    @responses.activate
    def test_enable_entry(self, client, base_url):
        """Test enabling AutoPing entry."""
        responses.add(
            responses.PATCH,
            f"{base_url}autoping/0/",
            status=200,
        )

        result = client.autoping.enable_entry(0)
        assert result is True

    @responses.activate
    def test_disable_entry(self, client, base_url):
        """Test disabling AutoPing entry."""
        responses.add(
            responses.PATCH,
            f"{base_url}autoping/1/",
            status=200,
        )

        result = client.autoping.disable_entry(1)
        assert result is True
