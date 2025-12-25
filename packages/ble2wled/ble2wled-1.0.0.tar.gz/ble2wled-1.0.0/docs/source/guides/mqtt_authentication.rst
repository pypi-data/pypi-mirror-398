MQTT Authentication
===================

BLE2WLED supports username and password authentication for MQTT brokers that require credentials.

Overview
--------

The MQTT authentication system allows you to:

- Connect to secured MQTT brokers with credentials
- Optional authentication (works with or without credentials)
- Secure password management via environment variables
- Support for both CLI and Python API

Configuration
-------------

Using .env File
~~~~~~~~~~~~~~~

Add the following to your `.env` file:

.. code-block:: bash

    # MQTT Broker Settings
    MQTT_BROKER=192.168.1.100
    MQTT_PORT=1883
    MQTT_LOCATION=living_room

    # MQTT Authentication (Optional)
    MQTT_USERNAME=mqtt_user
    MQTT_PASSWORD=mqtt_secure_password

Using Environment Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Set environment variables directly:

.. code-block:: bash

    export MQTT_BROKER=192.168.1.100
    export MQTT_PORT=1883
    export MQTT_LOCATION=living_room
    export MQTT_USERNAME=mqtt_user
    export MQTT_PASSWORD=mqtt_secure_password

Optional Authentication
~~~~~~~~~~~~~~~~~~~~~~~

**MQTT authentication is completely optional.** If ``MQTT_USERNAME`` and ``MQTT_PASSWORD`` are not set, the system attempts to connect without authentication.


CLI Usage
---------

Without Authentication
~~~~~~~~~~~~~~~~~~~~~~

For MQTT brokers that don't require credentials:

.. code-block:: bash

    python -m ble2wled.cli_simulator --mqtt \
      --mqtt-broker 192.168.1.100 \
      --mqtt-location living_room \
      --led-count 60

With Authentication
~~~~~~~~~~~~~~~~~~~

For secured MQTT brokers:

.. code-block:: bash

    python -m ble2wled.cli_simulator --mqtt \
      --mqtt-broker 192.168.1.100 \
      --mqtt-port 1883 \
      --mqtt-location living_room \
      --mqtt-username mqtt_user \
      --mqtt-password mqtt_secure_pass \
      --led-count 60

Using .env Configuration
~~~~~~~~~~~~~~~~~~~~~~~~

Load credentials from `.env` file automatically:

.. code-block:: bash

    python -m ble2wled.cli_simulator --mqtt \
      --mqtt-broker 192.168.1.100 \
      --mqtt-location living_room \
      --led-count 60

The CLI automatically uses ``MQTT_USERNAME`` and ``MQTT_PASSWORD`` from `.env` if present.

Python API
----------

Using Config Class
~~~~~~~~~~~~~~~~~~~

Load credentials from configuration:

.. code-block:: python

    from ble2wled.config import Config
    from ble2wled.mqtt import EspresenseBeaconListener
    from ble2wled.states import BeaconState

    # Load configuration from .env
    config = Config('.env')

    # Initialize beacon state
    state = BeaconState()

    # Create listener with credentials from config
    listener = EspresenseBeaconListener(
        state,
        broker=config.mqtt_broker,
        port=config.mqtt_port,
        location=config.mqtt_location,
        username=config.mqtt_username,      # Optional
        password=config.mqtt_password       # Optional
    )

    # Start listening for beacon data
    listener.start()

Direct Constructor Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pass credentials directly to the listener:

.. code-block:: python

    from ble2wled.mqtt import EspresenseBeaconListener
    from ble2wled.states import BeaconState

    state = BeaconState()

    # With authentication
    listener = EspresenseBeaconListener(
        state,
        broker="192.168.1.100",
        port=1883,
        location="living_room",
        username="mqtt_user",
        password="secure_password"
    )
    listener.start()

    # Without authentication (credentials optional)
    listener = EspresenseBeaconListener(
        state,
        broker="192.168.1.100",
        port=1883,
        location="living_room"
    )
    listener.start()

Complete Example
~~~~~~~~~~~~~~~~

Production setup with authentication:

.. code-block:: python

    from ble2wled.config import Config
    from ble2wled.states import BeaconState
    from ble2wled.mqtt import EspresenseBeaconListener
    from ble2wled.wled import WLEDUDPController
    from ble2wled.animation import run_wled_beacons

    # Load configuration from .env
    config = Config('.env')
    config.validate()

    # Create beacon state
    beacon_state = BeaconState(
        timeout_seconds=6.0,
        fade_out_seconds=4.0
    )

    # Create MQTT listener with authentication
    mqtt_listener = EspresenseBeaconListener(
        beacon_state,
        broker=config.mqtt_broker,
        port=config.mqtt_port,
        location=config.mqtt_location,
        username=config.mqtt_username,      # From MQTT_USERNAME env var
        password=config.mqtt_password       # From MQTT_PASSWORD env var
    )
    mqtt_listener.start()

    # Create WLED controller
    controller = WLEDUDPController(
        host=config.wled_host,
        led_count=config.led_count
    )

    # Run animation loop
    try:
        run_wled_beacons(
            controller,
            led_count=config.led_count,
            beacon_state=beacon_state,
            update_interval=0.05,
            trail_length=10,
            fade_factor=0.75
        )
    finally:
        mqtt_listener.stop()

Security Best Practices
-----------------------

Password Management
~~~~~~~~~~~~~~~~~~~

1. **Use .env files** - Never hardcode passwords in source code

   .. code-block:: bash

       # Good: credentials in .env
       MQTT_PASSWORD=secure_password

       # Bad: hardcoded in code
       password = "secure_password"

2. **Protect .env files** - Add to `.gitignore`

   .. code-block:: bash

       # .gitignore
       .env
       .env.local

3. **Use strong passwords** - Follow broker security recommendations

   Good password:
   - At least 12 characters
   - Mix of upper/lowercase, numbers, symbols
   - No dictionary words or patterns

4. **Rotate credentials regularly** - Change MQTT credentials periodically

5. **Limit broker access** - Configure firewall rules on MQTT broker:

   .. code-block:: bash

       # Only allow connections from trusted IP ranges
       ufw allow from 192.168.1.0/24 to any port 1883

Environment Variable Management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For CI/CD or Docker deployments:

.. code-block:: bash

    # Set via environment
    docker run -e MQTT_USERNAME=user -e MQTT_PASSWORD=pass image

    # Or use secrets file
    docker secret create mqtt_password /path/to/password
    docker service create --secret mqtt_password image

Testing
-------

Test MQTT Connection
~~~~~~~~~~~~~~~~~~~~

Verify your MQTT credentials work:

.. code-block:: bash

    # Test with mosquitto client
    mosquitto_sub -h 192.168.1.100 -u mqtt_user -P mqtt_password \
      -t "espresense/devices/living_room/+"

    # Should receive beacon messages
    espresense/devices/living_room/device_id {"rssi": -45, ...}

Test CLI Simulator
~~~~~~~~~~~~~~~~~~

Test the simulator with authentication:

.. code-block:: bash

    python -m ble2wled.cli_simulator --mqtt \
      --mqtt-broker 192.168.1.100 \
      --mqtt-username mqtt_user \
      --mqtt-password mqtt_password \
      --mqtt-location living_room

You should see animated beacons and MQTT statistics.

Test Python API
~~~~~~~~~~~~~~~

Test the listener directly:

.. code-block:: python

    from ble2wled.mqtt import EspresenseBeaconListener
    from ble2wled.states import BeaconState

    state = BeaconState()
    listener = EspresenseBeaconListener(
        state,
        broker="192.168.1.100",
        username="mqtt_user",
        password="mqtt_password",
        location="test"
    )

    try:
        listener.start()
        print("Connected successfully!")
        print(f"Active beacons: {len(state.beacons)}")
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        listener.stop()

Troubleshooting
~~~~~~~~~~~~~~~

**Connection refused with credentials**

1. Verify username/password are correct:

   .. code-block:: bash

       mosquitto_sub -h broker -u username -P password -t "test"

2. Check MQTT broker logs for authentication errors

3. Ensure broker has user configured:

   .. code-block:: bash

       # Mosquitto: check password file
       sudo cat /etc/mosquitto/passwd

**Authentication failed error**

1. Verify credentials are properly set:

   .. code-block:: python

       from ble2wled.config import Config
       config = Config('.env')
       print(f"Username: {config.mqtt_username}")
       print(f"Password: {'*' * len(config.mqtt_password)}")

2. Check .env file format (no extra spaces):

   .. code-block:: bash

       # Good
       MQTT_USERNAME=user
       MQTT_PASSWORD=password

       # Bad
       MQTT_USERNAME = user
       MQTT_PASSWORD = password

3. Check for special characters that need escaping:

   .. code-block:: bash

       # If password contains special chars, quote it
       MQTT_PASSWORD="p@ss:word!"

**Connection works without credentials but fails with them**

1. Broker might not have authentication enabled
2. Check broker configuration
3. Verify user account exists in broker

Configuration Examples
~~~~~~~~~~~~~~~~~~~~~~

**Mosquitto with authentication:**

.. code-block:: bash

    # Create password file
    sudo mosquitto_passwd -c /etc/mosquitto/passwd mqtt_user

    # Configure mosquitto.conf
    allow_anonymous false
    password_file /etc/mosquitto/passwd
    listener 1883

**Home Assistant MQTT:**

.. code-block:: bash

    MQTT_BROKER=192.168.1.50
    MQTT_USERNAME=homeassistant
    MQTT_PASSWORD=<your-ha-password>
    MQTT_LOCATION=living_room

**HiveMQ Cloud:**

.. code-block:: bash

    MQTT_BROKER=<your-cluster>.s2.eu.hivemq.cloud
    MQTT_PORT=8883
    MQTT_USERNAME=<hivemq-username>
    MQTT_PASSWORD=<hivemq-password>
    MQTT_LOCATION=test

Next Steps
----------

- :doc:`configuration` - Full configuration reference
- :doc:`cli_simulator` - CLI simulator usage
- :doc:`../api/mqtt` - MQTT module API reference
