:mod:`ble2wled.animation` - Animation Loop
===========================================

.. automodule:: ble2wled.animation
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The ``animation`` module provides the main animation loop and LED rendering logic. It:

- Processes beacon state into LED colors
- Renders motion trails
- Handles fade-out animations
- Updates WLED device at regular intervals

Key Function
~~~~~~~~~~~~

``run_wled_beacons()`` is the main entry point for running beacon visualization.

Quick Example
~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.config import Config
    from ble2wled.states import BeaconState
    from ble2wled.mqtt import EspresenseBeaconListener
    from ble2wled.wled import WLEDUDPController
    from ble2wled.animation import run_wled_beacons

    # Load configuration
    config = Config('.env')

    # Create beacon state and MQTT listener
    beacon_state = BeaconState()
    mqtt_listener = EspresenseBeaconListener(
        beacon_state,
        broker=config.mqtt_broker,
        location=config.mqtt_location
    )
    mqtt_listener.start()

    # Create WLED controller
    controller = WLEDUDPController(config.wled_host, config.led_count)

    # Run animation loop (blocking)
    run_wled_beacons(
        controller,
        led_count=config.led_count,
        beacon_state=beacon_state
    )

Functions
---------

run_wled_beacons()
~~~~~~~~~~~~~~~~~~

Main animation loop for beacon visualization.

**Parameters:**

- ``controller`` - WLED device controller (WLEDHTTPController or WLEDUDPController)
- ``led_count`` (int) - Total number of LEDs
- ``beacon_state`` (BeaconState) - Beacon state tracker
- ``update_interval`` (float, default 0.05) - Update interval in seconds (50ms = 20fps)
- ``trail_length`` (int, default 8) - Length of motion trail in LEDs
- ``fade_factor`` (float, default 0.75) - Trail fade factor (0.1-1.0)

**Behavior:**

The function runs a continuous animation loop:

1. **Read beacon state** - Get active and fading beacons
2. **Initialize LED array** - Create array of [R, G, B] for each LED
3. **Render trails** - For each beacon, render motion trail on LEDs
4. **Apply fade-out** - Reduce brightness for beacons in timeout
5. **Update device** - Send LED array to WLED controller
6. **Cleanup** - Remove expired beacons
7. **Sleep** - Wait update_interval before next iteration

**Raises:**

- ``KeyboardInterrupt`` - When user presses Ctrl+C

**Example:**

.. code-block:: python

    from ble2wled.animation import run_wled_beacons
    from ble2wled.wled import WLEDUDPController
    from ble2wled.states import BeaconState

    state = BeaconState()
    controller = WLEDUDPController('192.168.1.100', 60)

    try:
        run_wled_beacons(
            controller,
            led_count=60,
            beacon_state=state,
            update_interval=0.05,      # 20fps
            trail_length=10,           # 10-LED trail
            fade_factor=0.75           # Dim trail
        )
    except KeyboardInterrupt:
        print("Animation stopped")

Animation Parameters
---------------------

Update Interval
~~~~~~~~~~~~~~~

Controls animation smoothness and CPU usage.

**Values:**

- ``0.02`` - 50fps (very smooth, high CPU)
- ``0.05`` - 20fps (good balance, recommended)
- ``0.1`` - 10fps (lower CPU, less smooth)
- ``0.2`` - 5fps (low CPU, clearly animated)

**Example:**

.. code-block:: python

    # Fast animation
    run_wled_beacons(controller, ..., update_interval=0.02)

    # Smooth default
    run_wled_beacons(controller, ..., update_interval=0.05)

    # CPU efficient
    run_wled_beacons(controller, ..., update_interval=0.1)

Trail Length
~~~~~~~~~~~~

Number of LEDs the motion trail extends backward from beacon position.

**Values:**

- ``4`` - Short trails (just position)
- ``8`` - Medium trails (default)
- ``15`` - Long trails (motion effect)
- ``30`` - Very long trails (significant motion history)

**Example:**

.. code-block:: python

    # Short trail
    run_wled_beacons(controller, ..., trail_length=4)

    # Medium trail (default)
    run_wled_beacons(controller, ..., trail_length=8)

    # Long trail (motion effect)
    run_wled_beacons(controller, ..., trail_length=15)

Fade Factor
~~~~~~~~~~~

How much each trail segment fades compared to the previous.

**Values:**

- ``0.1`` - Fast fade (dim trails)
- ``0.5`` - Medium fade
- ``0.75`` - Default fade
- ``0.9`` - Slow fade (bright trails)

**Behavior:**

For a trail with ``trail_length=8`` and ``fade_factor=0.75``:

- Position 0 (current): brightness 1.0
- Position 1: brightness 0.75
- Position 2: brightness 0.56 (0.75²)
- Position 3: brightness 0.42 (0.75³)
- ... and so on

**Example:**

.. code-block:: python

    # Dim trails
    run_wled_beacons(controller, ..., fade_factor=0.5)

    # Medium trails (default)
    run_wled_beacons(controller, ..., fade_factor=0.75)

    # Bright trails
    run_wled_beacons(controller, ..., fade_factor=0.9)

Examples
--------

Basic Animation Loop
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.animation import run_wled_beacons
    from ble2wled.states import BeaconState
    from ble2wled.wled import WLEDUDPController
    from ble2wled.simulator import MockBeaconGenerator

    # Setup
    state = BeaconState()
    controller = WLEDUDPController('192.168.1.100', 60)

    # Generate mock beacons for testing
    generator = MockBeaconGenerator(state, 3, 60)
    generator.start()

    # Run animation
    try:
        run_wled_beacons(controller, 60, state)
    finally:
        generator.stop()

With MQTT
~~~~~~~~~

.. code-block:: python

    from ble2wled.animation import run_wled_beacons
    from ble2wled.states import BeaconState
    from ble2wled.mqtt import EspresenseBeaconListener
    from ble2wled.wled import WLEDUDPController

    # Setup
    state = BeaconState()
    listener = EspresenseBeaconListener(state, 'localhost', 'living_room')
    controller = WLEDUDPController('192.168.1.100', 60)

    # Start listener
    listener.start()

    # Run animation
    try:
        run_wled_beacons(
            controller,
            led_count=60,
            beacon_state=state,
            update_interval=0.05,
            trail_length=8,
            fade_factor=0.75
        )
    finally:
        listener.stop()

With Custom Parameters
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.animation import run_wled_beacons
    from ble2wled.config import Config
    from ble2wled.states import BeaconState
    from ble2wled.wled import WLEDUDPController

    # Load configuration
    config = Config('.env')

    # Create components
    state = BeaconState(
        timeout_seconds=config.beacon_timeout_seconds,
        fade_out_seconds=config.beacon_fade_out_seconds
    )
    controller = WLEDUDPController(config.wled_host, config.led_count)

    # Run with configuration values
    run_wled_beacons(
        controller,
        led_count=config.led_count,
        beacon_state=state,
        update_interval=config.animation_update_interval,
        trail_length=config.animation_trail_length,
        fade_factor=config.animation_fade_factor
    )

Performance Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**For smooth 20fps animation on 60 LEDs:**

.. code-block:: python

    run_wled_beacons(
        controller,
        led_count=60,
        beacon_state=state,
        update_interval=0.05        # 20fps
    )

**For CPU-constrained systems:**

.. code-block:: python

    run_wled_beacons(
        controller,
        led_count=60,
        beacon_state=state,
        update_interval=0.1,        # 10fps
        trail_length=4,             # Shorter trail
        fade_factor=0.5             # Faster fade
    )

**For high-end systems with more LEDs:**

.. code-block:: python

    run_wled_beacons(
        controller,
        led_count=300,              # More LEDs
        beacon_state=state,
        update_interval=0.02,       # 50fps
        trail_length=15,            # Longer trail
        fade_factor=0.9             # Slower fade
    )

Debugging Animation
~~~~~~~~~~~~~~~~~~~

To debug animation issues, capture LED data before sending:

.. code-block:: python

    from ble2wled.animation import run_wled_beacons
    from ble2wled.wled import WLEDUDPController

    class DebugController(WLEDUDPController):
        def update(self, leds):
            # Print first 10 LEDs
            print(f"LEDs: {leds[:10]}")
            super().update(leds)

    controller = DebugController('192.168.1.100', 60)
    run_wled_beacons(controller, 60, state)

See Also
--------

- :doc:`states` - Beacon state tracking
- :doc:`colors` - Color calculations
- :doc:`wled` - WLED device communication
- :doc:`../guides/configuration` - Configure animation parameters
