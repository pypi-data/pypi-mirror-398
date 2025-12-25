:mod:`ble2wled.mqtt` - MQTT Beacon Listener
============================================

.. automodule:: ble2wled.mqtt
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The ``mqtt`` module provides MQTT listener for receiving beacon data from espresense devices. It:

- Connects to MQTT broker
- Subscribes to beacon topic
- Updates beacon state with position and signal strength
- Handles connection failures gracefully
- Supports username/password authentication

Quick Example
~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.mqtt import EspresenseBeaconListener
    from ble2wled.states import BeaconState

    # Create beacon state tracker
    state = BeaconState()

    # Create MQTT listener
    listener = EspresenseBeaconListener(
        state,
        broker='localhost',
        location='living_room'
    )

    # Start listening (non-blocking, runs in background)
    listener.start()

    # Beacon state is updated automatically as messages arrive
    import time
    time.sleep(5)
    print(f"Active beacons: {len(state.beacons)}")

    # Stop listener
    listener.stop()

Classes
-------

EspresenseBeaconListener
~~~~~~~~~~~~~~~~~~~~~~~~

Listens for beacon data from espresense devices via MQTT.

**Attributes:**

- ``beacon_state`` (BeaconState) - Beacon state to update
- ``broker`` (str) - MQTT broker hostname or IP
- ``port`` (int, default 1883) - MQTT port
- ``location`` (str) - Location/room identifier
- ``username`` (str, optional) - MQTT username
- ``password`` (str, optional) - MQTT password
- ``client`` - paho-mqtt client instance

**Methods:**

- ``start()`` - Start listening (non-blocking, runs in background thread)
- ``stop()`` - Stop listening and disconnect

**Behavior:**

Subscribes to topic: ``espresense/devices/{location}/#``

Handles message format:

.. code-block:: json

    {
      "distance": 2.5,
      "id": "device_id",
      "mac": "aa:bb:cc:dd:ee:ff",
      "rssi": -45,
      "name": "Device Name",
      "timestamp": 1234567890
    }

**Example:**

.. code-block:: python

    from ble2wled.mqtt import EspresenseBeaconListener
    from ble2wled.states import BeaconState

    state = BeaconState()

    # Basic listener
    listener = EspresenseBeaconListener(
        state,
        broker='192.168.1.50',
        location='bedroom'
    )
    listener.start()

    # Listener with authentication
    listener_auth = EspresenseBeaconListener(
        state,
        broker='192.168.1.50',
        port=1883,
        location='bedroom',
        username='mqtt_user',
        password='mqtt_password'
    )
    listener_auth.start()

Configuration
~~~~~~~~~~~~~

The MQTT topic is derived from location:

- Location: ``living_room``
- Topic: ``espresense/devices/living_room/#``

This subscribes to all devices reporting from that location.

**Topic format:**

``espresense/devices/{location}/{mac_address}``

Messages contain beacon distance, RSSI, and device info.

MQTT Message Format
~~~~~~~~~~~~~~~~~~~

espresense messages contain:

.. code-block:: json

    {
      "distance": 2.5,
      "id": "device_id",
      "mac": "aa:bb:cc:dd:ee:ff",
      "rssi": -45,
      "name": "Device Name",
      "timestamp": 1234567890
    }

The listener extracts:

- ``id`` - Unique beacon identifier
- ``distance`` - Estimated distance from device (meters)
- ``rssi`` - Signal strength (dBm)

Examples
--------

Basic MQTT Listening
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.mqtt import EspresenseBeaconListener
    from ble2wled.states import BeaconState
    import time

    # Setup
    state = BeaconState()
    listener = EspresenseBeaconListener(
        state,
        broker='localhost',
        location='test'
    )

    # Start listening
    listener.start()
    print("Listening for beacon data...")

    # Let it collect data
    time.sleep(10)

    # Check collected beacons
    print(f"Received {len(state.beacons)} beacons")
    for beacon_id, beacon in state.beacons.items():
        print(f"  {beacon_id}: position={beacon.position}, rssi={beacon.rssi}")

    # Stop listening
    listener.stop()

With Configuration
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.config import Config
    from ble2wled.mqtt import EspresenseBeaconListener
    from ble2wled.states import BeaconState

    # Load configuration from .env
    config = Config('.env')

    # Create listener with config
    state = BeaconState(
        timeout_seconds=config.beacon_timeout_seconds,
        fade_out_seconds=config.beacon_fade_out_seconds
    )

    listener = EspresenseBeaconListener(
        state,
        broker=config.mqtt_broker,
        port=config.mqtt_port,
        location=config.mqtt_location,
        username=config.mqtt_username,
        password=config.mqtt_password
    )

    listener.start()

With WLED Animation
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.mqtt import EspresenseBeaconListener
    from ble2wled.states import BeaconState
    from ble2wled.wled import WLEDUDPController
    from ble2wled.animation import run_wled_beacons

    # Setup
    state = BeaconState()
    listener = EspresenseBeaconListener(
        state,
        broker='localhost',
        location='living_room'
    )
    controller = WLEDUDPController('192.168.1.100', 60)

    # Start MQTT listener
    listener.start()

    # Run animation (blocks)
    try:
        run_wled_beacons(
            controller,
            led_count=60,
            beacon_state=state
        )
    finally:
        listener.stop()

With Authentication
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.mqtt import EspresenseBeaconListener
    from ble2wled.states import BeaconState

    state = BeaconState()

    # With credentials for secured MQTT broker
    listener = EspresenseBeaconListener(
        state,
        broker='192.168.1.50',
        port=1883,
        location='kitchen',
        username='mqtt_user',
        password='secure_password'
    )

    listener.start()

Multiple Locations
~~~~~~~~~~~~~~~~~~

Monitor multiple locations with separate listeners:

.. code-block:: python

    from ble2wled.mqtt import EspresenseBeaconListener
    from ble2wled.states import BeaconState

    # Create state for each location
    living_room_state = BeaconState()
    kitchen_state = BeaconState()

    # Create listeners
    living_room_listener = EspresenseBeaconListener(
        living_room_state,
        broker='localhost',
        location='living_room'
    )

    kitchen_listener = EspresenseBeaconListener(
        kitchen_state,
        broker='localhost',
        location='kitchen'
    )

    # Start both
    living_room_listener.start()
    kitchen_listener.start()

    # Process both state streams...

    # Stop both
    living_room_listener.stop()
    kitchen_listener.stop()

Error Handling
--------------

Connection Failures
~~~~~~~~~~~~~~~~~~~

The listener handles connection failures gracefully:

.. code-block:: python

    from ble2wled.mqtt import EspresenseBeaconListener
    from ble2wled.states import BeaconState

    state = BeaconState()
    listener = EspresenseBeaconListener(
        state,
        broker='192.168.1.100',  # Non-existent broker
        location='test'
    )

    listener.start()  # Doesn't raise, just logs error
    # Check logs for connection errors

Authentication Failures
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.mqtt import EspresenseBeaconListener
    from ble2wled.states import BeaconState

    state = BeaconState()
    listener = EspresenseBeaconListener(
        state,
        broker='localhost',
        location='test',
        username='wrong_user',
        password='wrong_password'
    )

    listener.start()  # Doesn't raise, but won't receive messages
    # Check logs: "MQTT authentication failed"

Troubleshooting
---------------

No Beacons Received
~~~~~~~~~~~~~~~~~~~

1. Check MQTT broker is running:

   .. code-block:: bash

       mosquitto_sub -h localhost -t "espresense/devices/test/#"

   If this doesn't show messages, broker isn't receiving espresense data.

2. Verify location matches espresense configuration

3. Check authentication credentials

4. Check network connectivity:

   .. code-block:: bash

       ping <mqtt-broker-ip>

Connection Refused
~~~~~~~~~~~~~~~~~~

1. Verify broker is running and accessible

2. Check port (default 1883)

3. Verify IP/hostname is correct

4. Check firewall rules

Authentication Failed
~~~~~~~~~~~~~~~~~~~~~

1. Verify username and password are correct

2. Check user account exists in MQTT broker:

   .. code-block:: bash

       # Mosquitto
       sudo mosquitto_passwd -l /etc/mosquitto/passwd

3. Check broker authentication is enabled

Performance
-----------

Message Rate
~~~~~~~~~~~~

MQTT listener receives messages for each detected beacon. Typical rates:

- 1-5 beacons: 10-50 messages/second
- 10+ beacons: 100+ messages/second

The listener is non-blocking and handles high message rates efficiently.

State Updates
~~~~~~~~~~~~~

Beacon state is updated immediately as messages arrive. No polling needed.

Examples per Second
~~~~~~~~~~~~~~~~~~~

- Low: 1-2 messages/second (1-2 beacons with slow scan)
- Medium: 10-20 messages/second (3-5 beacons)
- High: 100+ messages/second (10+ beacons with fast scan)

See Also
--------

- :doc:`states` - Beacon state management
- :doc:`../guides/mqtt_authentication` - MQTT authentication guide
- :doc:`../guides/configuration` - Configuration reference
- :doc:`../quickstart` - Quick start with MQTT
