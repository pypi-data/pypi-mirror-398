"""Tests for espresense MQTT listener."""

from unittest.mock import MagicMock, patch

from ble2wled.mqtt import EspresenseBeaconListener
from ble2wled.states import BeaconState


class TestEspresenseBeaconListener:
    """Test cases for EspresenseBeaconListener."""

    def test_init(self):
        """Test listener initialization."""
        state = BeaconState()
        with patch("ble2wled.mqtt.mqtt.Client"):
            listener = EspresenseBeaconListener(state, "localhost", location="balkon")
            assert listener.location == "balkon"
            assert listener.base_topic == "espresense/devices"

    def test_parse_topic_and_payload(self):
        """Test parsing topic and payload."""
        state = BeaconState()
        with patch("ble2wled.mqtt.mqtt.Client"):
            listener = EspresenseBeaconListener(state, "localhost", location="balkon")

            # Create mock message
            msg = MagicMock()
            msg.topic = "espresense/devices/iBeacon:2686f39c-bada-4658-854a-a62e7e5e8b8d-1-0/balkon"
            msg.payload = b'{"id":"iBeacon:2686f39c-bada-4658-854a-a62e7e5e8b8d-1-0","rssi":-50.5}'

            # Process message
            listener.on_message(None, None, msg)

            # Verify beacon was updated
            snapshot = state.snapshot()
            assert "iBeacon:2686f39c-bada-4658-854a-a62e7e5e8b8d-1-0" in snapshot
            rssi, life = snapshot["iBeacon:2686f39c-bada-4658-854a-a62e7e5e8b8d-1-0"]
            assert rssi == -50
            assert life == 1.0

    def test_filters_by_location(self):
        """Test that messages are filtered by location."""
        state = BeaconState()
        with patch("ble2wled.mqtt.mqtt.Client"):
            listener = EspresenseBeaconListener(state, "localhost", location="balkon")

            # Create message from wrong location
            msg = MagicMock()
            msg.topic = "espresense/devices/iBeacon:test-1-0/kitchen"
            msg.payload = b'{"id":"iBeacon:test-1-0","rssi":-50}'

            listener.on_message(None, None, msg)

            # Verify beacon was NOT updated
            snapshot = state.snapshot()
            assert len(snapshot) == 0

    def test_handles_beacon_id_mismatch(self):
        """Test handling of beacon ID mismatch."""
        state = BeaconState()
        with patch("ble2wled.mqtt.mqtt.Client"):
            listener = EspresenseBeaconListener(state, "localhost", location="balkon")

            # Create message with mismatched ID
            msg = MagicMock()
            msg.topic = "espresense/devices/iBeacon:test1-1-0/balkon"
            msg.payload = b'{"id":"iBeacon:test2-1-0","rssi":-50}'

            listener.on_message(None, None, msg)

            # Verify beacon was NOT updated
            snapshot = state.snapshot()
            assert len(snapshot) == 0

    def test_handles_missing_rssi(self):
        """Test handling of missing RSSI."""
        state = BeaconState()
        with patch("ble2wled.mqtt.mqtt.Client"):
            listener = EspresenseBeaconListener(state, "localhost", location="balkon")

            # Create message without rssi
            msg = MagicMock()
            msg.topic = "espresense/devices/iBeacon:test-1-0/balkon"
            msg.payload = b'{"id":"iBeacon:test-1-0"}'

            listener.on_message(None, None, msg)

            # Verify beacon was NOT updated
            snapshot = state.snapshot()
            assert len(snapshot) == 0

    def test_apple_beacon_format(self):
        """Test parsing of apple beacon format."""
        state = BeaconState()
        with patch("ble2wled.mqtt.mqtt.Client"):
            listener = EspresenseBeaconListener(state, "localhost", location="balkon")

            # Apple beacon format
            msg = MagicMock()
            msg.topic = "espresense/devices/apple:1006:10-12/balkon"
            msg.payload = (
                b'{"mac":"67518126293a","id":"apple:1006:10-12",'
                b'"rssi@1m":-65,"rssi":-84.77,"rxAdj":0,'
                b'"rssiVar":9.56,"distance":2.49,"var":0.16,"int":626}'
            )

            listener.on_message(None, None, msg)

            # Verify beacon was updated
            snapshot = state.snapshot()
            assert "apple:1006:10-12" in snapshot
            rssi, life = snapshot["apple:1006:10-12"]
            assert rssi == -84
            assert life == 1.0

    def test_handles_invalid_json(self):
        """Test handling of invalid JSON."""
        state = BeaconState()
        with patch("ble2wled.mqtt.mqtt.Client"):
            listener = EspresenseBeaconListener(state, "localhost", location="balkon")

            # Invalid JSON
            msg = MagicMock()
            msg.topic = "espresense/devices/iBeacon:test-1-0/balkon"
            msg.payload = b"not valid json"

            listener.on_message(None, None, msg)

            # Verify beacon was NOT updated
            snapshot = state.snapshot()
            assert len(snapshot) == 0

    def test_handles_short_topic(self):
        """Test handling of malformed topic."""
        state = BeaconState()
        with patch("ble2wled.mqtt.mqtt.Client"):
            listener = EspresenseBeaconListener(state, "localhost", location="balkon")

            # Too few topic parts
            msg = MagicMock()
            msg.topic = "espresense/devices"
            msg.payload = b'{"id":"test","rssi":-50}'

            listener.on_message(None, None, msg)

            # Verify beacon was NOT updated
            snapshot = state.snapshot()
            assert len(snapshot) == 0
