:mod:`ble2wled.states` - Beacon State Management
================================================

.. automodule:: ble2wled.states
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The ``states`` module manages beacon state and lifecycle. It tracks:

- Active beacons and their positions
- Signal strength (RSSI) over time
- Beacon timeouts (when beacons disappear)
- Fade-out animations for departing beacons

Key Classes
-----------

**Beacon**

Represents a single beacon with its current state.

**BeaconState**

Tracks all active and fading beacons.

Quick Example
~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.states import BeaconState, Beacon

    # Create beacon state tracker
    state = BeaconState(
        timeout_seconds=6.0,      # Beacon times out after 6 seconds
        fade_out_seconds=4.0      # Fade out over 4 seconds after timeout
    )

    # Add a beacon (usually from MQTT)
    state.update_or_create(
        beacon_id='device_123',
        position=30,              # Position on LED strip (0-60)
        rssi=-45                  # Signal strength in dBm
    )

    # Get active beacon
    beacon = state.beacons['device_123']
    print(f"Position: {beacon.position}, RSSI: {beacon.rssi}")

    # Check if beacon is in timeout
    if beacon.is_in_timeout:
        print("Beacon has timed out!")

    # Update beacon positions/signals
    state.update_or_create('device_123', position=32, rssi=-48)

    # Cleanup expired beacons
    state.cleanup()

Classes
-------

Beacon
~~~~~~

A single beacon with position and signal information.

**Attributes:**

- ``beacon_id`` (str) - Unique beacon identifier
- ``position`` (float) - Position on LED strip (0 to led_count)
- ``rssi`` (int) - Signal strength in dBm (typically -20 to -100)
- ``last_update_time`` (float) - Timestamp of last update
- ``timeout_at`` (float) - Timestamp when beacon times out
- ``is_in_timeout`` (bool) - Whether beacon has timed out

**Methods:**

- ``should_be_removed(current_time: float) -> bool`` - Check if beacon should be removed
- ``get_fade_factor(current_time: float) -> float`` - Get fade factor (0.0-1.0) during fade-out

BeaconState
~~~~~~~~~~~

Tracks all active and fading beacons.

**Attributes:**

- ``beacons`` (Dict[str, Beacon]) - Active and fading beacons
- ``timeout_seconds`` (float) - Beacon timeout duration
- ``fade_out_seconds`` (float) - Fade-out animation duration

**Methods:**

- ``update_or_create(beacon_id: str, position: float, rssi: int)`` - Update or create beacon
- ``cleanup()`` - Remove expired beacons
- ``clear()`` - Remove all beacons

Examples
--------

Basic Beacon Tracking
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.states import BeaconState

    state = BeaconState()

    # Update beacon position and signal
    state.update_or_create('beacon_1', position=15, rssi=-50)
    state.update_or_create('beacon_2', position=45, rssi=-60)

    # Check active beacons
    print(f"Active beacons: {len(state.beacons)}")
    for beacon_id, beacon in state.beacons.items():
        print(f"  {beacon_id}: pos={beacon.position}, rssi={beacon.rssi}")

Beacon Lifecycle
~~~~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.states import BeaconState
    import time

    state = BeaconState(timeout_seconds=2.0, fade_out_seconds=1.0)

    # Beacon appears
    state.update_or_create('device_1', position=30, rssi=-45)
    print(f"Beacon active: {state.beacons['device_1'].is_in_timeout}")  # False

    # After 2 seconds without update: beacon times out
    time.sleep(2.1)
    print(f"Beacon timed out: {state.beacons['device_1'].is_in_timeout}")  # True

    # Get fade factor for animation
    fade = state.beacons['device_1'].get_fade_factor(time.time())
    print(f"Fade factor: {fade}")  # 0.5 (halfway through fade-out)

    # After 3 seconds: beacon is removed
    time.sleep(1.0)
    state.cleanup()
    print(f"Beacon count: {len(state.beacons)}")  # 0

MQTT Integration
~~~~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.states import BeaconState
    from ble2wled.mqtt import EspresenseBeaconListener

    state = BeaconState()

    # MQTT listener updates beacon state automatically
    listener = EspresenseBeaconListener(
        state,
        broker='localhost',
        location='living_room'
    )
    listener.start()

    # Beacon state is automatically updated from MQTT
    time.sleep(0.1)
    for beacon_id, beacon in state.beacons.items():
        print(f"{beacon_id}: {beacon.position} @ {beacon.rssi} dBm")

Animation Integration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.states import BeaconState
    from ble2wled.colors import position_to_color_hue

    state = BeaconState()
    state.update_or_create('beacon_1', position=30, rssi=-50)

    # Get beacon for animation
    beacon = state.beacons['beacon_1']

    # Calculate color based on distance/signal
    hue = position_to_color_hue(beacon.position, led_count=60)
    print(f"Color hue: {hue}")

    # Use fade factor if beacon is timing out
    brightness = 1.0 * beacon.get_fade_factor(time.time())
    print(f"Brightness: {brightness}")

Custom Timeout Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.states import BeaconState

    # Fast timeout: 2 seconds active, 1 second fade-out
    state_fast = BeaconState(timeout_seconds=2.0, fade_out_seconds=1.0)

    # Slow timeout: 10 seconds active, 5 seconds fade-out
    state_slow = BeaconState(timeout_seconds=10.0, fade_out_seconds=5.0)

    # Very persistent: 30 seconds before timeout
    state_persistent = BeaconState(timeout_seconds=30.0, fade_out_seconds=2.0)

See Also
--------

- :doc:`../guides/configuration` - Configure timeout values
- :doc:`colors` - Color mapping for beacons
- :doc:`animation` - Animation loop using beacon state
- :doc:`mqtt` - MQTT listener that updates beacon state
