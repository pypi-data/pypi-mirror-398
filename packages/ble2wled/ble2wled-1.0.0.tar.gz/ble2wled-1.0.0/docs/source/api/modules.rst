API Reference
=============

Complete API reference for BLE2WLED modules.

.. toctree::
   :maxdepth: 2

   config
   states
   colors
   animation
   wled
   mqtt
   simulator

Overview
--------

BLE2WLED consists of several modular components:

**Configuration Management**
  - :doc:`config` - Load and manage configuration from environment variables

**Beacon State Tracking**
  - :doc:`states` - Track beacon positions, signals, and lifecycles

**Visualization**
  - :doc:`colors` - Color mapping and HSV calculations
  - :doc:`animation` - Animation loop and LED rendering
  - :doc:`wled` - WLED device communication (HTTP/UDP)

**Input**
  - :doc:`mqtt` - MQTT listener for beacon data

**Testing**
  - :doc:`simulator` - LED simulator and mock beacon generation

Module Dependencies
~~~~~~~~~~~~~~~~~~~

::

    config.py
        └─> Loads environment variables and .env files

    states.py
        └─> Tracks beacon state over time

    mqtt.py
        ├─> Depends on states.py
        └─> Provides beacon data to states

    colors.py
        └─> Converts distance/signal to LED colors

    animation.py
        ├─> Depends on states.py, colors.py, wled.py
        └─> Main animation loop

    wled.py
        └─> Communicates with physical WLED devices

    simulator.py
        ├─> Depends on states.py
        └─> Mock WLED controller for testing

Usage Example
~~~~~~~~~~~~~

Typical application flow:

.. code-block:: python

    # 1. Load configuration
    from ble2wled.config import Config
    config = Config('.env')

    # 2. Create beacon state tracker
    from ble2wled.states import BeaconState
    beacon_state = BeaconState()

    # 3. Start MQTT listener (provides beacon data)
    from ble2wled.mqtt import EspresenseBeaconListener
    listener = EspresenseBeaconListener(
        beacon_state,
        broker=config.mqtt_broker,
        location=config.mqtt_location
    )
    listener.start()

    # 4. Create WLED controller
    from ble2wled.wled import WLEDUDPController
    controller = WLEDUDPController(config.wled_host, config.led_count)

    # 5. Run animation loop
    from ble2wled.animation import run_wled_beacons
    run_wled_beacons(
        controller,
        beacon_state=beacon_state,
        led_count=config.led_count
    )
