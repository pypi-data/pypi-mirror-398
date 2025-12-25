"""Tests for Config class."""

import os
import tempfile
from pathlib import Path

import pytest

from ble2wled.config import Config


@pytest.fixture
def clean_env():
    """Clear relevant environment variables before and after each test."""
    # Store original values
    original_env = {}
    env_keys = [
        "WLED_HOST",
        "LED_COUNT",
        "MQTT_BROKER",
        "MQTT_PORT",
        "MQTT_LOCATION",
        "BEACON_TIMEOUT_SECONDS",
        "BEACON_FADE_OUT_SECONDS",
        "UPDATE_INTERVAL",
        "TRAIL_LENGTH",
        "FADE_FACTOR",
        "OUTPUT_MODE",
        "UDP_PORT",
        "HTTP_TIMEOUT",
        "LOG_LEVEL",
    ]

    for key in env_keys:
        original_env[key] = os.environ.get(key)
        if key in os.environ:
            del os.environ[key]

    yield

    # Restore original values
    for key, value in original_env.items():
        if value is not None:
            os.environ[key] = value
        elif key in os.environ:
            del os.environ[key]


class TestConfigDefaults:
    """Test default configuration values."""

    def test_default_wled_host(self, clean_env):
        """Test default WLED host."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.touch()
            config = Config(str(env_file))
            assert config.wled_host == "wled.local"

    def test_default_led_count(self, clean_env):
        """Test default LED count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.touch()
            config = Config(str(env_file))
            assert config.led_count == 60

    def test_default_mqtt_broker(self, clean_env):
        """Test default MQTT broker."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.touch()
            config = Config(str(env_file))
            assert config.mqtt_broker == "localhost"

    def test_default_mqtt_port(self, clean_env):
        """Test default MQTT port."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.touch()
            config = Config(str(env_file))
            assert config.mqtt_port == 1883

    def test_default_mqtt_location(self, clean_env):
        """Test default MQTT location."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.touch()
            config = Config(str(env_file))
            assert config.mqtt_location == "balkon"

    def test_default_beacon_timeout(self, clean_env):
        """Test default beacon timeout."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.touch()
            config = Config(str(env_file))
            assert config.beacon_timeout_seconds == 6.0

    def test_default_beacon_fade_out(self, clean_env):
        """Test default beacon fade out."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.touch()
            config = Config(str(env_file))
            assert config.beacon_fade_out_seconds == 4.0

    def test_default_update_interval(self, clean_env):
        """Test default update interval."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.touch()
            config = Config(str(env_file))
            assert config.update_interval == 0.2

    def test_default_trail_length(self, clean_env):
        """Test default trail length."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.touch()
            config = Config(str(env_file))
            assert config.trail_length == 10

    def test_default_fade_factor(self, clean_env):
        """Test default fade factor."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.touch()
            config = Config(str(env_file))
            assert config.fade_factor == 0.75

    def test_default_output_mode(self, clean_env):
        """Test default output mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.touch()
            config = Config(str(env_file))
            assert config.output_mode == "udp"

    def test_default_udp_port(self, clean_env):
        """Test default UDP port."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.touch()
            config = Config(str(env_file))
            assert config.udp_port == 21324

    def test_default_http_timeout(self, clean_env):
        """Test default HTTP timeout."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.touch()
            config = Config(str(env_file))
            assert config.http_timeout == 1


class TestConfigEnvironmentOverrides:
    """Test environment variable overrides."""

    def test_override_wled_host(self, clean_env):
        """Test overriding WLED host."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("WLED_HOST=192.168.1.100\n")
            config = Config(str(env_file))
            assert config.wled_host == "192.168.1.100"

    def test_override_led_count(self, clean_env):
        """Test overriding LED count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("LED_COUNT=120\n")
            config = Config(str(env_file))
            assert config.led_count == 120

    def test_override_mqtt_broker(self, clean_env):
        """Test overriding MQTT broker."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("MQTT_BROKER=mosquitto.local\n")
            config = Config(str(env_file))
            assert config.mqtt_broker == "mosquitto.local"

    def test_override_mqtt_port(self, clean_env):
        """Test overriding MQTT port."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("MQTT_PORT=8883\n")
            config = Config(str(env_file))
            assert config.mqtt_port == 8883

    def test_override_mqtt_location(self, clean_env):
        """Test overriding MQTT location."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("MQTT_LOCATION=bedroom\n")
            config = Config(str(env_file))
            assert config.mqtt_location == "bedroom"

    def test_override_trail_length(self, clean_env):
        """Test overriding trail length."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("TRAIL_LENGTH=20\n")
            config = Config(str(env_file))
            assert config.trail_length == 20

    def test_override_output_mode(self, clean_env):
        """Test overriding output mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("OUTPUT_MODE=http\n")
            config = Config(str(env_file))
            assert config.output_mode == "http"


class TestConfigTypeConversion:
    """Test type conversion from environment variables."""

    def test_led_count_type_conversion(self, clean_env):
        """Test LED count converts to int."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("LED_COUNT=100\n")
            config = Config(str(env_file))
            assert isinstance(config.led_count, int)
            assert config.led_count == 100

    def test_mqtt_port_type_conversion(self, clean_env):
        """Test MQTT port converts to int."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("MQTT_PORT=1883\n")
            config = Config(str(env_file))
            assert isinstance(config.mqtt_port, int)
            assert config.mqtt_port == 1883

    def test_beacon_timeout_type_conversion(self, clean_env):
        """Test beacon timeout converts to float."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("BEACON_TIMEOUT_SECONDS=5.5\n")
            config = Config(str(env_file))
            assert isinstance(config.beacon_timeout_seconds, float)
            assert config.beacon_timeout_seconds == 5.5

    def test_fade_factor_type_conversion(self, clean_env):
        """Test fade factor converts to float."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("FADE_FACTOR=0.5\n")
            config = Config(str(env_file))
            assert isinstance(config.fade_factor, float)
            assert config.fade_factor == 0.5


class TestConfigValidation:
    """Test configuration validation."""

    def test_validate_valid_config(self, clean_env):
        """Test validation passes with valid config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("FADE_FACTOR=0.75\nLED_COUNT=60\n")
            config = Config(str(env_file))
            config.validate()

    def test_validate_fade_factor_too_low(self, clean_env):
        """Test validation fails when fade factor is too low."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("FADE_FACTOR=0.0\n")
            config = Config(str(env_file))
            with pytest.raises(ValueError, match="FADE_FACTOR must be between"):
                config.validate()

    def test_validate_fade_factor_too_high(self, clean_env):
        """Test validation fails when fade factor is too high."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("FADE_FACTOR=1.1\n")
            config = Config(str(env_file))
            with pytest.raises(ValueError, match="FADE_FACTOR must be between"):
                config.validate()

    def test_validate_led_count_zero(self, clean_env):
        """Test validation fails when LED count is zero."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("LED_COUNT=0\n")
            config = Config(str(env_file))
            with pytest.raises(ValueError, match="LED_COUNT must be positive"):
                config.validate()

    def test_validate_invalid_output_mode(self, clean_env):
        """Test validation fails with invalid output mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("OUTPUT_MODE=invalid\n")
            config = Config(str(env_file))
            with pytest.raises(ValueError, match="OUTPUT_MODE must be"):
                config.validate()

    def test_validate_invalid_log_level(self, clean_env):
        """Test validation fails with invalid log level."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("LOG_LEVEL=INVALID\n")
            config = Config(str(env_file))
            with pytest.raises(ValueError, match="LOG_LEVEL must be"):
                config.validate()


class TestConfigToDict:
    """Test configuration dictionary export."""

    def test_to_dict_contains_all_properties(self, clean_env):
        """Test to_dict includes all configuration properties."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.touch()
            config = Config(str(env_file))
            config_dict = config.to_dict()

            assert "wled_host" in config_dict
            assert "led_count" in config_dict
            assert "mqtt_broker" in config_dict
            assert "mqtt_port" in config_dict
            assert "mqtt_location" in config_dict
            assert "beacon_timeout_seconds" in config_dict
            assert "beacon_fade_out_seconds" in config_dict
            assert "update_interval" in config_dict
            assert "trail_length" in config_dict
            assert "fade_factor" in config_dict
            assert "output_mode" in config_dict
            assert "udp_port" in config_dict
            assert "http_timeout" in config_dict
            assert "log_level" in config_dict

    def test_to_dict_values_correct(self, clean_env):
        """Test to_dict returns correct values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text(
                "WLED_HOST=test.local\nLED_COUNT=100\nMQTT_BROKER=broker.local\n"
            )
            config = Config(str(env_file))
            config_dict = config.to_dict()

            assert config_dict["wled_host"] == "test.local"
            assert config_dict["led_count"] == 100
            assert config_dict["mqtt_broker"] == "broker.local"

    def test_to_dict_is_dict(self, clean_env):
        """Test to_dict returns a dictionary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.touch()
            config = Config(str(env_file))
            config_dict = config.to_dict()

            assert isinstance(config_dict, dict)


class TestConfigComplexScenarios:
    """Test complex configuration scenarios."""

    def test_full_custom_config(self, clean_env):
        """Test loading a fully custom configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text(
                """
WLED_HOST=192.168.1.100
LED_COUNT=200
MQTT_BROKER=mosquitto.local
MQTT_LOCATION=kitchen
MQTT_PORT=1883
BEACON_TIMEOUT_SECONDS=5.0
BEACON_FADE_OUT_SECONDS=3.0
UPDATE_INTERVAL=0.1
TRAIL_LENGTH=15
FADE_FACTOR=0.8
OUTPUT_MODE=http
HTTP_TIMEOUT=2
LOG_LEVEL=DEBUG
"""
            )
            config = Config(str(env_file))
            config.validate()

            assert config.wled_host == "192.168.1.100"
            assert config.led_count == 200
            assert config.mqtt_broker == "mosquitto.local"
            assert config.mqtt_location == "kitchen"
            assert config.beacon_timeout_seconds == 5.0
            assert config.trail_length == 15
            assert config.output_mode == "http"

    def test_partial_custom_config(self, clean_env):
        """Test loading partial custom config with defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("WLED_HOST=custom.local\nLED_COUNT=100\n")
            config = Config(str(env_file))

            assert config.wled_host == "custom.local"
            assert config.led_count == 100
            assert config.mqtt_broker == "localhost"  # default
            assert config.trail_length == 10  # default

    def test_missing_env_file(self, clean_env):
        """Test loading config with missing env file uses defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / "nonexistent.env"
            config = Config(str(env_file))

            assert config.wled_host == "wled.local"
            assert config.led_count == 60
            assert config.mqtt_broker == "localhost"
