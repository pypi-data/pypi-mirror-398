"""Configuration management using environment variables and .env files.

This module provides centralized configuration management for BLE2WLED using
environment variables and .env files. Configuration is loaded from .env on
initialization and provides property-based access with type conversion,
validation, and sensible defaults.

Configuration Hierarchy:
    1. .env file (if it exists)
    2. Environment variables
    3. Default values

Example:
    Load and use configuration::

        from ble2wled.config import Config

        config = Config('.env')
        config.validate()  # Check all values are valid

        # Access configuration properties
        print(f"WLED host: {config.wled_host}")
        print(f"LED count: {config.led_count}")
        print(f"MQTT broker: {config.mqtt_broker}")

        # Log all configuration
        import json
        print(json.dumps(config.to_dict(), indent=2))
"""

import logging
import os
from typing import TYPE_CHECKING

from dotenv import load_dotenv

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class Config:
    """Centralized configuration management for BLE2WLED.

    Loads configuration from .env file and environment variables. Provides
    property-based access to configuration with automatic type conversion,
    validation, and sensible defaults.

    All configuration values are read through environment variables, which
    can be set via .env file or directly in the process environment.

    Attributes:
        wled_host (str): WLED device hostname or IP.
        led_count (int): Number of LEDs in the strip.
        output_mode (str): LED output protocol ('udp' or 'http').
        mqtt_broker (str): MQTT broker hostname or IP.
        mqtt_location (str): Location filter for beacons.
        mqtt_port (int): MQTT broker port.
    """

    def __init__(self, env_file: str | None = None):
        """Initialize configuration.

        Loads environment variables from .env file if it exists. Configuration
        properties can then be accessed via the property methods.

        Args:
            env_file (str): Path to .env file. If None, defaults to \".env\"
                in the current directory.

        Example:
            Load configuration from default .env file::

                config = Config()  # Loads from .env

            Or from a specific file::

                config = Config('/path/to/.env.production')
        """
        # Load .env file if it exists
        if env_file is None:
            env_file = ".env"

        if os.path.exists(env_file):
            load_dotenv(env_file, verbose=True)
            logger.info("Loaded configuration from %s", env_file)
        else:
            logger.warning("Configuration file %s not found", env_file)

    # WLED Configuration
    @property
    def wled_host(self) -> str:
        """WLED device hostname or IP address.

        Default: 'wled.local'

        Returns:
            str: Hostname or IP address of WLED device.

        Example:
            Access WLED host::

                print(config.wled_host)  # 'wled.local'
        """
        return os.getenv("WLED_HOST", "wled.local")

    @property
    def led_count(self) -> int:
        """Number of LEDs in the strip.

        Default: 60

        Returns:
            int: LED count (must be positive).

        Raises:
            ValueError: If LED_COUNT is not positive.

        Example:
            Access LED count::

                leds = [[0, 0, 0] for _ in range(config.led_count)]
        """
        count = int(os.getenv("LED_COUNT", "60"))
        if count <= 0:
            raise ValueError(f"LED_COUNT must be positive, got {count}")
        return count

    @property
    def output_mode(self) -> str:
        """LED output mode: 'udp' or 'http'.

        - 'udp': Fast real-time protocol (DRGB)
        - 'http': Slower but more reliable JSON API

        Default: 'udp'

        Returns:
            str: Output mode ('udp' or 'http').

        Raises:
            ValueError: If OUTPUT_MODE is not 'udp' or 'http'.

        Example:
            Check output mode::

                if config.output_mode == 'udp':
                    print('Using fast UDP updates')
        """
        mode = os.getenv("OUTPUT_MODE", "udp").lower()
        if mode not in ("udp", "http"):
            raise ValueError(f"OUTPUT_MODE must be 'udp' or 'http', got {mode}")
        return mode

    @property
    def http_timeout(self) -> float:
        """HTTP request timeout in seconds.

        Default: 1.0

        Returns:
            float: Timeout in seconds.

        Example:
            Set HTTP request timeout::

                requests.post(url, json=data, timeout=config.http_timeout)
        """
        return float(os.getenv("HTTP_TIMEOUT", "1"))

    @property
    def udp_port(self) -> int:
        """UDP DRGB protocol port.

        Default: 21324

        Returns:
            int: UDP port number.

        Example:
            Use configured UDP port::

                controller = WLEDUDPController(
                    config.wled_host,
                    config.led_count,
                    port=config.udp_port
                )
        """
        return int(os.getenv("UDP_PORT", "21324"))

    # MQTT Configuration
    @property
    def mqtt_broker(self) -> str:
        """MQTT broker hostname or IP address.

        Default: 'localhost'

        Returns:
            str: MQTT broker hostname or IP.

        Example:
            Connect to MQTT broker::

                listener = EspresenseBeaconListener(
                    state,
                    broker=config.mqtt_broker,
                    port=config.mqtt_port
                )
        """
        return os.getenv("MQTT_BROKER", "localhost")

    @property
    def mqtt_location(self) -> str:
        """Location name for espresense filtering.

        Used to filter beacon messages from a specific location.
        Example values: 'balkon', 'bedroom', 'living_room'

        Default: 'balkon'

        Returns:
            str: Location name.

        Example:
            Filter beacons by location::

                listener = EspresenseBeaconListener(
                    state,
                    broker=config.mqtt_broker,
                    location=config.mqtt_location
                )
        """
        return os.getenv("MQTT_LOCATION", "balkon")

    @property
    def mqtt_port(self) -> int:
        """MQTT broker port.

        Default: 1883

        Returns:
            int: MQTT port number.
        """
        return int(os.getenv("MQTT_PORT", "1883"))

    @property
    def mqtt_username(self) -> str | None:
        """MQTT broker username for authentication.

        If set, used to authenticate with the MQTT broker.

        Default: None (no authentication)

        Returns:
            Optional[str]: MQTT username or None if not set.

        Example:
            Authenticate with MQTT broker::

                if config.mqtt_username:
                    client.username_pw_set(
                        config.mqtt_username,
                        config.mqtt_password
                    )
        """
        return os.getenv("MQTT_USERNAME")

    @property
    def mqtt_password(self) -> str | None:
        """MQTT broker password for authentication.

        If set along with mqtt_username, used to authenticate with the MQTT broker.

        Default: None (no authentication)

        Returns:
            Optional[str]: MQTT password or None if not set.
        """
        return os.getenv("MQTT_PASSWORD")

    # Beacon State Configuration
    @property
    def beacon_timeout_seconds(self) -> float:
        """Beacon timeout duration in seconds.

        Time before a beacon is considered timed out (no updates received).

        Default: 6.0

        Returns:
            float: Timeout duration in seconds.

        Example:
            Create beacon state with configured timeout::

                state = BeaconState(
                    timeout_seconds=config.beacon_timeout_seconds,
                    fade_out_seconds=config.beacon_fade_out_seconds
                )
        """
        return float(os.getenv("BEACON_TIMEOUT_SECONDS", "6.0"))

    @property
    def beacon_fade_out_seconds(self) -> float:
        """Beacon fade-out duration in seconds.

        Time to fade out a beacon after timeout.

        Default: 4.0

        Returns:
            float: Fade-out duration in seconds.
        """
        return float(os.getenv("BEACON_FADE_OUT_SECONDS", "4.0"))

    # Animation Configuration
    @property
    def update_interval(self) -> float:
        """LED update interval in seconds.

        Time between LED updates. Smaller values = smoother but higher CPU.

        Default: 0.2

        Returns:
            float: Update interval in seconds.

        Example:
            Run animation loop with configured interval::

                run_wled_beacons(
                    controller,
                    led_count=config.led_count,
                    beacon_state=state,
                    update_interval=config.update_interval,
                    trail_length=config.trail_length,
                    fade_factor=config.fade_factor
                )
        """
        return float(os.getenv("UPDATE_INTERVAL", "0.2"))

    @property
    def trail_length(self) -> int:
        """Motion trail length in LEDs.

        Number of LEDs in the motion trail behind each beacon.

        Default: 10

        Returns:
            int: Trail length in LEDs.

        Example:
            Use trail length for rendering::

                add_trail(leds, pos, color, trail_length=config.trail_length,
                         fade_factor=config.fade_factor)
        """
        return int(os.getenv("TRAIL_LENGTH", "10"))

    @property
    def fade_factor(self) -> float:
        """Trail brightness fade factor per segment.

        Brightness decay per trail segment (0.0 < x <= 1.0).
        0.75 = each segment is 75% brightness of previous.

        Default: 0.75

        Returns:
            float: Fade factor (0.0 to 1.0).

        Raises:
            ValueError: If fade factor is not in valid range.

        Example:
            Configure trail rendering::

                add_trail(leds, pos, color,
                         trail_length=config.trail_length,
                         fade_factor=config.fade_factor)
        """
        fade = float(os.getenv("FADE_FACTOR", "0.75"))
        if not 0.0 < fade <= 1.0:
            raise ValueError(f"FADE_FACTOR must be between 0 and 1, got {fade}")
        return fade

    # Logging Configuration
    @property
    def log_level(self) -> str:
        """Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).

        Controls verbosity of application logging.

        Default: 'INFO'

        Returns:
            str: Log level name (DEBUG, INFO, WARNING, ERROR, CRITICAL).

        Raises:
            ValueError: If log level is not recognized.

        Example:
            Configure logging::

                import logging
                logging.basicConfig(level=config.log_level)
        """
        level = os.getenv("LOG_LEVEL", "INFO").upper()
        valid_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        if level not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}, got {level}")
        return level

    def validate(self) -> None:
        """Validate all configuration values.

        Runs all property getters to check for invalid values. Useful for
        catching configuration errors at startup.

        Raises:
            ValueError: If any configuration value is invalid.

        Example:
            Validate configuration on startup::

                config = Config('.env')
                try:
                    config.validate()
                    print(\"Configuration is valid\")
                except ValueError as e:
                    print(f\"Configuration error: {e}\")
                    sys.exit(1)
        """
        # Trigger all properties to validate
        _ = self.output_mode
        _ = self.led_count
        _ = self.fade_factor
        _ = self.log_level
        _ = self.mqtt_port
        _ = self.udp_port
        _ = self.http_timeout
        _ = self.beacon_timeout_seconds
        _ = self.beacon_fade_out_seconds
        _ = self.update_interval
        _ = self.trail_length

    def to_dict(self) -> dict:
        """Export configuration as dictionary.

        Returns all configuration values as a dictionary. Useful for logging
        or debugging configuration state.

        Returns:
            dict: Dictionary with all configuration values.

        Example:
            Log configuration on startup::

                import json
                config = Config('.env')
                print(json.dumps(config.to_dict(), indent=2))
        """
        return {
            # WLED
            "wled_host": self.wled_host,
            "led_count": self.led_count,
            "output_mode": self.output_mode,
            "http_timeout": self.http_timeout,
            "udp_port": self.udp_port,
            # MQTT
            "mqtt_broker": self.mqtt_broker,
            "mqtt_location": self.mqtt_location,
            "mqtt_port": self.mqtt_port,
            "mqtt_username": self.mqtt_username,
            "mqtt_password": self.mqtt_password,
            # Beacon State
            "beacon_timeout_seconds": self.beacon_timeout_seconds,
            "beacon_fade_out_seconds": self.beacon_fade_out_seconds,
            # Animation
            "update_interval": self.update_interval,
            "trail_length": self.trail_length,
            "fade_factor": self.fade_factor,
            # Logging
            "log_level": self.log_level,
        }
