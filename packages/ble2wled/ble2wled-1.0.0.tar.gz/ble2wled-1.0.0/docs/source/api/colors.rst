:mod:`ble2wled.colors` - Color Calculations
============================================

.. automodule:: ble2wled.colors
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The ``colors`` module provides color calculations for LED visualization, including:

- Distance-to-color mapping (position on LED strip → hue)
- Signal strength mapping (RSSI → brightness)
- HSV to RGB conversion
- Color utilities for beacon visualization

Color Strategy
~~~~~~~~~~~~~~

BLE2WLED uses a sophisticated color mapping strategy:

1. **Hue Assignment** - Each beacon gets a unique hue based on its ID (hash-based)
2. **Distance Mapping** - Distance from transmitter maps to saturation/value
3. **Signal Strength** - RSSI maps to brightness
4. **Motion Trails** - Recent positions brightest, fade out over time

Quick Example
~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.colors import (
        position_to_color_hue,
        rssi_to_brightness,
        beacon_id_to_hue,
        hsv_to_rgb
    )

    # Get hue for a position on the LED strip
    position = 30  # Middle of 60-LED strip
    hue = position_to_color_hue(position, led_count=60)
    print(f"Position {position} → Hue {hue}")

    # Get brightness from signal strength
    rssi = -50
    brightness = rssi_to_brightness(rssi)
    print(f"RSSI {rssi} → Brightness {brightness}")

    # Get unique color for each beacon
    beacon_id = "device_123"
    beacon_hue = beacon_id_to_hue(beacon_id)
    print(f"Beacon {beacon_id} → Hue {beacon_hue}")

    # Convert HSV to RGB
    h, s, v = beacon_hue, 0.8, 1.0
    r, g, b = hsv_to_rgb(h, s, v)
    print(f"HSV({h}, {s}, {v}) → RGB({r}, {g}, {b})")

Functions
---------

position_to_color_hue()
~~~~~~~~~~~~~~~~~~~~~~~

Map a position on the LED strip to a color hue.

**Parameters:**

- ``position`` (float) - Position on LED strip (0 to led_count)
- ``led_count`` (int) - Total number of LEDs

**Returns:**

- ``float`` - Hue value (0-360 degrees)

**Example:**

.. code-block:: python

    from ble2wled.colors import position_to_color_hue

    # 60-LED strip
    hue_start = position_to_color_hue(0, 60)      # Red (0°)
    hue_middle = position_to_color_hue(30, 60)    # Cyan (180°)
    hue_end = position_to_color_hue(59, 60)       # Purple (359°)

rssi_to_brightness()
~~~~~~~~~~~~~~~~~~~~

Map signal strength (RSSI) to brightness.

**Parameters:**

- ``rssi`` (int) - Signal strength in dBm (typically -20 to -100)

**Returns:**

- ``float`` - Brightness (0.0-1.0)

**Behavior:**

- Very strong signal (-20 to -30): brightness 1.0 (full)
- Strong signal (-30 to -50): brightness 0.8-1.0
- Medium signal (-50 to -70): brightness 0.3-0.8
- Weak signal (-70 to -100): brightness 0.0-0.3

**Example:**

.. code-block:: python

    from ble2wled.colors import rssi_to_brightness

    rssi_strong = -40
    rssi_weak = -80

    brightness_strong = rssi_to_brightness(rssi_strong)  # ~0.9
    brightness_weak = rssi_to_brightness(rssi_weak)      # ~0.2

beacon_id_to_hue()
~~~~~~~~~~~~~~~~~~

Get a unique, consistent hue for each beacon based on its ID.

**Parameters:**

- ``beacon_id`` (str) - Unique beacon identifier

**Returns:**

- ``float`` - Hue value (0-360 degrees)

**Behavior:**

- Same beacon ID always gets same hue
- Different beacon IDs get different hues
- Uses hash function for distribution

**Example:**

.. code-block:: python

    from ble2wled.colors import beacon_id_to_hue

    beacon1_hue = beacon_id_to_hue("device_123")
    beacon2_hue = beacon_id_to_hue("device_456")

    # Same beacon, same hue (consistent)
    assert beacon_id_to_hue("device_123") == beacon1_hue

    # Different beacon, different hue
    assert beacon1_hue != beacon2_hue

hsv_to_rgb()
~~~~~~~~~~~~

Convert HSV color to RGB.

**Parameters:**

- ``h`` (float) - Hue (0-360 degrees)
- ``s`` (float) - Saturation (0.0-1.0)
- ``v`` (float) - Value/Brightness (0.0-1.0)

**Returns:**

- ``tuple`` - RGB values (r, g, b) each 0-255

**Example:**

.. code-block:: python

    from ble2wled.colors import hsv_to_rgb

    # Red
    r, g, b = hsv_to_rgb(0, 1.0, 1.0)
    assert (r, g, b) == (255, 0, 0)

    # Green
    r, g, b = hsv_to_rgb(120, 1.0, 1.0)
    assert (r, g, b) == (0, 255, 0)

    # Blue
    r, g, b = hsv_to_rgb(240, 1.0, 1.0)
    assert (r, g, b) == (0, 0, 255)

    # Gray (low saturation)
    r, g, b = hsv_to_rgb(0, 0.0, 0.5)
    assert (r, g, b) == (128, 128, 128)

Examples
--------

Complete Color Calculation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.colors import (
        position_to_color_hue,
        rssi_to_brightness,
        beacon_id_to_hue,
        hsv_to_rgb
    )

    # For a beacon at position 30 with RSSI -50
    beacon_id = "device_123"
    position = 30
    rssi = -50
    led_count = 60

    # Get base hue from beacon ID (unique per beacon)
    hue = beacon_id_to_hue(beacon_id)

    # Get saturation from position (distance-based)
    # Closer beacons are more saturated
    position_hue = position_to_color_hue(position, led_count)
    saturation = 1.0 - abs(hue - position_hue) / 180.0

    # Get brightness from signal strength
    brightness = rssi_to_brightness(rssi)

    # Convert HSV to RGB for LED
    r, g, b = hsv_to_rgb(hue, saturation, brightness)

    print(f"Beacon {beacon_id} at LED {position}")
    print(f"  HSV: ({hue:.1f}°, {saturation:.2f}, {brightness:.2f})")
    print(f"  RGB: ({r}, {g}, {b})")

Multiple Beacons
~~~~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.colors import beacon_id_to_hue, hsv_to_rgb

    beacons = {
        "device_1": {"position": 10, "rssi": -45},
        "device_2": {"position": 30, "rssi": -60},
        "device_3": {"position": 50, "rssi": -75},
    }

    for beacon_id, data in beacons.items():
        hue = beacon_id_to_hue(beacon_id)
        # ... calculate saturation, brightness ...
        r, g, b = hsv_to_rgb(hue, 0.8, brightness)
        print(f"{beacon_id}: RGB({r}, {g}, {b})")

Gradient Visualization
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.colors import position_to_color_hue, hsv_to_rgb

    # Show color gradient across LED strip
    led_count = 60
    for position in range(0, led_count, 10):
        hue = position_to_color_hue(position, led_count)
        r, g, b = hsv_to_rgb(hue, 1.0, 1.0)
        print(f"LED {position:2d}: RGB({r:3d}, {g:3d}, {b:3d})")

Signal Strength Visualization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.colors import rssi_to_brightness, hsv_to_rgb

    # Show brightness at different signal strengths
    rssi_values = [-30, -50, -70, -90]
    hue = 120  # Green

    for rssi in rssi_values:
        brightness = rssi_to_brightness(rssi)
        r, g, b = hsv_to_rgb(hue, 1.0, brightness)
        print(f"RSSI {rssi:3d} dBm: Brightness {brightness:.2f} → RGB({r}, {g}, {b})")

See Also
--------

- :doc:`states` - Beacon state with position and RSSI
- :doc:`animation` - Animation loop using colors
- :doc:`../guides/configuration` - Configure trail and fade
