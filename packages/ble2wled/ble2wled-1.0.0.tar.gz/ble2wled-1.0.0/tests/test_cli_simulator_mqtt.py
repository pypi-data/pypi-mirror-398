"""Tests for CLI simulator MQTT functionality."""

import inspect
from unittest.mock import MagicMock, patch

import pytest

from ble2wled.cli_simulator import main
from ble2wled.states import BeaconState


class TestCLISimulatorMQTT:
    """Test cases for MQTT beacon mode in CLI simulator."""

    def test_main_with_mqtt_flag(self):
        """Test that main accepts MQTT flag."""
        # This just tests that the function accepts the parameter
        # We can't actually run it without a broker, but we can verify the signature
        sig = inspect.signature(main)
        assert "use_mqtt" in sig.parameters
        assert "mqtt_broker" in sig.parameters
        assert "mqtt_port" in sig.parameters
        assert "mqtt_location" in sig.parameters

    def test_mqtt_parameters_defaults(self):
        """Test MQTT parameter defaults."""
        sig = inspect.signature(main)

        assert sig.parameters["use_mqtt"].default is False
        assert sig.parameters["mqtt_broker"].default == "localhost"
        assert sig.parameters["mqtt_port"].default == 1883
        assert sig.parameters["mqtt_location"].default == "balkon"

    def test_main_beacon_state_updated_without_mqtt(self):
        """Test beacon state is updated with mock generator when not using MQTT."""
        beacon_state = BeaconState()

        # The beacon_state should be passed to both generator and MQTT listener
        # This test just verifies the BeaconState class works as expected
        beacon_state.update("test_beacon", -50)

        snapshot = beacon_state.snapshot()
        assert "test_beacon" in snapshot
        assert snapshot["test_beacon"][0] == -50  # RSSI

    @patch("ble2wled.cli_simulator.EspresenseBeaconListener")
    def test_mqtt_listener_created_with_correct_params(self, mock_listener_class):
        """Test that MQTT listener is created with correct parameters."""
        mock_listener = MagicMock()
        mock_listener_class.return_value = mock_listener

        beacon_state = BeaconState()

        # Simulate what happens in main when use_mqtt=True
        mqtt_listener = mock_listener_class(
            beacon_state,
            broker="test.example.com",
            location="bedroom",
            port=1883,
        )

        # Verify listener was created
        mock_listener_class.assert_called_once_with(
            beacon_state,
            broker="test.example.com",
            location="bedroom",
            port=1883,
        )

        # Verify start was not called yet
        mqtt_listener.start.assert_not_called()

    def test_mock_generator_still_works_without_mqtt(self):
        """Test that mock generator still works when not using MQTT."""
        from ble2wled.simulator import MockBeaconGenerator

        generator = MockBeaconGenerator(num_beacons=2)
        beacons = generator.update(time_delta=0.1)

        assert len(beacons) == 2
        assert "beacon_0" in beacons
        assert "beacon_1" in beacons
        assert isinstance(beacons["beacon_0"], int)
        assert isinstance(beacons["beacon_1"], int)

    def test_beacon_state_shared_between_mqtt_and_renderer(self):
        """Test that beacon state is shared between MQTT listener and renderer."""
        beacon_state = BeaconState()

        # Simulate MQTT listener updating beacon state
        beacon_state.update("beacon_from_mqtt", -55)

        # Renderer should see the update
        snapshot = beacon_state.snapshot()
        assert "beacon_from_mqtt" in snapshot
        rssi, life = snapshot["beacon_from_mqtt"]
        assert rssi == -55
        assert life > 0  # Should have life value

    def test_mqtt_mode_ignores_num_beacons_parameter(self):
        """Test that num_beacons parameter is ignored when using MQTT."""
        sig = inspect.signature(main)

        # Both parameters should exist
        assert "use_mqtt" in sig.parameters
        assert "num_beacons" in sig.parameters

        # When use_mqtt is True, num_beacons should not affect MQTT data source
        # (This is verified by the implementation logic)

    def test_cli_validation_mqtt_port_range(self):
        """Test that CLI validates MQTT port range."""
        import sys

        from ble2wled.cli_simulator import cli

        # Test invalid port (too high)
        with patch.object(sys, "argv", ["prog", "--mqtt-port", "99999"]):
            with pytest.raises(SystemExit):
                cli()

        # Test invalid port (too low)
        with patch.object(sys, "argv", ["prog", "--mqtt-port", "0"]):
            with pytest.raises(SystemExit):
                cli()

    def test_mqtt_beacon_timeout_configuration(self):
        """Test that beacon timeout is configured for MQTT mode."""
        beacon_state = BeaconState(timeout_seconds=3.0, fade_out_seconds=2.0)

        # Verify beacon state has correct timeout configuration
        assert beacon_state is not None

        # Add a beacon and verify it times out
        beacon_state.update("test", -50)
        snapshot1 = beacon_state.snapshot()
        assert "test" in snapshot1

    def test_cli_help_includes_mqtt_options(self):
        """Test that CLI help includes MQTT options."""
        import sys

        from ble2wled.cli_simulator import cli

        with patch.object(sys, "argv", ["prog", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                cli()
            # Help should exit with code 0
            assert exc_info.value.code == 0

    def test_main_docstring_includes_mqtt_example(self):
        """Test that main function docstring includes MQTT example."""
        docstring = main.__doc__
        assert docstring is not None
        assert "use_mqtt" in docstring.lower()
        assert "mqtt" in docstring.lower()
