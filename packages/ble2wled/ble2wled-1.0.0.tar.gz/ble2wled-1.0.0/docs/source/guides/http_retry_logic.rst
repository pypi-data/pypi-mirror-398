HTTP Retry Logic
================

BLE2WLED automatically handles temporary connection failures to WLED devices via HTTP using intelligent retry logic with exponential backoff.

Overview
--------

The HTTP retry mechanism ensures reliable communication with WLED devices by:

- Automatically retrying failed HTTP requests
- Handling transient timeouts and connection errors
- Gracefully degrading when device is unreachable
- Continuing animation even during temporary failures
- Configurable retry behavior

Why Retry Logic?
~~~~~~~~~~~~~~~~

WLED devices over HTTP can experience temporary delays due to:

- Network congestion or WiFi interference
- WLED device busy processing other requests
- Device momentarily unreachable
- Slow network response times

The retry logic recovers from these transient failures without disrupting the animation.

How It Works
------------

Retry Mechanism
~~~~~~~~~~~~~~~

When an HTTP request to a WLED device times out:

1. Controller automatically retries up to 3 times (configurable)
2. Brief 50ms delay between retries allows device to recover
3. On success: LED update is sent and animation continues
4. On failure after all retries: Error is logged, animation continues without update

Handled Errors
~~~~~~~~~~~~~~

The following errors trigger automatic retries:

- ``requests.exceptions.ReadTimeout`` - Server didn't send response in time
- ``requests.exceptions.Timeout`` - Generic timeout error
- ``requests.exceptions.ConnectionError`` - Connection to device failed

Other errors don't trigger retries:
- DNS resolution errors
- SSL/TLS errors  
- Invalid JSON responses
- 4xx/5xx HTTP errors

These are logged as errors but don't retry (retry wouldn't help).

Retry Behavior
~~~~~~~~~~~~~~

**Success on first attempt:**

::

    LED update → Success → Continue animation

**Timeout on first attempt, success on retry:**

::

    LED update (attempt 1) → Timeout → Sleep 50ms
    LED update (attempt 2) → Success → Continue animation

**Multiple timeouts with recovery:**

::

    LED update (attempt 1) → Timeout → Sleep 50ms
    LED update (attempt 2) → Timeout → Sleep 50ms
    LED update (attempt 3) → Success → Continue animation

**All retries exhausted:**

::

    LED update (attempt 1) → Timeout → Sleep 50ms
    LED update (attempt 2) → Timeout → Sleep 50ms
    LED update (attempt 3) → Timeout → Log error → Continue animation

Animation continues with last known LED state.

Usage
-----

Default Configuration (3 retries)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

With default settings, HTTP controller retries 3 times on timeout:

.. code-block:: python

    from ble2wled.wled import WLEDHTTPController

    controller = WLEDHTTPController(
        host='192.168.1.100',
        led_count=60
    )
    # Automatically retries 3 times on timeout
    controller.update(leds)

Custom Retry Count
~~~~~~~~~~~~~~~~~~~

Configure the number of retry attempts:

.. code-block:: python

    # Retry up to 5 times (for unreliable networks)
    controller = WLEDHTTPController(
        host='192.168.1.100',
        led_count=60,
        max_retries=5
    )

    # Single attempt, no retries (fast fail)
    controller = WLEDHTTPController(
        host='192.168.1.100',
        led_count=60,
        max_retries=1
    )

Custom Timeout
~~~~~~~~~~~~~~

Configure HTTP request timeout:

.. code-block:: python

    # 2 second timeout per request
    controller = WLEDHTTPController(
        host='192.168.1.100',
        led_count=60,
        timeout=2.0,
        max_retries=3
    )

    # Short timeout for responsive devices
    controller = WLEDHTTPController(
        host='192.168.1.100',
        led_count=60,
        timeout=0.5,
        max_retries=2
    )

Configuration
~~~~~~~~~~~~~

Configure via .env file:

.. code-block:: bash

    WLED_HOST=192.168.1.100
    LED_COUNT=60
    WLED_HTTP_TIMEOUT=1.0
    WLED_HTTP_RETRIES=3

Then use in code:

.. code-block:: python

    from ble2wled.config import Config
    from ble2wled.wled import WLEDHTTPController

    config = Config('.env')
    controller = WLEDHTTPController(
        host=config.wled_host,
        led_count=config.led_count,
        timeout=config.wled_http_timeout,
        max_retries=config.wled_http_retries
    )

Logging Output
--------------

Retry Attempt (WARNING Level)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a timeout occurs and retry is attempted:

.. code-block:: text

    HTTP timeout on attempt 1/3 for 192.168.1.100, retrying...
    HTTP timeout on attempt 2/3 for 192.168.1.100, retrying...

Final Failure (ERROR Level)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When all retries are exhausted:

.. code-block:: text

    HTTP request failed after 3 attempts for 192.168.1.100: Read timed out. (read timeout=1)

Other Errors (ERROR Level)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

For errors that don't retry:

.. code-block:: text

    HTTP request error for 192.168.1.100: [Errno -2] Name or service not known

Collecting Logs
~~~~~~~~~~~~~~~

Enable logging to see retry messages:

.. code-block:: python

    import logging

    # Configure logging to show INFO and above
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Now you'll see retry messages
    controller = WLEDHTTPController(...)
    controller.update(leds)

Performance Impact
------------------

Overhead Analysis
~~~~~~~~~~~~~~~~~

- **50ms retry delay** - Sleep between attempts
- **Typical timeout** - 1-2 seconds before retry
- **Total overhead per failed update** - ~150ms (3 retries × 50ms)

This overhead is acceptable because:
- Animation updates run every 50-100ms anyway
- Missing one update is imperceptible to human eye
- Fast recovery is more important than speed of single update

Overall Impact
~~~~~~~~~~~~~~

In typical scenarios:

- No impact on normal operation (no retries)
- <150ms delay for one failed update (recovered on retry)
- Complete failure still allows animation to continue

Example: With 60 LED updates per second (16.7ms each):
- Timeout and recovery takes ~200ms (12 frames)
- User sees smooth animation, brief pause during timeout recovery
- Much better than animation crash

Typical Scenarios
-----------------

Scenario 1: Momentary Network Congestion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**What happens:**

- WiFi temporarily congested, single packet loss
- Attempt 1: Timeout (device busy)
- Attempt 2: Success (device responds)
- Result: Slight animation pause, then continues smoothly

**Logs:**

.. code-block:: text

    HTTP timeout on attempt 1/3 for 192.168.1.100, retrying...
    [LED update succeeds on retry 2]

**User experience:** Smooth animation, imperceptible brief pause

Scenario 2: Device Temporarily Busy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**What happens:**

- WLED device processing multiple requests
- Attempt 1: Timeout (queue full)
- Attempt 2: Timeout (still busy)
- Attempt 3: Success (queue cleared)
- Result: Animation continues after brief delay

**Logs:**

.. code-block:: text

    HTTP timeout on attempt 1/3 for 192.168.1.100, retrying...
    HTTP timeout on attempt 2/3 for 192.168.1.100, retrying...
    [LED update succeeds on retry 3]

**User experience:** Smooth animation with minor frame drops

Scenario 3: Device Unreachable
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**What happens:**

- WLED device powered off or network disconnected
- All 3 attempts timeout
- Animation continues with last known LED state
- User sees frozen LED pattern
- When device comes back online, animation resumes

**Logs:**

.. code-block:: text

    HTTP timeout on attempt 1/3 for 192.168.1.100, retrying...
    HTTP timeout on attempt 2/3 for 192.168.1.100, retrying...
    HTTP request failed after 3 attempts for 192.168.1.100: Read timed out.

**User experience:** LEDs freeze, then resume when device comes back

Scenario 4: Poor WiFi Signal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**What happens:**

- WiFi signal weak (edge of range)
- Some updates succeed, others timeout and retry
- Animation continues but with more frame drops
- Works, but not smooth

**Logs:**

.. code-block:: text

    HTTP timeout on attempt 1/3 for 192.168.1.100, retrying...
    [Succeeds on retry]
    [Normal update]
    HTTP timeout on attempt 1/3 for 192.168.1.100, retrying...
    [Succeeds on retry]
    ...

**User experience:** Animation continues but somewhat choppy
**Solution:** Move WiFi router closer or increase max_retries

Optimization Tips
-----------------

For Fast Networks
~~~~~~~~~~~~~~~~~

If your WLED device is on a fast local network:

.. code-block:: python

    controller = WLEDHTTPController(
        host='192.168.1.100',
        led_count=60,
        timeout=0.5,      # Shorter timeout
        max_retries=2     # Fewer retries
    )

For Slow/Unstable Networks
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If your network is slow or unstable:

.. code-block:: python

    controller = WLEDHTTPController(
        host='192.168.1.100',
        led_count=60,
        timeout=2.0,       # Longer timeout
        max_retries=5      # More retries
    )

For Critical Applications
~~~~~~~~~~~~~~~~~~~~~~~~~~

If animation must not freeze:

.. code-block:: python

    controller = WLEDHTTPController(
        host='192.168.1.100',
        led_count=60,
        timeout=0.5,       # Fast timeout
        max_retries=1      # Single attempt
    )
    # Animation continues even if device unreachable
    # Might miss some updates but never stalls

UDP Alternative
~~~~~~~~~~~~~~~

For most reliable real-time updates, consider UDP:

.. code-block:: python

    from ble2wled.wled import WLEDUDPController

    # UDP is faster and doesn't require connection
    controller = WLEDUDPController(
        host='192.168.1.100',
        led_count=60
    )

UDP doesn't have timeouts - packets are sent and forgotten.

Troubleshooting
~~~~~~~~~~~~~~~

**Frequent timeout warnings in logs**

1. Check network connectivity: ``ping 192.168.1.100``
2. Verify WLED is responding: ``curl http://192.168.1.100/json/state``
3. Try increasing timeout: ``timeout=2.0``
4. Try more retries: ``max_retries=5``

**Device always timing out**

1. Ensure device is powered on and connected
2. Check IP address is correct
3. Try accessing WLED web interface: ``http://192.168.1.100``
4. Check WLED logs for errors
5. Try UDP mode instead

**Animation stutters despite retries**

1. Network might be overloaded
2. Try increasing update_interval: ``update_interval=0.1`` (slower)
3. Try reducing trail_length or fade effects
4. Consider moving WiFi router closer
5. Check for interference on WiFi channel

**High CPU usage during retries**

This shouldn't happen (retries include 50ms sleep).
If you see high CPU:

1. Check if animation thread is spinning
2. Reduce update_interval
3. Verify timeout isn't set too low

Next Steps
----------

- :doc:`configuration` - Configure HTTP parameters
- :doc:`cli_simulator` - Test with simulator
- :doc:`../api/wled` - WLEDHTTPController API reference
