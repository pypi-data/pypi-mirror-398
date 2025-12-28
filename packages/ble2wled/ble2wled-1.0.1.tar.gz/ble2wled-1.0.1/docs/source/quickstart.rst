Quickstart
==========

Get BLE2WLED up and running in 5 minutes.

1. Installation
---------------

.. code-block:: bash

    pip install -e ".[dev]"

2. Basic Setup
--------------

Create a `.env` file in your project directory:

.. code-block:: bash

    # WLED LED Strip
    WLED_HOST=wled.local
    LED_COUNT=60

    # MQTT Broker
    MQTT_BROKER=localhost
    MQTT_LOCATION=living_room
    MQTT_PORT=1883

3. Test with Simulator
----------------------

Run the CLI simulator to see beacon visualization in your terminal:

.. code-block:: bash

    python -m ble2wled.cli_simulator --led-count 60 --beacons 3

You should see an animated LED grid with colorful moving beacons.

4. Real-Time Statistics
------------------------

The simulator can display real-time MQTT statistics:

.. code-block:: bash

    python -m ble2wled.cli_simulator --mqtt \
      --mqtt-broker localhost \
      --mqtt-location living_room \
      --led-count 60

This connects to a live MQTT broker and displays:
- Number of messages received
- Messages per second
- Number of active beacons
- Current frame rate
- Total elapsed time

5. Python API (Production)
---------------------------

For production use with a real WLED device:

.. code-block:: python

    from ble2wled.config import Config
    from ble2wled.states import BeaconState
    from ble2wled.mqtt import EspresenseBeaconListener
    from ble2wled.wled import WLEDUDPController
    from ble2wled.animation import run_wled_beacons

    # Load configuration from .env
    config = Config('.env')

    # Validate configuration
    config.validate()

    # Create beacon state tracker
    beacon_state = BeaconState(
        timeout_seconds=6.0,
        fade_out_seconds=4.0
    )

    # Create MQTT listener
    mqtt_listener = EspresenseBeaconListener(
        beacon_state,
        broker=config.mqtt_broker,
        port=config.mqtt_port,
        location=config.mqtt_location,
        username=config.mqtt_username,
        password=config.mqtt_password
    )
    mqtt_listener.start()

    # Create WLED controller (UDP is faster)
    controller = WLEDUDPController(
        host=config.wled_host,
        led_count=config.led_count
    )

    # Run animation loop
    run_wled_beacons(
        controller,
        led_count=config.led_count,
        beacon_state=beacon_state,
        update_interval=0.05,      # 50ms updates
        trail_length=10,
        fade_factor=0.75
    )

6. HTTP Alternative
--------------------

If your WLED device doesn't support UDP, use HTTP instead:

.. code-block:: python

    from ble2wled.wled import WLEDHTTPController

    # Create HTTP controller with automatic retry on timeout
    controller = WLEDHTTPController(
        host=config.wled_host,
        led_count=config.led_count,
        timeout=1.0,        # 1 second timeout
        max_retries=3       # Retry 3 times on timeout
    )

    # Use same animation loop
    run_wled_beacons(controller, ...)

7. Configuration with Authentication
-------------------------------------

If your MQTT broker requires authentication:

.. code-block:: bash

    # Add to .env
    MQTT_USERNAME=my_username
    MQTT_PASSWORD=my_password

Or via CLI:

.. code-block:: bash

    python -m ble2wled.cli_simulator --mqtt \
      --mqtt-broker 192.168.1.100 \
      --mqtt-location living_room \
      --mqtt-username my_user \
      --mqtt-password my_pass \
      --led-count 60

Next Steps
----------

- :doc:`guides/configuration` - Full configuration reference
- :doc:`guides/cli_simulator` - Advanced simulator usage
- :doc:`guides/mqtt_authentication` - MQTT authentication setup
- :doc:`guides/http_retry_logic` - Understanding HTTP retry behavior
- :doc:`api/modules` - Full API documentation
