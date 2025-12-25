CLI Simulator Guide
===================

The BLE2WLED simulator provides a command-line interface for testing beacon visualization without requiring a real WLED device or MQTT broker.

Features
--------

- **Visual LED Display** - Renders LED strip as a colored grid in the terminal using ANSI 24-bit colors
- **Mock Beacon Generation** - Simulates realistic BLE beacon movement and signal strength
- **Configurable Parameters** - Customize LED count, grid layout, beacon count, and animation settings
- **Live MQTT Connection** - Connect to real MQTT broker to test with actual beacon data
- **Real-time Statistics** - Display message rates, active beacons, and frame rate
- **Headless Testing** - Run simulations in CI/CD pipelines or headless environments

Basic Usage
-----------

Run the simulator with default settings (60 LEDs, 3 beacons):

.. code-block:: bash

    python -m ble2wled.cli_simulator

This displays an animated grid of LEDs with colorful moving beacons in your terminal.

Press ``Ctrl+C`` to exit.

Command-Line Options
---------------------

::

    --led-count LED_COUNT
        Total number of LEDs in the strip (default: 60)
        Valid range: 1-1024

    --rows ROWS
        Display grid rows (default: 10)
        Lower values = taller display

    --cols COLS
        Display grid columns (default: 6)
        Higher values = wider display

    --beacons BEACONS
        Number of mock beacons to simulate (default: 3)
        Valid range: 1-50

    --update-interval UPDATE_INTERVAL
        Update interval in seconds (default: 0.1)
        Lower = smoother animation but higher CPU
        Valid range: 0.01-1.0

    --trail-length TRAIL_LENGTH
        Length of motion trail in LEDs (default: 8)
        Valid range: 1-100

    --fade-factor FADE_FACTOR
        Trail fade factor 0-1 (default: 0.7)
        0.9 = slow fade, 0.1 = fast fade

    --duration DURATION
        Run duration in seconds (default: infinite)
        Useful for automated testing

    --mqtt
        Connect to real MQTT broker instead of generating mock beacons

    --mqtt-broker BROKER
        MQTT broker hostname/IP (default: localhost)

    --mqtt-port PORT
        MQTT broker port (default: 1883)

    --mqtt-location LOCATION
        Beacon location/room (default: test)
        Topic: espresense/devices/{LOCATION}

    --mqtt-username USERNAME
        MQTT username for authentication (optional)

    --mqtt-password PASSWORD
        MQTT password for authentication (optional)

    --help
        Show help message

Basic Examples
--------------

**120-LED strip with 5 beacons:**

.. code-block:: bash

    python -m ble2wled.cli_simulator --led-count 120 --beacons 5

**Run for 30 seconds with faster updates:**

.. code-block:: bash

    python -m ble2wled.cli_simulator --duration 30 --update-interval 0.05

**Custom grid layout with longer trails:**

.. code-block:: bash

    python -m ble2wled.cli_simulator --led-count 100 --rows 20 --cols 5 --trail-length 15

**Small display for narrow terminals:**

.. code-block:: bash

    python -m ble2wled.cli_simulator --led-count 60 --rows 5 --cols 12

**High-speed animation (50fps):**

.. code-block:: bash

    python -m ble2wled.cli_simulator --update-interval 0.02

**Slow animation (5fps):**

.. code-block:: bash

    python -m ble2wled.cli_simulator --update-interval 0.2

Live MQTT Examples
------------------

Connect to a real MQTT broker and visualize actual beacon data:

**Basic MQTT connection:**

.. code-block:: bash

    python -m ble2wled.cli_simulator --mqtt \
      --mqtt-broker localhost \
      --mqtt-location living_room

**MQTT with custom grid layout:**

.. code-block:: bash

    python -m ble2wled.cli_simulator --mqtt \
      --mqtt-broker 192.168.1.100 \
      --mqtt-location bedroom \
      --led-count 60 \
      --rows 12 \
      --cols 5

**MQTT with authentication:**

.. code-block:: bash

    python -m ble2wled.cli_simulator --mqtt \
      --mqtt-broker 192.168.1.100 \
      --mqtt-port 1883 \
      --mqtt-location office \
      --mqtt-username mqtt_user \
      --mqtt-password my_password \
      --led-count 100

**MQTT with real-time statistics display:**

The simulator automatically displays real-time statistics when using MQTT:

::

    MQTT: 342 msgs | 12.3 msg/s | Beacons: 8 | FPS: 9.8 | Time: 00:02:34

This shows:
- **342 msgs** - Total messages received
- **12.3 msg/s** - Message rate per second
- **Beacons: 8** - Number of active beacons
- **FPS: 9.8** - Animation frame rate
- **Time: 00:02:34** - Elapsed time

Python API
----------

Use the simulator programmatically in your code:

**Using LEDSimulator with mock beacons:**

.. code-block:: python

    from ble2wled.simulator import LEDSimulator
    from ble2wled.states import BeaconState
    from ble2wled.animation import run_wled_beacons

    # Create simulator (60 LEDs in 10×6 grid)
    simulator = LEDSimulator(led_count=60, rows=10, cols=6)

    # Create beacon state
    beacon_state = BeaconState()

    # Generate some beacons for testing
    from ble2wled.simulator import MockBeaconGenerator
    generator = MockBeaconGenerator(
        beacon_state,
        num_beacons=3,
        led_count=60
    )
    generator.start()

    # Run animation loop with simulator
    run_wled_beacons(
        simulator,
        led_count=60,
        beacon_state=beacon_state,
        update_interval=0.1,
        trail_length=8,
        fade_factor=0.7
    )

**Using MockBeaconGenerator for testing:**

.. code-block:: python

    from ble2wled.simulator import MockBeaconGenerator
    from ble2wled.states import BeaconState

    # Create beacon state
    beacon_state = BeaconState()

    # Create mock beacon generator
    generator = MockBeaconGenerator(
        beacon_state,
        num_beacons=5,
        led_count=60,
        update_interval=0.5
    )

    # Start generating mock beacons
    generator.start()

    # Use beacon_state in your animation loop
    for beacon_id, beacon in beacon_state.beacons.items():
        print(f"Beacon {beacon_id}: pos={beacon.position}, rssi={beacon.rssi}")

    # Stop generator
    generator.stop()

Display Output
--------------

The simulator displays LEDs as colored blocks in a grid:

**Example output with 60 LEDs (10×6 grid) and 3 beacons:**

::

    ██████████████████████████████
    ██████████████████████████████
    ██████████████████████████████
    ███░░░░███░░░░██████████░░████
    ██░░░░░░░░░░░░██████████████░░
    ██░░░░░░░░░░░░██████████░░░░░░
    ██████████░░░░██░░░░██░░░░░░░░
    ██████████░░░░██░░░░██░░░░░░░░
    ██████████░░░░██░░░░██░░░░░░░░
    ██████████████████████████░░░░

- **Colors** represent different beacons (hash-based hue)
- **Brightness** represents signal strength (RSSI)
- **Trails** show recent beacon positions (fading backward)

Troubleshooting
~~~~~~~~~~~~~~~

**Nothing displays or "broken pipe" error:**

Try using a smaller grid:

.. code-block:: bash

    python -m ble2wled.cli_simulator --rows 5 --cols 12

**MQTT connection refuses:**

Check:
1. MQTT broker is running: ``telnet localhost 1883``
2. Correct broker address: ``--mqtt-broker <your-broker>``
3. Correct location: ``--mqtt-location <location>``
4. Network connectivity: ``ping <broker-ip>``

**Animation is choppy or slow:**

Reduce complexity:

.. code-block:: bash

    python -m ble2wled.cli_simulator --rows 5 --cols 10 --update-interval 0.2

**No beacons appear on MQTT:**

Ensure:
1. MQTT broker is receiving messages: ``mosquitto_sub -t "espresense/devices/+/+"``
2. Correct location in command matches espresense devices
3. Espresense devices are actively scanning

Performance Tips
~~~~~~~~~~~~~~~~

**For smooth animation:**

- Use ``--update-interval 0.05`` for 20fps (good balance)
- Keep grid under 120 LEDs for smooth display
- Use ``--trail-length 8`` or lower for lower-end systems

**For CPU-constrained systems:**

- Increase ``--update-interval`` to 0.2 (5fps)
- Reduce ``--rows`` and ``--cols`` for smaller grid
- Reduce ``--trail-length`` to 4 or less

**For high-speed animation:**

- Use ``--update-interval 0.02`` for 50fps (requires fast terminal)
- Keep grid reasonably sized (50-100 LEDs)

Next Steps
----------

- :doc:`configuration` - Learn about configuration options
- :doc:`mqtt_authentication` - Set up authenticated MQTT
- :doc:`http_retry_logic` - Understand HTTP retry behavior
- :doc:`../api/simulator` - Simulator API reference
