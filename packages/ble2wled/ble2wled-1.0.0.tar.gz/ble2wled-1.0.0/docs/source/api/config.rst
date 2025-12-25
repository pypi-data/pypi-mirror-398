:mod:`ble2wled.config` - Configuration Management
==================================================

.. automodule:: ble2wled.config
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The ``config`` module provides centralized configuration management for BLE2WLED using environment variables and .env files.

Configuration is loaded from:

1. .env file (if present)
2. Environment variables
3. Default values

Quick Example
~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.config import Config

    # Load configuration from .env
    config = Config('.env')

    # Validate all required values are present
    config.validate()

    # Access configuration properties
    print(f"WLED: {config.wled_host}:{config.led_count}")
    print(f"MQTT: {config.mqtt_broker}:{config.mqtt_port}")

    # Export as dictionary for logging
    import json
    print(json.dumps(config.to_dict(), indent=2))

Properties
----------

**WLED Device**

- ``wled_host`` (str, required) - WLED device hostname/IP
- ``led_count`` (int, default 60) - Number of LEDs in strip
- ``wled_http_timeout`` (float, default 1.0) - HTTP request timeout
- ``wled_http_retries`` (int, default 3) - HTTP retry attempts
- ``wled_udp_port`` (int, default 21324) - UDP DRGB port

**MQTT Broker**

- ``mqtt_broker`` (str, required if using MQTT) - MQTT broker hostname/IP
- ``mqtt_port`` (int, default 1883) - MQTT port
- ``mqtt_location`` (str, required if using MQTT) - Location/room identifier
- ``mqtt_username`` (str, optional) - MQTT authentication username
- ``mqtt_password`` (str, optional) - MQTT authentication password

**Animation**

- ``animation_update_interval`` (float, default 0.05) - Animation update interval
- ``animation_trail_length`` (int, default 8) - Motion trail length
- ``animation_fade_factor`` (float, default 0.7) - Trail fade factor

**Beacon Detection**

- ``beacon_timeout_seconds`` (float, default 6.0) - Beacon timeout
- ``beacon_fade_out_seconds`` (float, default 4.0) - Fade out duration

Methods
-------

``__init__(env_file: Optional[str] = None)``
  Initialize configuration, optionally loading from .env file.

``validate() -> None``
  Validate that all required configuration values are present.

``to_dict() -> Dict[str, Any]``
  Export configuration as dictionary (useful for logging/debugging).

Examples
--------

Load from .env File
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    config = Config('.env')
    print(f"LED count: {config.led_count}")

Load from Environment Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    export WLED_HOST=192.168.1.100
    export LED_COUNT=120
    export MQTT_BROKER=localhost

.. code-block:: python

    config = Config()  # Reads from environment
    print(f"LED count: {config.led_count}")  # 120

Validate Configuration
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    config = Config('.env')
    try:
        config.validate()
        print("Configuration valid!")
    except ValueError as e:
        print(f"Invalid config: {e}")

Use with MQTT Authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    config = Config('.env')
    
    from ble2wled.mqtt import EspresenseBeaconListener
    listener = EspresenseBeaconListener(
        beacon_state,
        broker=config.mqtt_broker,
        port=config.mqtt_port,
        location=config.mqtt_location,
        username=config.mqtt_username,      # Optional
        password=config.mqtt_password       # Optional
    )

Export for Logging
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import json
    config = Config('.env')
    
    # Print formatted configuration
    print(json.dumps(config.to_dict(), indent=2))

    # Output:
    # {
    #   "wled_host": "192.168.1.100",
    #   "led_count": 60,
    #   "mqtt_broker": "192.168.1.50",
    #   ...
    # }

See Also
--------

- :doc:`../guides/configuration` - Full configuration guide
- :doc:`../quickstart` - Quick start with configuration
