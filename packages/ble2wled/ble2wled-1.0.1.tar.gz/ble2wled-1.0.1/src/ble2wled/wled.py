"""WLED LED controller implementations.

This module provides abstract and concrete LED controller classes for
communicating with WLED devices via HTTP and UDP protocols.

Protocols:
    - HTTP: JSON-based API, slower but more reliable
    - UDP: DRGB protocol, real-time updates with low latency

Example:
    Create and use an LED controller::

        from ble2wled.wled import WLEDUDPController

        controller = WLEDUDPController('wled.local', led_count=60, port=21324)
        leds = [[255, 0, 0] for _ in range(60)]  # All red
        controller.update(leds)
"""

import logging
import socket
import time
from abc import ABC, abstractmethod

import requests

logger = logging.getLogger(__name__)


class LEDController(ABC):
    """Abstract base class for LED controllers.

    Defines the interface that all LED controller implementations must follow.

    Attributes:
        host (str): WLED device hostname or IP address.
        led_count (int): Total number of LEDs in the strip.
    """

    def __init__(self, host: str, led_count: int):
        """Initialize LED controller.

        Args:
            host (str): WLED device hostname or IP address.
            led_count (int): Total number of LEDs in the strip.

        Example:
            Subclass initialization::

                class MyController(LEDController):
                    def __init__(self, host, led_count):
                        super().__init__(host, led_count)
        """
        self.host = host
        self.led_count = led_count

    @abstractmethod
    def update(self, leds: list[list[int]]) -> None:
        """Send LED color update to device.

        Args:
            leds (list): List of RGB color values [R, G, B] 0-255.
        """


class WLEDHTTPController(LEDController):
    """WLED controller using HTTP API.

    Sends LED updates via WLED's JSON HTTP API. Slower than UDP but more
    reliable and easier to debug.

    Implements automatic retry logic for handling temporary connection failures
    and timeouts.

    Example:
        Use HTTP controller::

            controller = WLEDHTTPController('192.168.1.100', led_count=60)
            leds = [[255, 100, 50] for _ in range(60)]
            controller.update(leds)
    """

    def __init__(self, host: str, led_count: int, max_retries: int = 3):
        """Initialize HTTP controller.

        Args:
            host (str): WLED device hostname or IP address.
            led_count (int): Total number of LEDs in the strip.
            max_retries (int): Maximum number of retry attempts on timeout.
                Default: 3.
        """
        super().__init__(host, led_count)
        self.url = f"http://{host}/json/state"
        self.max_retries = max_retries
        self.timeout = 1

    def update(self, leds: list[list[int]]) -> None:
        """Send LED update via HTTP POST with retry logic.

        Sends LED data to WLED device using the /json/state endpoint.
        Automatically retries on timeout errors to handle temporary
        connection issues.

        Args:
            leds (list): List of RGB color values [R, G, B] 0-255.

        Example:
            Update LEDs via HTTP::

                leds = [[255, 0, 0] for _ in range(60)]  # All red
                controller.update(leds)
        """
        payload = {"on": True, "seg": [{"id": 0, "i": leds}]}

        for attempt in range(self.max_retries):
            try:
                requests.post(self.url, json=payload, timeout=self.timeout)
                return  # Success
            except (
                requests.exceptions.Timeout,
                requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError,
            ) as e:
                if attempt < self.max_retries - 1:
                    logger.warning(
                        "HTTP timeout on attempt %d/%d for %s, retrying...",
                        attempt + 1,
                        self.max_retries,
                        self.host,
                    )
                    # Brief sleep before retry to allow device to recover
                    time.sleep(0.05)
                else:
                    logger.error(
                        "HTTP request failed after %d attempts for %s: %s",
                        self.max_retries,
                        self.host,
                        e,
                    )
                    # Don't raise - allow animation to continue even if device is unreachable
            except requests.exceptions.RequestException as e:
                logger.error("HTTP request error for %s: %s", self.host, e)
                # Don't raise on other request errors - allow animation to continue


class WLEDUDPController(LEDController):
    """WLED controller using UDP DRGB protocol.

    Sends LED updates via UDP using the DRGB protocol for real-time updates
    with minimal latency. Requires WLED to have UDP realtime protocol enabled.

    The DRGB protocol is simple:
        - Header: 'DRGB' (4 bytes)
        - Data: RGB triplets (3 bytes per LED)

    Example:
        Use UDP controller for real-time updates::

            controller = WLEDUDPController('wled.local', led_count=60, port=21324)
            leds = [[0, 255, 0] for _ in range(60)]  # All green
            controller.update(leds)
    """

    def __init__(self, host: str, led_count: int, port: int = 21324):
        """Initialize UDP controller.

        Args:
            host (str): WLED device hostname or IP address.
            led_count (int): Total number of LEDs in the strip.
            port (int): DRGB protocol port. Default: 21324.

        Example:
            Create UDP controller with custom port::

                controller = WLEDUDPController('wled.local', 60, port=21325)
        """
        super().__init__(host, led_count)
        self.addr = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def update(self, leds: list[list[int]]) -> None:
        """Send LED update via UDP DRGB protocol.

        Constructs DRGB packet with header and RGB data, sends via UDP.
        No response is expected or required.

        Args:
            leds (list): List of RGB color values [R, G, B] 0-255.

        Example:
            Update LEDs via UDP::

                leds = [[255, 0, 255] for _ in range(60)]  # All magenta
                controller.update(leds)
        """
        # DRGB header
        packet = bytearray(b"DRGB")

        for r, g, b in leds:
            packet.extend(bytes((r, g, b)))

        self.sock.sendto(packet, self.addr)
