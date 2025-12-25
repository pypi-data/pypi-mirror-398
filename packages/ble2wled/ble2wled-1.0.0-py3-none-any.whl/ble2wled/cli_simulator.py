#!/usr/bin/env python3
"""CLI simulator for testing BLE to WLED beacon visualization.

This script provides a command-line interface for testing beacon visualization
without requiring a real WLED device or MQTT broker. It runs the complete
visualization pipeline using mock beacons and a terminal-based simulator.

Usage:
    python -m ble2wled.cli_simulator [OPTIONS]

Options:
    --led-count: Number of LEDs (default: 60)
    --rows: Display grid rows (default: 10)
    --cols: Display grid columns (default: 6)
    --beacons: Number of mock beacons (default: 3)
    --update-interval: Update interval in seconds (default: 0.1)
    --trail-length: Length of motion trail (default: 8)
    --fade-factor: Trail fade factor 0-1 (default: 0.7)
    --duration: Run duration in seconds (default: infinite)
    --help: Show this help message
"""

import argparse
import logging
import signal
import sys
import threading
import time

from .animation import BeaconRunner, add_trail
from .colors import ble_beacon_to_rgb
from .mqtt import EspresenseBeaconListener
from .simulator import LEDSimulator, MockBeaconGenerator
from .states import BeaconState


class MQTTStatistics:
    """Track MQTT message statistics for real-time display.

    Monitors message count, rate, and per-beacon statistics.
    """

    def __init__(self):
        """Initialize statistics tracker."""
        self.total_messages = 0
        self.messages_by_beacon = {}
        self.last_message_time = None
        self.start_time = time.time()
        self.lock = threading.Lock()

    def record_message(self, beacon_id: str) -> None:
        """Record a received MQTT message.

        Args:
            beacon_id (str): ID of beacon that was received.
        """
        with self.lock:
            self.total_messages += 1
            self.messages_by_beacon[beacon_id] = (
                self.messages_by_beacon.get(beacon_id, 0) + 1
            )
            self.last_message_time = time.time()

    def get_stats(self) -> dict:
        """Get current statistics.

        Returns:
            dict: Statistics including total messages, rate, and per-beacon counts.
        """
        with self.lock:
            elapsed = time.time() - self.start_time
            rate = self.total_messages / elapsed if elapsed > 0 else 0
            return {
                "total": self.total_messages,
                "rate": rate,
                "elapsed": elapsed,
                "by_beacon": dict(self.messages_by_beacon),
                "unique_beacons": len(self.messages_by_beacon),
            }


class StatisticsTrackingBeaconState(BeaconState):
    """BeaconState wrapper that tracks MQTT statistics.

    Extends BeaconState to record statistics whenever beacons are updated.
    """

    def __init__(
        self,
        stats: MQTTStatistics,
        timeout_seconds: float = 5.0,
        fade_out_seconds: float = 3.0,
    ):
        """Initialize statistics tracking beacon state.

        Args:
            stats (MQTTStatistics): Statistics tracker instance.
            timeout_seconds (float): Beacon timeout in seconds. Default: 5.0.
            fade_out_seconds (float): Beacon fade-out in seconds. Default: 3.0.
        """
        super().__init__(timeout_seconds, fade_out_seconds)
        self.stats = stats

    def update(self, beacon_id: str, rssi: int) -> None:
        """Update beacon and record statistics.

        Args:
            beacon_id (str): Beacon identifier.
            rssi (int): Signal strength in dBm.
        """
        super().update(beacon_id, rssi)
        self.stats.record_message(beacon_id)


def handle_interrupt(_signum, _frame):
    """Handle Ctrl+C gracefully."""
    print("\n\nSimulation stopped.")
    sys.exit(0)


def main(
    led_count: int = 60,
    rows: int = 10,
    cols: int = 6,
    num_beacons: int = 3,
    update_interval: float = 0.1,
    trail_length: int = 8,
    fade_factor: float = 0.7,
    duration: float | None = None,
    use_mqtt: bool = False,
    mqtt_broker: str = "localhost",
    mqtt_port: int = 1883,
    mqtt_location: str = "balkon",
    mqtt_username: str | None = None,
    mqtt_password: str | None = None,
) -> None:
    """Run the CLI simulator.

    Args:
        led_count (int): Total number of LEDs. Default: 60.
        rows (int): Display grid rows. Default: 10.
        cols (int): Display grid columns. Default: 6.
        num_beacons (int): Number of mock beacons (if not using MQTT). Default: 3.
        update_interval (float): Seconds between updates. Default: 0.1.
        trail_length (int): LED trail length. Default: 8.
        fade_factor (float): Trail fade factor (0-1). Default: 0.7.
        duration (Optional[float]): Run duration in seconds. Default: None (infinite).
        use_mqtt (bool): Use real MQTT data instead of mock beacons. Default: False.
        mqtt_broker (str): MQTT broker hostname. Default: 'localhost'.
        mqtt_port (int): MQTT broker port. Default: 1883.
        mqtt_location (str): MQTT location filter. Default: 'balkon'.
        mqtt_username (Optional[str]): MQTT username for authentication. Default: None.
        mqtt_password (Optional[str]): MQTT password for authentication. Default: None.

    Example:
        Run simulator with 100 LEDs for 60 seconds::

            main(
                led_count=100,
                rows=10,
                cols=10,
                duration=60.0
            )

        Run simulator with real MQTT data and authentication::

            main(
                use_mqtt=True,
                mqtt_broker='192.168.1.100',
                mqtt_location='living_room',
                mqtt_username='user',
                mqtt_password='pass'
            )
    """
    # Setup signal handler for graceful shutdown
    signal.signal(signal.SIGINT, handle_interrupt)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    # Validate inputs
    if rows * cols != led_count:
        raise ValueError(
            f"rows ({rows}) × cols ({cols}) = {rows * cols} "
            f"does not equal led_count ({led_count})"
        )

    logger.info("Initializing BLE2WLED LED Simulator")

    beacon_source = "MQTT" if use_mqtt else "Mock Generator"
    logger.info(
        "Configuration: %d LEDs (%dx%d), beacon source: %s, %.2fs interval",
        led_count,
        rows,
        cols,
        beacon_source,
        update_interval,
    )

    # Initialize components
    simulator = LEDSimulator(led_count=led_count, rows=rows, cols=cols)

    # Initialize statistics tracker for MQTT mode
    mqtt_stats: MQTTStatistics | None = None
    if use_mqtt:
        mqtt_stats = MQTTStatistics()
        beacon_state = StatisticsTrackingBeaconState(
            mqtt_stats, timeout_seconds=3.0, fade_out_seconds=2.0
        )
    else:
        beacon_state = BeaconState(timeout_seconds=3.0, fade_out_seconds=2.0)

    beacon_runner = BeaconRunner(led_count)

    # Initialize beacon source
    beacon_generator: MockBeaconGenerator | None = None
    mqtt_listener: EspresenseBeaconListener | None = None

    if use_mqtt:
        logger.info(
            "Connecting to MQTT broker at %s:%d, listening to location '%s'",
            mqtt_broker,
            mqtt_port,
            mqtt_location,
        )
        mqtt_listener = EspresenseBeaconListener(
            beacon_state,
            broker=mqtt_broker,
            location=mqtt_location,
            port=mqtt_port,
            username=mqtt_username,
            password=mqtt_password,
        )
        mqtt_listener.start()
        logger.info("MQTT listener started")
    else:
        logger.info("Initializing mock beacon generator with %d beacons", num_beacons)
        beacon_generator = MockBeaconGenerator(num_beacons=num_beacons)

    logger.info("Simulator ready. Starting animation loop...")
    print("\n" + "=" * 80)
    print("BLE2WLED LED Strip Simulator")
    print("=" * 80)
    print(f"LED Count: {led_count} ({rows}x{cols} grid)")
    if use_mqtt:
        print(
            f"Beacon Source: MQTT ({mqtt_broker}:{mqtt_port}, location={mqtt_location})"
        )
    else:
        print(f"Beacon Source: Mock Generator ({num_beacons} beacons)")
    print(f"Update Interval: {update_interval:.2f}s")
    print(f"Trail Length: {trail_length}")
    print(f"Fade Factor: {fade_factor}")
    if duration:
        print(f"Duration: {duration:.1f}s")
    print("Press Ctrl+C to exit")
    print("=" * 80 + "\n")

    start_time = time.time()
    frame_count = 0

    try:
        while True:
            # Check if duration exceeded
            if duration and time.time() - start_time > duration:
                logger.info("Duration limit reached. Stopping simulation.")
                break

            frame_count += 1

            # Generate or receive beacon data
            if use_mqtt:
                # With MQTT, beacon_state is updated automatically by listener
                # Just get snapshot to render
                pass
            else:
                # With mock generator, manually update beacon_state
                if beacon_generator:
                    beacon_data = beacon_generator.update(time_delta=update_interval)
                    for beacon_id, rssi in beacon_data.items():
                        beacon_state.update(beacon_id, rssi)

            # Render LED strip
            leds = [[0, 0, 0] for _ in range(led_count)]

            for beacon_id, (rssi, life) in beacon_state.snapshot().items():
                pos = beacon_runner.next_position(beacon_id)
                color = ble_beacon_to_rgb(beacon_id, rssi, life)
                add_trail(leds, pos, color, trail_length, fade_factor)

            # Update simulator display
            simulator.update(leds)

            # Display MQTT statistics if enabled
            if use_mqtt and mqtt_stats:
                stats = mqtt_stats.get_stats()
                active_beacons = len(beacon_state.snapshot())
                elapsed = stats["elapsed"]
                fps = frame_count / elapsed if elapsed > 0 else 0

                # Format statistics display
                print(
                    f"\rMQTT: {stats['total']:4d} msgs | "
                    f"{stats['rate']:6.1f} msg/s | "
                    f"Beacons: {active_beacons:2d} | "
                    f"FPS: {fps:5.1f} | "
                    f"Time: {int(elapsed // 60):02d}:{int(elapsed % 60):02d}",
                    end="",
                    flush=True,
                )

            # Sleep for update interval
            time.sleep(update_interval)

    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user.")
    finally:
        logger.info(
            "Simulation complete. Rendered %d frames in %.2fs",
            frame_count,
            time.time() - start_time,
        )


def cli():
    """Command-line interface for the simulator."""
    parser = argparse.ArgumentParser(
        description="BLE2WLED LED Strip Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings (60 LEDs, 3 mock beacons)
  python -m ble2wled.cli_simulator

  # Simulate 120-LED strip with 5 mock beacons
  python -m ble2wled.cli_simulator --led-count 120 --rows 12 --cols 10 --beacons 5

  # Run for 30 seconds with faster updates
  python -m ble2wled.cli_simulator --duration 30 --update-interval 0.05

  # Use real MQTT data from espresense
  python -m ble2wled.cli_simulator --mqtt --mqtt-broker 192.168.1.100 --mqtt-location living_room

  # Use MQTT with custom LED grid
  python -m ble2wled.cli_simulator --mqtt --mqtt-broker 192.168.1.100 --led-count 100 --rows 20 --cols 5
        """,
    )

    parser.add_argument(
        "--led-count",
        type=int,
        default=60,
        help="Total number of LEDs (default: 60)",
    )

    parser.add_argument(
        "--rows",
        type=int,
        default=10,
        help="Display grid rows (default: 10)",
    )

    parser.add_argument(
        "--cols",
        type=int,
        default=6,
        help="Display grid columns (default: 6)",
    )

    parser.add_argument(
        "--beacons",
        type=int,
        default=3,
        help="Number of mock beacons (default: 3, ignored with --mqtt)",
    )

    parser.add_argument(
        "--update-interval",
        type=float,
        default=0.1,
        help="Update interval in seconds (default: 0.1)",
    )

    parser.add_argument(
        "--trail-length",
        type=int,
        default=8,
        help="Length of motion trail (default: 8)",
    )

    parser.add_argument(
        "--fade-factor",
        type=float,
        default=0.7,
        help="Trail fade factor 0-1 (default: 0.7)",
    )

    parser.add_argument(
        "--duration",
        type=float,
        default=None,
        help="Run duration in seconds (default: infinite)",
    )

    parser.add_argument(
        "--mqtt",
        action="store_true",
        help="Use real MQTT data instead of mock beacons",
    )

    parser.add_argument(
        "--mqtt-broker",
        type=str,
        default="localhost",
        help="MQTT broker hostname or IP (default: localhost)",
    )

    parser.add_argument(
        "--mqtt-port",
        type=int,
        default=1883,
        help="MQTT broker port (default: 1883)",
    )

    parser.add_argument(
        "--mqtt-location",
        type=str,
        default="balkon",
        help="MQTT location filter for beacons (default: balkon)",
    )

    parser.add_argument(
        "--mqtt-username",
        type=str,
        default=None,
        help="MQTT broker username for authentication (default: None)",
    )

    parser.add_argument(
        "--mqtt-password",
        type=str,
        default=None,
        help="MQTT broker password for authentication (default: None)",
    )

    args = parser.parse_args()

    # Validate arguments
    if args.led_count <= 0:
        parser.error("--led-count must be positive")
    if args.rows <= 0 or args.cols <= 0:
        parser.error("--rows and --cols must be positive")
    if args.rows * args.cols != args.led_count:
        parser.error(
            f"rows ({args.rows}) × cols ({args.cols}) "
            f"must equal led_count ({args.led_count})"
        )
    if args.beacons <= 0:
        parser.error("--beacons must be positive")
    if args.update_interval <= 0:
        parser.error("--update-interval must be positive")
    if args.trail_length <= 0:
        parser.error("--trail-length must be positive")
    if not 0 <= args.fade_factor <= 1:
        parser.error("--fade-factor must be between 0 and 1")
    if args.mqtt_port <= 0 or args.mqtt_port > 65535:
        parser.error("--mqtt-port must be between 1 and 65535")

    # Run simulator
    main(
        led_count=args.led_count,
        rows=args.rows,
        cols=args.cols,
        num_beacons=args.beacons,
        update_interval=args.update_interval,
        trail_length=args.trail_length,
        fade_factor=args.fade_factor,
        duration=args.duration,
        use_mqtt=args.mqtt,
        mqtt_broker=args.mqtt_broker,
        mqtt_port=args.mqtt_port,
        mqtt_location=args.mqtt_location,
        mqtt_username=args.mqtt_username,
        mqtt_password=args.mqtt_password,
    )


if __name__ == "__main__":
    cli()
