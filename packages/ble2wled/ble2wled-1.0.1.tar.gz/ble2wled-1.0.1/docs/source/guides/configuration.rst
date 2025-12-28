Configuration
==============

BLE2WLED is configured using environment variables and .env files. This guide covers all configuration options.

Configuration Methods
---------------------

Configuration can be specified in three ways (in order of precedence):

1. **Environment variables** - Highest priority, override everything
2. **.env file** - Project-level configuration
3. **Default values** - Built-in defaults

Using .env File
~~~~~~~~~~~~~~~

The recommended approach is to use a `.env` file:

1. Copy the template:

   .. code-block:: bash

       cp .env.example .env

2. Edit `.env` with your settings:

   .. code-block:: bash

       WLED_HOST=wled.local
       LED_COUNT=60
       MQTT_BROKER=localhost

3. Load configuration in your code:

   .. code-block:: python

       from ble2wled.config import Config
       config = Config('.env')

Using Environment Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Set environment variables directly:

.. code-block:: bash

    export WLED_HOST=192.168.1.100
    export LED_COUNT=60
    export MQTT_BROKER=localhost

Then access them:

.. code-block:: python

    from ble2wled.config import Config
    config = Config()  # Reads from environment

Configuration Reference
------------------------

WLED Device Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~

``WLED_HOST`` (string, required)
  IP address or hostname of WLED device
  
  Example: ``192.168.1.100`` or ``wled.local``

``LED_COUNT`` (integer, default: 60)
  Total number of LEDs in the strip
  
  Valid range: 1-1024

  Example: ``120``

``WLED_HTTP_TIMEOUT`` (float, default: 1.0)
  HTTP request timeout in seconds (for HTTP mode)
  
  Valid range: 0.1-10.0

  Example: ``2.0``

``WLED_HTTP_RETRIES`` (integer, default: 3)
  Number of HTTP retry attempts on timeout (for HTTP mode)
  
  Valid range: 0-10

  Example: ``5``

``WLED_UDP_PORT`` (integer, default: 21324)
  UDP port for DRGB protocol (for UDP mode)
  
  Standard WLED UDP port is 21324

MQTT Broker Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~

``MQTT_BROKER`` (string, required if using MQTT)
  MQTT broker hostname or IP address
  
  Example: ``192.168.1.100`` or ``mqtt.example.com``

``MQTT_PORT`` (integer, default: 1883)
  MQTT broker port
  
  Standard MQTT port is 1883
  
  Example: ``1883``

``MQTT_LOCATION`` (string, required if using MQTT)
  Location/room identifier for beacon subscription
  
  Subscribes to topic: ``espresense/devices/{MQTT_LOCATION}``
  
  Example: ``living_room`` or ``office``

``MQTT_USERNAME`` (string, optional)
  Username for MQTT authentication
  
  Leave empty or unset if broker doesn't require authentication
  
  Example: ``mqtt_user``

``MQTT_PASSWORD`` (string, optional)
  Password for MQTT authentication
  
  Leave empty or unset if broker doesn't require authentication
  
  Example: ``secure_password_123``

Animation Configuration
~~~~~~~~~~~~~~~~~~~~~~~

``ANIMATION_UPDATE_INTERVAL`` (float, default: 0.05)
  Time between animation updates in seconds
  
  Lower values = smoother animation but higher CPU usage
  
  Valid range: 0.01-1.0
  
  Examples:
  - 0.02 (50fps animation)
  - 0.05 (20fps)
  - 0.1 (10fps)

``ANIMATION_TRAIL_LENGTH`` (integer, default: 8)
  Number of LEDs in motion trail
  
  Valid range: 1-100
  
  Example: ``15``

``ANIMATION_FADE_FACTOR`` (float, default: 0.7)
  Trail fade factor (brightness multiplier per segment)
  
  Valid range: 0.1-1.0
  
  - 0.9 = slow fade (bright trails)
  - 0.5 = medium fade
  - 0.1 = fast fade (dim trails)

Beacon Configuration
~~~~~~~~~~~~~~~~~~~~

``BEACON_TIMEOUT_SECONDS`` (float, default: 6.0)
  How long before a beacon is considered gone
  
  Valid range: 1.0-60.0
  
  Example: ``10.0``

``BEACON_FADE_OUT_SECONDS`` (float, default: 4.0)
  How long to fade out after timeout
  
  Valid range: 0.5-30.0
  
  Example: ``2.0``

Complete Configuration Example
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here's a complete `.env` file with all options:

.. code-block:: bash

    # WLED Device
    WLED_HOST=192.168.1.100
    LED_COUNT=60
    WLED_HTTP_TIMEOUT=1.0
    WLED_HTTP_RETRIES=3
    WLED_UDP_PORT=21324

    # MQTT Broker
    MQTT_BROKER=192.168.1.50
    MQTT_PORT=1883
    MQTT_LOCATION=living_room
    MQTT_USERNAME=mqtt_user
    MQTT_PASSWORD=secure_password

    # Animation
    ANIMATION_UPDATE_INTERVAL=0.05
    ANIMATION_TRAIL_LENGTH=10
    ANIMATION_FADE_FACTOR=0.75

    # Beacon Detection
    BEACON_TIMEOUT_SECONDS=6.0
    BEACON_FADE_OUT_SECONDS=4.0

Validation
----------

Validate your configuration programmatically:

.. code-block:: python

    from ble2wled.config import Config

    config = Config('.env')
    try:
        config.validate()
        print("Configuration is valid!")
    except ValueError as e:
        print(f"Configuration error: {e}")

Export Configuration
~~~~~~~~~~~~~~~~~~~~

Export configuration as JSON for debugging:

.. code-block:: python

    import json
    from ble2wled.config import Config

    config = Config('.env')
    print(json.dumps(config.to_dict(), indent=2))

Output:

.. code-block:: json

    {
      "wled_host": "192.168.1.100",
      "led_count": 60,
      "mqtt_broker": "192.168.1.50",
      "mqtt_port": 1883,
      "mqtt_location": "living_room",
      "mqtt_username": "mqtt_user",
      "animation_update_interval": 0.05,
      "animation_trail_length": 10,
      "animation_fade_factor": 0.75,
      "beacon_timeout_seconds": 6.0,
      "beacon_fade_out_seconds": 4.0
    }

Default Values
~~~~~~~~~~~~~~

If a configuration value is not specified, defaults are used:

.. code-block:: python

    from ble2wled.config import Config

    config = Config()
    
    # These have defaults
    print(config.mqtt_port)              # 1883
    print(config.led_count)              # 60
    print(config.animation_update_interval)  # 0.05

Type Conversion
~~~~~~~~~~~~~~~

Configuration automatically converts types:

.. code-block:: python

    # These all work:
    config.led_count = 60              # int
    config.led_count = "60"            # str -> converted to int
    config.animation_fade_factor = 0.75      # float
    config.animation_fade_factor = "0.75"    # str -> converted to float

Optional Values
~~~~~~~~~~~~~~~

Some configuration values are optional (MQTT credentials):

.. code-block:: python

    config.mqtt_username      # None if not set
    config.mqtt_password      # None if not set

    # These are always required (no default)
    config.wled_host          # Required
    config.mqtt_broker        # Required if using MQTT
    config.mqtt_location      # Required if using MQTT

Troubleshooting Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**.env file not being read:**

Ensure the file exists and contains proper syntax:

.. code-block:: bash

    # Good syntax
    KEY=value
    KEY=value with spaces
    KEY="quoted value"

    # Bad syntax
    KEY = value         # Extra spaces
    KEY:value          # Wrong separator
    value              # Missing key

**Type conversion errors:**

Ensure values can be converted to expected types:

.. code-block:: python

    LED_COUNT=60        # OK (can convert to int)
    LED_COUNT=abc       # ERROR (cannot convert to int)
    ANIMATION_FADE_FACTOR=0.75   # OK (can convert to float)

**Missing required values:**

Call ``validate()`` to check for missing required values:

.. code-block:: python

    config.validate()  # Raises ValueError if required values missing

Next Steps
----------

- :doc:`../guides/cli_simulator` - Use simulator with configuration
- :doc:`../guides/mqtt_authentication` - MQTT authentication setup
- :doc:`../api/config` - Complete Config API reference
