"""MQTT listener for BLE beacon data from espresense.

This module provides the EspresenseBeaconListener class for receiving beacon
data from espresense via MQTT.

espresense is a distributed Bluetooth scanner that publishes BLE beacon
locations to MQTT. This listener subscribes to beacon topics and updates
the beacon state with RSSI values.

MQTT Topic Structure:
    espresense/devices/{beacon_id}/{location}

Example:
    Listen for beacons from a specific location::

        from ble2wled.mqtt import EspresenseBeaconListener
        from ble2wled.states import BeaconState

        state = BeaconState()
        listener = EspresenseBeaconListener(
            state,
            broker='192.168.1.100',
            location='living_room',
            port=1883
        )
        listener.start()
"""

import json
import logging
import threading
from typing import TYPE_CHECKING

import paho.mqtt.client as mqtt

if TYPE_CHECKING:
    from .states import BeaconState

logger = logging.getLogger(__name__)


class EspresenseBeaconListener:
    """Listens for BLE beacon data from espresense MQTT broker.

    Subscribes to espresense/devices/{beacon_id}/{location} topics and
    filters for messages from a specific location. Extracts beacon ID and
    RSSI from the topic and JSON payload.

    Attributes:
        state (BeaconState): BeaconState instance to update with beacon data.
        location (str): Location name to filter for (e.g., 'balkon').
        base_topic (str): Base MQTT topic prefix ('espresense/devices').
    """

    def __init__(
        self,
        state: "BeaconState",
        broker: str,
        location: str = "balkon",
        port: int = 1883,
        username: str | None = None,
        password: str | None = None,
    ):
        """Initialize espresense beacon listener.

        Connects to MQTT broker and subscribes to beacon topics.

        Args:
            state (BeaconState): BeaconState instance to update with beacon data.
            broker (str): MQTT broker hostname or IP address.
            location (str): Location name to filter for (e.g., 'balkon').
                Default: 'balkon'.
            port (int): MQTT broker port. Default: 1883.
            username (str): MQTT broker username for authentication.
                Default: None (no authentication).
            password (str): MQTT broker password for authentication.
                Default: None (no authentication).

        Example:
            Create and start listener without authentication::

                listener = EspresenseBeaconListener(
                    state,
                    broker='192.168.1.100',
                    location='bedroom',
                    port=1883
                )
                listener.start()

            Create and start listener with authentication::

                listener = EspresenseBeaconListener(
                    state,
                    broker='192.168.1.100',
                    location='bedroom',
                    port=1883,
                    username='mqtt_user',
                    password='mqtt_pass'
                )
                listener.start()
        """
        self.state = state
        self.location = location
        self.base_topic = "espresense/devices"

        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        # Set authentication credentials if provided
        if username and password:
            self.client.username_pw_set(username, password)
            logger.debug("MQTT authentication configured for user: %s", username)

        self.client.connect(broker, port, 30)

    def on_connect(
        self,
        client: mqtt.Client,
        userdata: object,  # noqa: ARG002
        flags: dict,  # noqa: ARG002
        rc: int,  # noqa: ARG002
    ) -> None:
        """Handle MQTT connection.

        Called when the client connects to the broker. Subscribes to beacon
        topics and logs connection status.

        Args:
            client (mqtt.Client): MQTT client instance.
            userdata (object): User data (unused).
            flags (dict): Connection flags (unused).
            rc (int): Connection result code (unused).

        Note:
            This is a callback method called by paho-mqtt library.
        """
        # Subscribe to all devices at all locations
        subscribe_topic = f"{self.base_topic}/+/+"
        client.subscribe(subscribe_topic)
        logger.info("Connected to MQTT broker, subscribed to %s", subscribe_topic)

    def on_message(
        self,
        client: mqtt.Client,  # noqa: ARG002
        userdata: object,  # noqa: ARG002
        msg: mqtt.MQTTMessage,
    ) -> None:
        """Handle incoming MQTT message from espresense.

        Parses topic and payload to extract beacon ID and RSSI. Validates
        data consistency and updates beacon state.

        Topic format: espresense/devices/{beacon_id}/{location}
        Payload format: {\"id\": \"...\", \"rssi\": -50.5, ...}

        Args:
            client (mqtt.Client): MQTT client instance (unused).
            userdata (object): User data (unused).
            msg (mqtt.MQTTMessage): MQTT message with topic and payload.

        Example:
            This method is called automatically by the MQTT library when
            messages arrive on subscribed topics.

        Note:
            This is a callback method called by paho-mqtt library.
        """
        try:
            # Parse topic: espresense/devices/{beacon_id}/{location}
            topic_parts = msg.topic.split("/")
            if len(topic_parts) < 4:
                return

            location = topic_parts[-1]
            beacon_id = topic_parts[-2]

            # Filter by location
            if location != self.location:
                return

            # Parse payload
            payload = json.loads(msg.payload.decode())
            beacon_id_payload = payload.get("id")
            rssi = payload.get("rssi")

            # Validate required fields
            if not beacon_id_payload or rssi is None:
                logger.warning(
                    "Missing id or rssi in payload from %s: %s",
                    beacon_id,
                    payload,
                )
                return

            # Verify beacon ID matches between topic and payload
            if beacon_id_payload != beacon_id:
                logger.warning(
                    "Beacon ID mismatch - topic: %s, payload: %s",
                    beacon_id,
                    beacon_id_payload,
                )
                return

            # Update state with beacon
            self.state.update(beacon_id, int(rssi))

        except json.JSONDecodeError as e:
            logger.warning("Failed to decode JSON payload: %s", e)
        except (IndexError, KeyError, TypeError) as e:
            logger.warning("Error parsing MQTT message: %s", e)

    def start(self) -> None:
        """Start listening in background thread.

        Starts the MQTT client loop in a background daemon thread. Blocks
        until connection is established.

        Example:
            Start listening for beacons::

                listener.start()
                # Listener runs in background, updating beacon state
        """
        threading.Thread(target=self.client.loop_forever, daemon=True).start()
        logger.debug("MQTT listener started for location %r", self.location)


# Backward compatibility alias
BeaconMQTTListener = EspresenseBeaconListener
