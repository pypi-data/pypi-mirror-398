:mod:`ble2wled.simulator` - LED Simulator and Mock Beacons
==========================================================

.. automodule:: ble2wled.simulator
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The ``simulator`` module provides tools for testing beacon visualization without requiring a real WLED device or MQTT broker. It includes:

- **LEDSimulator** - Visual LED display in terminal using ANSI colors
- **MockBeaconGenerator** - Generates realistic simulated beacon data
- **CLI interface** - Command-line tool for testing

Quick Example
~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.simulator import LEDSimulator, MockBeaconGenerator
    from ble2wled.states import BeaconState
    from ble2wled.animation import run_wled_beacons

    # Create simulator
    simulator = LEDSimulator(led_count=60, rows=10, cols=6)

    # Create beacon state
    state = BeaconState()

    # Generate mock beacons
    generator = MockBeaconGenerator(state, num_beacons=3, led_count=60)
    generator.start()

    # Run animation
    try:
        run_wled_beacons(simulator, 60, state, update_interval=0.1)
    finally:
        generator.stop()

Classes
-------

LEDSimulator
~~~~~~~~~~~~

Displays LEDs as colored blocks in terminal using ANSI 24-bit colors.

**Attributes:**

- ``led_count`` (int) - Total number of LEDs
- ``rows`` (int, default 10) - Grid rows
- ``cols`` (int, default 6) - Grid columns
- ``width`` (int) - Terminal width needed (cols * 4)
- ``height`` (int) - Terminal height needed (rows + 5)

**Methods:**

- ``update(leds: List[List[int]])`` - Display LED data
- ``clear()`` - Clear display

**Requirements:**

- Terminal must support ANSI 24-bit colors
- Terminal width must be at least ``cols * 4``
- Terminal height must be at least ``rows + 5``

**Example:**

.. code-block:: python

    from ble2wled.simulator import LEDSimulator

    # Create 60-LED display in 10×6 grid
    simulator = LEDSimulator(led_count=60, rows=10, cols=6)

    # Display colors
    leds = [[255, 0, 0]] * 30 + [[0, 255, 0]] * 30
    simulator.update(leds)

    # Clear display
    simulator.clear()

LED Count and Grid Layout
~~~~~~~~~~~~~~~~~~~~~~~~~~

The LED count must equal rows × cols:

.. code-block:: python

    # 60 LEDs (10 rows × 6 columns)
    sim = LEDSimulator(led_count=60, rows=10, cols=6)

    # 100 LEDs (20 rows × 5 columns)
    sim = LEDSimulator(led_count=100, rows=20, cols=5)

    # 120 LEDs (12 rows × 10 columns)
    sim = LEDSimulator(led_count=120, rows=12, cols=10)

MockBeaconGenerator
~~~~~~~~~~~~~~~~~~~

Generates simulated beacon data for testing.

**Attributes:**

- ``beacon_state`` (BeaconState) - State to update with beacons
- ``num_beacons`` (int) - Number of beacons to simulate
- ``led_count`` (int) - Total LEDs (for position bounds)
- ``update_interval`` (float, default 0.1) - Update interval in seconds

**Methods:**

- ``start()`` - Start generating beacons (non-blocking, background thread)
- ``stop()`` - Stop generator
- ``is_running`` (property) - Whether generator is running

**Behavior:**

Generates random beacon movements:

- Beacons move randomly along LED strip
- RSSI values change realistically (-20 to -90 dBm)
- Updates at specified interval
- Beacons persist until stopped

**Example:**

.. code-block:: python

    from ble2wled.simulator import MockBeaconGenerator
    from ble2wled.states import BeaconState

    state = BeaconState()

    # Generate 5 mock beacons
    gen = MockBeaconGenerator(state, num_beacons=5, led_count=60)
    gen.start()

    # Beacons are now updating in background
    import time
    time.sleep(5)

    # Stop generator
    gen.stop()

Examples
--------

Visual LED Display
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.simulator import LEDSimulator
    from ble2wled.states import BeaconState
    from ble2wled.colors import beacon_id_to_hue, hsv_to_rgb
    import time

    # Create display
    simulator = LEDSimulator(led_count=60, rows=10, cols=6)
    state = BeaconState()

    # Add some beacons
    state.update_or_create('beacon_1', position=15, rssi=-50)
    state.update_or_create('beacon_2', position=30, rssi=-60)
    state.update_or_create('beacon_3', position=45, rssi=-70)

    # Render beacons
    leds = [[0, 0, 0]] * 60
    for beacon_id, beacon in state.beacons.items():
        pos = int(beacon.position)
        hue = beacon_id_to_hue(beacon_id)
        r, g, b = hsv_to_rgb(hue, 1.0, 1.0)
        leds[pos] = [r, g, b]

    # Display
    simulator.update(leds)

Mock Beacon Animation
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.simulator import LEDSimulator, MockBeaconGenerator
    from ble2wled.states import BeaconState
    from ble2wled.animation import run_wled_beacons

    # Setup
    simulator = LEDSimulator(led_count=60, rows=10, cols=6)
    state = BeaconState()

    # Generate mock beacons
    generator = MockBeaconGenerator(state, num_beacons=3, led_count=60)
    generator.start()

    # Run animation
    try:
        run_wled_beacons(
            simulator,
            led_count=60,
            beacon_state=state,
            update_interval=0.1,
            trail_length=8,
            fade_factor=0.75
        )
    finally:
        generator.stop()

Custom Grid Layouts
~~~~~~~~~~~~~~~~~~~

Adjust grid for different terminal sizes:

.. code-block:: python

    from ble2wled.simulator import LEDSimulator

    # Narrow terminal (12 columns wide)
    sim_narrow = LEDSimulator(led_count=60, rows=5, cols=12)

    # Wide terminal (4 columns wide)
    sim_wide = LEDSimulator(led_count=60, rows=15, cols=4)

    # Very wide display
    sim_very_wide = LEDSimulator(led_count=120, rows=6, cols=20)

Programmatic LED Display
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.simulator import LEDSimulator

    simulator = LEDSimulator(led_count=60, rows=10, cols=6)

    # Rainbow gradient
    leds = []
    for i in range(60):
        hue = (i / 60) * 360
        from ble2wled.colors import hsv_to_rgb
        r, g, b = hsv_to_rgb(hue, 1.0, 1.0)
        leds.append([r, g, b])

    simulator.update(leds)

Display Output Format
~~~~~~~~~~~~~~~~~~~~~

The simulator displays LEDs as colored blocks:

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

- Bright colors = bright LEDs
- Dim colors = dim LEDs
- Each block is one LED

CLI Usage
---------

Run simulator from command line:

.. code-block:: bash

    python -m ble2wled.cli_simulator

With options:

.. code-block:: bash

    python -m ble2wled.cli_simulator \
      --led-count 120 \
      --rows 12 \
      --cols 10 \
      --beacons 5 \
      --update-interval 0.05 \
      --trail-length 15 \
      --fade-factor 0.75 \
      --duration 60

With MQTT:

.. code-block:: bash

    python -m ble2wled.cli_simulator --mqtt \
      --mqtt-broker 192.168.1.100 \
      --mqtt-location living_room \
      --mqtt-username user \
      --mqtt-password pass

Performance
-----------

Terminal Requirements
~~~~~~~~~~~~~~~~~~~~~

For smooth animation:

- Terminal must support ANSI 24-bit colors
- Terminal width >= cols * 4
- Terminal height >= rows + 5
- Adequate CPU for rendering

Typical Performance
~~~~~~~~~~~~~~~~~~~

- 60 LEDs (10×6): ~50fps on modern CPU
- 120 LEDs (12×10): ~25fps
- 300 LEDs (20×15): ~5-10fps

Optimization Tips
~~~~~~~~~~~~~~~~~

For CPU-constrained systems:

.. code-block:: python

    # Use fewer LEDs
    simulator = LEDSimulator(led_count=30, rows=5, cols=6)

    # Use slower update interval
    run_wled_beacons(controller, ..., update_interval=0.2)

    # Use shorter trails
    run_wled_beacons(controller, ..., trail_length=4)

For high-speed animation:

.. code-block:: python

    # Use moderate LED count
    simulator = LEDSimulator(led_count=100, rows=10, cols=10)

    # Use fast update interval
    run_wled_beacons(controller, ..., update_interval=0.02)

Troubleshooting
~~~~~~~~~~~~~~~

**Nothing displays or error about terminal:**

Try smaller grid:

.. code-block:: python

    simulator = LEDSimulator(led_count=30, rows=5, cols=6)

**Colors look wrong:**

Ensure terminal supports 24-bit colors. Most modern terminals do.

**Animation stutters:**

Reduce LED count or increase update_interval.

See Also
--------

- :doc:`../guides/cli_simulator` - CLI simulator guide
- :doc:`animation` - Animation loop
- :doc:`states` - Beacon state
- :doc:`colors` - Color calculations
