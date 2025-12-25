"""Tests for outlet management."""

import responses


class TestOutletManager:
    """Test OutletManager class."""

    @responses.activate
    def test_outlet_on(self, client, base_url):
        """Test turning on an outlet."""
        responses.add(
            responses.PUT,
            f"{base_url}relay/outlets/0/state/",
            status=200,
        )

        result = client.outlets.on(0)
        assert result is True

    @responses.activate
    def test_outlet_off(self, client, base_url):
        """Test turning off an outlet."""
        responses.add(
            responses.PUT,
            f"{base_url}relay/outlets/1/state/",
            status=200,
        )

        result = client.outlets.off(1)
        assert result is True

    @responses.activate
    def test_outlet_cycle(self, client, base_url):
        """Test cycling an outlet."""
        responses.add(
            responses.POST,
            f"{base_url}relay/outlets/2/cycle/",
            status=200,
        )

        result = client.outlets.cycle(2)
        assert result is True

    @responses.activate
    def test_get_state(self, client, base_url):
        """Test getting outlet state."""
        responses.add(
            responses.GET,
            f"{base_url}relay/outlets/0/state/",
            json=True,
            status=200,
        )

        state = client.outlets.get_state(0)
        assert state is True

    @responses.activate
    def test_get_physical_state(self, client, base_url):
        """Test getting physical outlet state."""
        responses.add(
            responses.GET,
            f"{base_url}relay/outlets/0/physical_state/",
            json=False,
            status=200,
        )

        state = client.outlets.get_physical_state(0)
        assert state is False

    @responses.activate
    def test_get_name(self, client, base_url):
        """Test getting outlet name."""
        responses.add(
            responses.GET,
            f"{base_url}relay/outlets/0/name/",
            json="Test Outlet",
            status=200,
        )

        name = client.outlets.get_name(0)
        assert name == "Test Outlet"

    @responses.activate
    def test_set_name(self, client, base_url):
        """Test setting outlet name."""
        responses.add(
            responses.PUT,
            f"{base_url}relay/outlets/0/name/",
            status=200,
        )

        result = client.outlets.set_name(0, "New Name")
        assert result is True

    @responses.activate
    def test_get_locked(self, client, base_url):
        """Test getting outlet lock status."""
        responses.add(
            responses.GET,
            f"{base_url}relay/outlets/0/locked/",
            json=True,
            status=200,
        )

        locked = client.outlets.get_locked(0)
        assert locked is True

    @responses.activate
    def test_set_locked(self, client, base_url):
        """Test setting outlet lock status."""
        responses.add(
            responses.PUT,
            f"{base_url}relay/outlets/0/locked/",
            status=200,
        )

        result = client.outlets.set_locked(0, True)
        assert result is True

    @responses.activate
    def test_get_all_states(self, client, base_url):
        """Test getting all outlet states."""
        responses.add(
            responses.GET,
            f"{base_url}relay/outlets/all;/state/",
            json=[True, False, True, False, True, False, True, False],
            status=200,
        )

        states = client.outlets.get_all_states()
        assert len(states) == 8
        assert states[0] is True
        assert states[1] is False

    @responses.activate
    def test_get_states(self, client, base_url):
        """Test getting specific outlet states."""
        responses.add(
            responses.GET,
            f"{base_url}relay/outlets/=0,1,4/state/",
            json=[True, False, True],
            status=200,
        )

        states = client.outlets.get_states([0, 1, 4])
        assert len(states) == 3

    @responses.activate
    def test_bulk_operation_off(self, client, base_url):
        """Test bulk operation to turn off outlets."""
        responses.add(
            responses.PUT,
            f"{base_url}relay/outlets/all;locked=false/state/",
            status=207,
        )

        result = client.outlets.bulk_operation("off", locked=False)
        assert result is True

    @responses.activate
    def test_bulk_operation_on(self, client, base_url):
        """Test bulk operation to turn on outlets."""
        responses.add(
            responses.PUT,
            f"{base_url}relay/outlets/all;locked=false/state/",
            status=207,
        )

        result = client.outlets.bulk_operation("on", locked=False)
        assert result is True

    @responses.activate
    def test_bulk_operation_cycle(self, client, base_url):
        """Test bulk operation to cycle outlets."""
        responses.add(
            responses.POST,
            f"{base_url}relay/outlets/all;name=test/cycle/",
            status=207,
        )

        result = client.outlets.bulk_operation("cycle", name="test")
        assert result is True

    @responses.activate
    def test_bulk_operation_multiple_filters(self, client, base_url):
        """Test bulk operation with multiple filters."""
        responses.add(
            responses.PUT,
            f"{base_url}relay/outlets/all;locked=false;name=server/state/",
            status=207,
        )

        result = client.outlets.bulk_operation("off", locked=False, name="server")
        assert result is True

    @responses.activate
    def test_count(self, client, base_url):
        """Test counting outlets."""
        responses.add(
            responses.GET,
            f"{base_url}relay/outlets/",
            json={
                "0": {},
                "1": {},
                "2": {},
                "3": {},
                "4": {},
                "5": {},
                "6": {},
                "7": {},
            },
            status=200,
        )

        count = client.outlets.count()
        assert count == 8

    @responses.activate
    def test_list_all(self, client, base_url):
        """Test listing all outlets."""
        # Mock multiple requests for each outlet
        for i in range(3):
            responses.add(
                responses.GET,
                f"{base_url}relay/outlets/",
                json={"0": {}, "1": {}, "2": {}},
                status=200,
            )
            responses.add(
                responses.GET,
                f"{base_url}relay/outlets/{i}/name/",
                json=f"Outlet {i}",
                status=200,
            )
            responses.add(
                responses.GET,
                f"{base_url}relay/outlets/{i}/state/",
                json=True,
                status=200,
            )
            responses.add(
                responses.GET,
                f"{base_url}relay/outlets/{i}/locked/",
                json=False,
                status=200,
            )

        outlets = client.outlets.list_all()
        assert len(outlets) == 3
        assert outlets[0]["name"] == "Outlet 0"


class TestOutlet:
    """Test Outlet class."""

    @responses.activate
    def test_outlet_indexing(self, client, base_url):
        """Test accessing outlet by index."""
        outlet = client.outlets[0]
        assert outlet.outlet_id == 0
        assert outlet.client == client

    @responses.activate
    def test_outlet_on(self, client, base_url):
        """Test outlet on method."""
        responses.add(
            responses.PUT,
            f"{base_url}relay/outlets/0/state/",
            status=200,
        )

        outlet = client.outlets[0]
        result = outlet.on()
        assert result is True

    @responses.activate
    def test_outlet_off(self, client, base_url):
        """Test outlet off method."""
        responses.add(
            responses.PUT,
            f"{base_url}relay/outlets/0/state/",
            status=200,
        )

        outlet = client.outlets[0]
        result = outlet.off()
        assert result is True

    @responses.activate
    def test_outlet_cycle(self, client, base_url):
        """Test outlet cycle method."""
        responses.add(
            responses.POST,
            f"{base_url}relay/outlets/0/cycle/",
            status=200,
        )

        outlet = client.outlets[0]
        result = outlet.cycle()
        assert result is True

    @responses.activate
    def test_outlet_state_property(self, client, base_url):
        """Test outlet state property."""
        responses.add(
            responses.GET,
            f"{base_url}relay/outlets/0/state/",
            json=True,
            status=200,
        )

        outlet = client.outlets[0]
        assert outlet.state is True

    @responses.activate
    def test_outlet_state_setter_true(self, client, base_url):
        """Test outlet state setter with True."""
        responses.add(
            responses.PUT,
            f"{base_url}relay/outlets/0/state/",
            status=200,
        )

        outlet = client.outlets[0]
        outlet.state = True
        assert len(responses.calls) == 1

    @responses.activate
    def test_outlet_state_setter_false(self, client, base_url):
        """Test outlet state setter with False."""
        responses.add(
            responses.PUT,
            f"{base_url}relay/outlets/0/state/",
            status=200,
        )

        outlet = client.outlets[0]
        outlet.state = False
        assert len(responses.calls) == 1

    @responses.activate
    def test_outlet_physical_state_property(self, client, base_url):
        """Test outlet physical_state property."""
        responses.add(
            responses.GET,
            f"{base_url}relay/outlets/0/physical_state/",
            json=True,
            status=200,
        )

        outlet = client.outlets[0]
        assert outlet.physical_state is True

    @responses.activate
    def test_outlet_name_property(self, client, base_url):
        """Test outlet name property."""
        responses.add(
            responses.GET,
            f"{base_url}relay/outlets/0/name/",
            json="Test",
            status=200,
        )

        outlet = client.outlets[0]
        assert outlet.name == "Test"

    @responses.activate
    def test_outlet_name_setter(self, client, base_url):
        """Test outlet name setter."""
        responses.add(
            responses.PUT,
            f"{base_url}relay/outlets/0/name/",
            status=200,
        )

        outlet = client.outlets[0]
        outlet.name = "New Name"
        assert len(responses.calls) == 1

    @responses.activate
    def test_outlet_locked_property(self, client, base_url):
        """Test outlet locked property."""
        responses.add(
            responses.GET,
            f"{base_url}relay/outlets/0/locked/",
            json=False,
            status=200,
        )

        outlet = client.outlets[0]
        assert outlet.locked is False

    @responses.activate
    def test_outlet_locked_setter(self, client, base_url):
        """Test outlet locked setter."""
        responses.add(
            responses.PUT,
            f"{base_url}relay/outlets/0/locked/",
            status=200,
        )

        outlet = client.outlets[0]
        outlet.locked = True
        assert len(responses.calls) == 1

    @responses.activate
    def test_outlet_repr(self, client, base_url):
        """Test outlet string representation."""
        responses.add(
            responses.GET,
            f"{base_url}relay/outlets/0/name/",
            json="TestOutlet",
            status=200,
        )
        responses.add(
            responses.GET,
            f"{base_url}relay/outlets/0/state/",
            json=True,
            status=200,
        )

        outlet = client.outlets[0]
        repr_str = repr(outlet)
        assert "Outlet 0" in repr_str
        assert "TestOutlet" in repr_str
        assert "ON" in repr_str
