"""Main BLE to WLED beacon visualization loop.

This module provides the main animation loop for beacon visualization on WLED
LED strips. It manages the interaction between beacon detection, color
conversion, animation, and LED output.

Example:
    Run the complete beacon visualization system::

        from ble2wled import (
            BeaconState, EspresenseBeaconListener,
            WLEDUDPController, run_wled_beacons
        )

        # Initialize beacon state
        beacon_state = BeaconState(
            timeout_seconds=6.0,
            fade_out_seconds=4.0
        )

        # Start MQTT listener
        listener = EspresenseBeaconListener(
            beacon_state,
            broker='192.168.1.100',
            location='living_room'
        )
        listener.start()

        # Create LED controller
        controller = WLEDUDPController(
            'wled.local',
            led_count=60,
            port=21324
        )

        # Run animation loop
        run_wled_beacons(
            controller,
            led_count=60,
            beacon_state=beacon_state,
            update_interval=0.2,
            trail_length=10,
            fade_factor=0.75
        )
"""

import logging
import time
from typing import TYPE_CHECKING

from .animation import BeaconRunner, add_trail
from .colors import ble_beacon_to_rgb
from .config import Config
from .mqtt import EspresenseBeaconListener
from .states import BeaconState
from .wled import WLEDHTTPController, WLEDUDPController

if TYPE_CHECKING:
    from .wled import LEDController

logger = logging.getLogger(__name__)


def run_wled_beacons(
    controller: "LEDController",
    led_count: int,
    beacon_state: BeaconState,
    update_interval: float = 1.0,
    trail_length: int = 8,
    fade_factor: float = 0.7,
) -> None:
    """Main animation loop for beacon visualization.

    Continuously renders beacons from beacon_state onto LED strip via controller.
    Each beacon is rendered at its current position with a fading trail effect.

    Algorithm:
        1. Initialize LED array to black
        2. Get snapshot of active beacons from beacon_state
        3. For each beacon:
           - Get next animation position
           - Convert beacon data (RSSI, life) to RGB color
           - Add trail effect behind beacon
        4. Send LED update to controller
        5. Sleep for update_interval
        6. Repeat

    Args:
        controller (LEDController): LED controller instance (HTTP or UDP).
        led_count (int): Total number of LEDs in the strip.
        beacon_state (BeaconState): BeaconState instance with active beacons.
        update_interval (float): Seconds between LED updates. Default: 1.0.
            Typical values: 0.1-0.5 for smooth animation.
        trail_length (int): Number of LEDs in motion trail. Default: 8.
            Typical values: 5-15. Higher = longer trails, more CPU.
        fade_factor (float): Brightness decay per trail segment. Default: 0.7.
            Range: 0.0-1.0. Higher = brighter trails.

    Raises:
        ValueError: If parameters are invalid.

    Example:
        Run visualization loop::

            controller = WLEDUDPController('wled.local', led_count=60)
            state = BeaconState()
            run_wled_beacons(
                controller,
                led_count=60,
                beacon_state=state,
                update_interval=0.2,
                trail_length=10,
                fade_factor=0.75
            )
    """
    runner = BeaconRunner(led_count)

    while True:
        leds = [[0, 0, 0] for _ in range(led_count)]

        for beacon_id, (rssi, life) in beacon_state.snapshot().items():
            pos = runner.next_position(beacon_id)
            color = ble_beacon_to_rgb(beacon_id, rssi, life)
            add_trail(leds, pos, color, trail_length, fade_factor)

        controller.update(leds)
        time.sleep(update_interval)


def main():
    """Run the BLE to WLED beacon visualization system.

    This function initializes the configuration, logging, and system components
    required to visualize BLE beacons on a WLED LED strip. It starts the MQTT
    listener to track beacon signals and continuously updates the LED strip
    with beacon animations.

    Steps performed:
        1. Load configuration from a `.env` file.
        2. Configure logging.
        3. Validate configuration parameters.
        4. Initialize beacon state tracking.
        5. Start the Espresense MQTT listener.
        6. Create a WLED controller (UDP or HTTP) based on configuration.
        7. Run the main beacon animation loop, updating the LED strip at
           configured intervals until interrupted.

    Raises:
        ValueError: If the configuration is invalid.
        KeyboardInterrupt: When the user interrupts the animation loop.

    Example:
        Run the main function to start beacon visualization::

            if __name__ == "__main__":
                main()
    """
    # Load configuration from .env file
    config = Config(".env")

    # Configure logging
    logging.basicConfig(
        level=config.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger.info("Starting BLE2WLED beacon visualization")
    logger.debug("Configuration: %s", config.to_dict())

    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        logger.error("Configuration error: %s", e)
        raise

    # Initialize beacon state
    beacon_state = BeaconState(
        timeout_seconds=config.beacon_timeout_seconds,
        fade_out_seconds=config.beacon_fade_out_seconds,
    )

    # Start espresense MQTT listener
    mqtt_listener = EspresenseBeaconListener(
        beacon_state,
        config.mqtt_broker,
        location=config.mqtt_location,
        port=config.mqtt_port,
        username=config.mqtt_username,
        password=config.mqtt_password,
    )
    mqtt_listener.start()
    logger.info(
        "MQTT listener started for location '%s' on %s:%d",
        config.mqtt_location,
        config.mqtt_broker,
        config.mqtt_port,
    )

    # Create WLED controller
    if config.output_mode == "udp":
        controller = WLEDUDPController(
            config.wled_host, config.led_count, port=config.udp_port
        )
        logger.info(
            "Using WLED UDP controller at %s:%d with %d LEDs",
            config.wled_host,
            config.udp_port,
            config.led_count,
        )
    else:
        controller = WLEDHTTPController(config.wled_host, config.led_count)
        logger.info(
            "Using WLED HTTP controller at %s with %d LEDs",
            config.wled_host,
            config.led_count,
        )

    # Run main animation loop
    logger.info("Starting animation loop with interval %.2fs", config.update_interval)
    try:
        run_wled_beacons(
            controller,
            config.led_count,
            beacon_state,
            update_interval=config.update_interval,
            trail_length=config.trail_length,
            fade_factor=config.fade_factor,
        )
    except KeyboardInterrupt:
        logger.info("Animation loop interrupted by user, exiting...")


if __name__ == "__main__":
    main()
