"""Tests for meter/power monitoring management."""

import responses


class TestMeterManager:
    """Test MeterManager class."""

    @responses.activate
    def test_get_all_values(self, client, base_url):
        """Test getting all meter values."""
        responses.add(
            responses.GET,
            f"{base_url}meter/values/all;/",
            json={
                "bus.0.current": 1.5,
                "bus.0.voltage": 120.2,
                "bus.0.power": 180.3,
            },
            status=200,
        )

        meters = client.meters.get_all_values()
        assert len(meters) == 3
        assert meters[0]["name"] == "bus.0.current"
        assert meters[0]["value"] == 1.5

    @responses.activate
    def test_get_value(self, client, base_url):
        """Test getting specific meter value."""
        responses.add(
            responses.GET,
            f"{base_url}meter/values/bus.0.current/value/",
            json=1.5,
            status=200,
        )

        current = client.meters.get_value("bus.0.current")
        assert current == 1.5

    @responses.activate
    def test_get_voltage(self, client, base_url):
        """Test getting voltage reading."""
        responses.add(
            responses.GET,
            f"{base_url}meter/values/bus.0.voltage/value/",
            json=120.5,
            status=200,
        )

        voltage = client.meters.get_voltage()
        assert voltage == 120.5

    @responses.activate
    def test_get_voltage_custom_bus(self, client, base_url):
        """Test getting voltage reading for custom bus."""
        responses.add(
            responses.GET,
            f"{base_url}meter/values/bus.1.voltage/value/",
            json=120.3,
            status=200,
        )

        voltage = client.meters.get_voltage(bus=1)
        assert voltage == 120.3

    @responses.activate
    def test_get_current(self, client, base_url):
        """Test getting current reading."""
        responses.add(
            responses.GET,
            f"{base_url}meter/values/bus.0.current/value/",
            json=1.2,
            status=200,
        )

        current = client.meters.get_current()
        assert current == 1.2

    @responses.activate
    def test_get_current_custom_bus(self, client, base_url):
        """Test getting current reading for custom bus."""
        responses.add(
            responses.GET,
            f"{base_url}meter/values/bus.2.current/value/",
            json=0.8,
            status=200,
        )

        current = client.meters.get_current(bus=2)
        assert current == 0.8

    @responses.activate
    def test_get_power(self, client, base_url):
        """Test getting power reading."""
        responses.add(
            responses.GET,
            f"{base_url}meter/values/bus.0.power/value/",
            json=144.6,
            status=200,
        )

        power = client.meters.get_power()
        assert power == 144.6

    @responses.activate
    def test_get_power_calculated(self, client, base_url):
        """Test getting power calculated from voltage and current."""
        # First request for power fails
        responses.add(
            responses.GET,
            f"{base_url}meter/values/bus.0.power/value/",
            status=404,
        )
        # Then get voltage
        responses.add(
            responses.GET,
            f"{base_url}meter/values/bus.0.voltage/value/",
            json=120.0,
            status=200,
        )
        # Then get current
        responses.add(
            responses.GET,
            f"{base_url}meter/values/bus.0.current/value/",
            json=1.5,
            status=200,
        )

        power = client.meters.get_power()
        assert power == 180.0  # 120 * 1.5

    @responses.activate
    def test_get_total_energy(self, client, base_url):
        """Test getting total energy consumption."""
        responses.add(
            responses.GET,
            f"{base_url}meter/values/bus.0.total_energy/value/",
            json=1234.5,
            status=200,
        )

        energy = client.meters.get_total_energy()
        assert energy == 1234.5

    @responses.activate
    def test_get_bus_values(self, client, base_url):
        """Test getting all values for a specific bus."""
        responses.add(
            responses.GET,
            f"{base_url}meter/values/all;bus=0/=name,value/",
            json=["bus.0.current", 1.2, "bus.0.voltage", 120.5],
            status=200,
        )

        values = client.meters.get_bus_values()
        assert values["bus.0.current"] == 1.2
        assert values["bus.0.voltage"] == 120.5

    @responses.activate
    def test_list_meters(self, client, base_url):
        """Test listing all available meters."""
        responses.add(
            responses.GET,
            f"{base_url}meter/values/all;/=name,value/",
            json=["bus.0.current", 1.5, "bus.0.voltage", 120.2],
            status=200,
        )

        meters = client.meters.list_meters()
        assert len(meters) == 2
        assert meters[0]["name"] == "bus.0.current"
        assert meters[0]["value"] == 1.5
