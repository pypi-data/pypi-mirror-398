"""Tests for script execution management."""

import responses


class TestScriptManager:
    """Test ScriptManager class."""

    @responses.activate
    def test_start(self, client, base_url):
        """Test starting script execution."""
        responses.add(
            responses.POST,
            f"{base_url}script/start/",
            json="thread_12345",
            status=200,
        )

        thread_id = client.script.start("test_function")
        assert thread_id == "thread_12345"

    @responses.activate
    def test_start_with_source(self, client, base_url):
        """Test starting script execution with source code."""
        responses.add(
            responses.POST,
            f"{base_url}script/start/",
            json="thread_67890",
            status=200,
        )

        thread_id = client.script.start("test_func", 'test_func(1, "hello")')
        assert thread_id == "thread_67890"

    @responses.activate
    def test_get_status(self, client, base_url):
        """Test getting script execution status."""
        responses.add(
            responses.GET,
            f"{base_url}script/status/thread_123/",
            json={
                "status": "running",
                "output": "Processing...",
                "progress": 50,
            },
            status=200,
        )

        status = client.script.get_status("thread_123")
        assert status["status"] == "running"
        assert status["progress"] == 50

    @responses.activate
    def test_stop(self, client, base_url):
        """Test stopping script execution."""
        responses.add(
            responses.POST,
            f"{base_url}script/stop/thread_456/",
            status=200,
        )

        result = client.script.stop("thread_456")
        assert result is True

    @responses.activate
    def test_stop_status_204(self, client, base_url):
        """Test stopping script with 204 response."""
        responses.add(
            responses.POST,
            f"{base_url}script/stop/thread_789/",
            status=204,
        )

        result = client.script.stop("thread_789")
        assert result is True

    @responses.activate
    def test_list_functions(self, client, base_url):
        """Test listing available user functions."""
        responses.add(
            responses.GET,
            f"{base_url}script/functions/",
            json=["func1", "func2", "func3"],
            status=200,
        )

        functions = client.script.list_functions()
        assert len(functions) == 3
        assert "func1" in functions

    @responses.activate
    def test_list_functions_dict(self, client, base_url):
        """Test listing functions when API returns dict."""
        responses.add(
            responses.GET,
            f"{base_url}script/functions/",
            json={"func1": {}, "func2": {}, "func3": {}},
            status=200,
        )

        functions = client.script.list_functions()
        assert len(functions) == 3
        assert "func1" in functions
