:mod:`ble2wled.wled` - WLED Device Communication
=================================================

.. automodule:: ble2wled.wled
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The ``wled`` module provides controllers for communicating with WLED devices via HTTP and UDP protocols. It handles:

- HTTP requests with automatic retry logic
- UDP DRGB protocol for fast updates
- Graceful error handling and recovery

Quick Example
~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.wled import WLEDUDPController, WLEDHTTPController

    # UDP is faster and doesn't require connection setup
    controller = WLEDUDPController(
        host='192.168.1.100',
        led_count=60
    )

    # HTTP is slower but more reliable for some networks
    controller = WLEDHTTPController(
        host='192.168.1.100',
        led_count=60,
        timeout=1.0,
        max_retries=3
    )

    # Send LED data
    leds = [[255, 0, 0]] * 60  # All red
    controller.update(leds)

Classes
-------

WLEDUDPController
~~~~~~~~~~~~~~~~~

Fast UDP-based communication using DRGB protocol.

**Attributes:**

- ``host`` (str) - WLED device hostname or IP
- ``led_count`` (int) - Number of LEDs in strip
- ``port`` (int, default 21324) - UDP port

**Methods:**

- ``update(leds: List[List[int]])`` - Send LED data to device

**Advantages:**

- Faster (no connection overhead)
- Fire-and-forget (no waiting for response)
- Works with most WLED devices

**Disadvantages:**

- No error handling (packets can be lost)
- No acknowledgment

**Example:**

.. code-block:: python

    from ble2wled.wled import WLEDUDPController

    controller = WLEDUDPController('192.168.1.100', 60)

    # Send all red
    leds = [[255, 0, 0] for _ in range(60)]
    controller.update(leds)

    # Send gradient
    leds = [[i * 4, 0, 255 - i * 4] for i in range(60)]
    controller.update(leds)

WLEDHTTPController
~~~~~~~~~~~~~~~~~~

Reliable HTTP-based communication with automatic retry logic.

**Attributes:**

- ``host`` (str) - WLED device hostname or IP
- ``led_count`` (int) - Number of LEDs in strip
- ``timeout`` (float, default 1.0) - HTTP request timeout in seconds
- ``max_retries`` (int, default 3) - Number of retry attempts on timeout
- ``port`` (int, default 80) - HTTP port

**Methods:**

- ``update(leds: List[List[int]])`` - Send LED data to device

**Advantages:**

- HTTP retries on timeout (automatic recovery)
- Error handling and logging
- Works with unreliable networks

**Disadvantages:**

- Slower (HTTP overhead)
- Connection setup time

**Example:**

.. code-block:: python

    from ble2wled.wled import WLEDHTTPController

    # Standard configuration
    controller = WLEDHTTPController(
        host='192.168.1.100',
        led_count=60,
        timeout=1.0,
        max_retries=3
    )

    # For unreliable networks
    controller = WLEDHTTPController(
        host='192.168.1.100',
        led_count=60,
        timeout=2.0,        # Longer timeout
        max_retries=5       # More retries
    )

    # For fast networks
    controller = WLEDHTTPController(
        host='192.168.1.100',
        led_count=60,
        timeout=0.5,        # Shorter timeout
        max_retries=1       # Fewer retries
    )

    # Send update
    leds = [[255, 0, 0]] * 60
    controller.update(leds)

LED Data Format
---------------

Both controllers accept LED data as a list of RGB tuples:

.. code-block:: python

    # List of [R, G, B] values for each LED
    # Each value is 0-255

    leds = [
        [255, 0, 0],      # LED 0: Red
        [0, 255, 0],      # LED 1: Green
        [0, 0, 255],      # LED 2: Blue
        [255, 255, 255],  # LED 3: White
        # ... 56 more LEDs for 60-LED strip
    ]

    controller.update(leds)

**Requirements:**

- List length must equal ``led_count``
- Each element must be a list/tuple of [R, G, B]
- Each value must be 0-255

Examples
--------

Basic LED Updates
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.wled import WLEDUDPController

    controller = WLEDUDPController('192.168.1.100', 60)

    # All red
    leds = [[255, 0, 0]] * 60
    controller.update(leds)

    # Rainbow gradient
    leds = [
        [int(255 * (i / 60)), int(255 * (1 - i / 60)), 0]
        for i in range(60)
    ]
    controller.update(leds)

    # Off
    leds = [[0, 0, 0]] * 60
    controller.update(leds)

With Animation Loop
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.wled import WLEDUDPController
    import time

    controller = WLEDUDPController('192.168.1.100', 60)

    # Simple animation: moving red dot
    for iteration in range(100):
        position = iteration % 60
        leds = [[0, 0, 0]] * 60
        leds[position] = [255, 0, 0]
        controller.update(leds)
        time.sleep(0.05)  # 20fps

HTTP with Retry Handling
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from ble2wled.wled import WLEDHTTPController
    import logging

    # Enable logging to see retries
    logging.basicConfig(level=logging.INFO)

    controller = WLEDHTTPController(
        host='192.168.1.100',
        led_count=60,
        max_retries=3
    )

    # Try to update
    leds = [[255, 0, 0]] * 60
    controller.update(leds)

    # If device times out, will automatically retry
    # Logs will show retry attempts

Choosing Between UDP and HTTP
------------------------------

**Use UDP when:**

- WLED device is on stable local network
- Speed is critical
- You want fire-and-forget behavior

.. code-block:: python

    from ble2wled.wled import WLEDUDPController
    controller = WLEDUDPController('wled.local', 60)

**Use HTTP when:**

- Network is unreliable or WiFi
- You need automatic recovery from timeouts
- Device is temporarily unreachable

.. code-block:: python

    from ble2wled.wled import WLEDHTTPController
    controller = WLEDHTTPController('wled.local', 60)

**Use HTTP with more retries on bad networks:**

.. code-block:: python

    from ble2wled.wled import WLEDHTTPController
    controller = WLEDHTTPController(
        'wled.local',
        60,
        timeout=2.0,
        max_retries=5
    )

Error Handling
--------------

HTTP Errors
~~~~~~~~~~~

Handled automatically with retry logic:

.. code-block:: python

    from ble2wled.wled import WLEDHTTPController

    controller = WLEDHTTPController('192.168.1.100', 60)

    # These errors are retried automatically:
    # - ReadTimeout
    # - Timeout
    # - ConnectionError

    # Logs will show retry attempts:
    # "HTTP timeout on attempt 1/3 for 192.168.1.100, retrying..."
    # If all retries fail: "HTTP request failed after 3 attempts for 192.168.1.100..."

    leds = [[255, 0, 0]] * 60
    controller.update(leds)  # May log timeout messages but continues

UDP Errors
~~~~~~~~~~

UDP doesn't wait for responses, so no timeouts. Packets may be lost:

.. code-block:: python

    from ble2wled.wled import WLEDUDPController

    controller = WLEDUDPController('192.168.1.100', 60)

    # UDP doesn't throw exceptions for lost packets
    # If device unreachable, packets are silently dropped
    leds = [[255, 0, 0]] * 60
    controller.update(leds)

Debugging
---------

Check Device Connectivity
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Test HTTP connection
    curl http://192.168.1.100/json/state

    # Test UDP with netcat (Linux/Mac)
    echo "test" | nc -u 192.168.1.100 21324

See WLED Logs
~~~~~~~~~~~~~

Access WLED web interface at ``http://192.168.1.100`` and check logs.

Performance Tips
~~~~~~~~~~~~~~~~

- UDP is ~10x faster than HTTP
- HTTP adds network overhead but handles errors
- Update interval of 0.05s (20fps) is good balance
- Longer trails require more color calculations

See Also
--------

- :doc:`animation` - Animation loop using controllers
- :doc:`../guides/http_retry_logic` - HTTP retry documentation
- :doc:`../guides/configuration` - Configure WLED parameters
