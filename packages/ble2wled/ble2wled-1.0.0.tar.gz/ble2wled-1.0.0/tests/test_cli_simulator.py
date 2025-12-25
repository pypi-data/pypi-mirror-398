"""Tests for CLI simulator module.

Comprehensive tests for the cli_simulator module covering:
- MQTTStatistics class
- StatisticsTrackingBeaconState class
- Signal handling
- Main function with mock and MQTT modes
- Command-line interface and argument validation
"""

import signal
import sys
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from ble2wled.cli_simulator import (
    MQTTStatistics,
    StatisticsTrackingBeaconState,
    handle_interrupt,
    main,
)


class TestMQTTStatistics:
    """Tests for MQTTStatistics class."""

    def test_init(self):
        """Test MQTTStatistics initialization."""
        stats = MQTTStatistics()

        assert stats.total_messages == 0
        assert stats.messages_by_beacon == {}
        assert stats.last_message_time is None
        assert hasattr(stats, "lock")

    def test_record_message_single(self):
        """Test recording a single message."""
        stats = MQTTStatistics()

        stats.record_message("beacon_001")

        assert stats.total_messages == 1
        assert stats.messages_by_beacon["beacon_001"] == 1

    def test_record_message_multiple_beacons(self):
        """Test recording messages from multiple beacons."""
        stats = MQTTStatistics()

        stats.record_message("beacon_001")
        stats.record_message("beacon_002")
        stats.record_message("beacon_001")

        assert stats.total_messages == 3
        assert stats.messages_by_beacon["beacon_001"] == 2
        assert stats.messages_by_beacon["beacon_002"] == 1

    def test_record_message_updates_last_message_time(self):
        """Test that recording message updates last_message_time."""
        stats = MQTTStatistics()

        before = time.time()
        stats.record_message("beacon_001")
        after = time.time()

        assert before <= stats.last_message_time <= after

    def test_get_stats_initial(self):
        """Test get_stats with no messages."""
        stats = MQTTStatistics()

        result = stats.get_stats()

        assert result["total"] == 0
        assert result["by_beacon"] == {}
        assert result["unique_beacons"] == 0
        assert result["elapsed"] >= 0  # Should have elapsed time
        assert result["rate"] >= 0  # Rate should be calculated

    def test_get_stats_with_messages(self):
        """Test get_stats with recorded messages."""
        stats = MQTTStatistics()

        stats.record_message("beacon_001")
        stats.record_message("beacon_002")
        stats.record_message("beacon_001")

        result = stats.get_stats()

        assert result["total"] == 3
        assert result["by_beacon"]["beacon_001"] == 2
        assert result["by_beacon"]["beacon_002"] == 1
        assert result["unique_beacons"] == 2

    def test_get_stats_calculates_rate(self):
        """Test that get_stats calculates message rate correctly."""
        stats = MQTTStatistics()

        # Record a message
        stats.record_message("beacon_001")

        result = stats.get_stats()

        # Rate should be messages / elapsed time
        assert result["rate"] > 0
        assert result["elapsed"] > 0
        assert (
            result["rate"] <= result["total"] / result["elapsed"] * 1.1
        )  # Allow 10% margin

    def test_record_message_thread_safety(self):
        """Test that recording messages is thread-safe."""
        stats = MQTTStatistics()

        def record_messages(beacon_id, count):
            for _ in range(count):
                stats.record_message(beacon_id)

        threads = [
            threading.Thread(target=record_messages, args=(f"beacon_{i}", 10))
            for i in range(5)
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert stats.total_messages == 50


class TestStatisticsTrackingBeaconState:
    """Tests for StatisticsTrackingBeaconState class."""

    def test_init(self):
        """Test StatisticsTrackingBeaconState initialization."""
        stats = MQTTStatistics()

        beacon_state = StatisticsTrackingBeaconState(stats)

        assert beacon_state.stats == stats

    def test_init_with_custom_timeouts(self):
        """Test initialization with custom timeout values."""
        stats = MQTTStatistics()

        beacon_state = StatisticsTrackingBeaconState(
            stats,
            timeout_seconds=10.0,
            fade_out_seconds=5.0,
        )

        assert beacon_state.stats == stats

    def test_update_records_statistics(self):
        """Test that update records statistics."""
        stats = MQTTStatistics()
        beacon_state = StatisticsTrackingBeaconState(stats)

        beacon_state.update("beacon_001", -50)

        assert stats.total_messages == 1
        assert stats.messages_by_beacon["beacon_001"] == 1

    def test_update_multiple_beacons(self):
        """Test updating multiple beacons records stats for each."""
        stats = MQTTStatistics()
        beacon_state = StatisticsTrackingBeaconState(stats)

        beacon_state.update("beacon_001", -50)
        beacon_state.update("beacon_002", -60)
        beacon_state.update("beacon_001", -55)

        assert stats.total_messages == 3
        assert stats.messages_by_beacon["beacon_001"] == 2
        assert stats.messages_by_beacon["beacon_002"] == 1

    def test_update_inherits_from_beacon_state(self):
        """Test that update maintains BeaconState functionality."""
        stats = MQTTStatistics()
        beacon_state = StatisticsTrackingBeaconState(stats)

        beacon_state.update("beacon_001", -50)

        # Should have beacon in snapshot
        snapshot = beacon_state.snapshot()
        assert "beacon_001" in snapshot


class TestHandleInterrupt:
    """Tests for signal handler."""

    def test_handle_interrupt_exits(self):
        """Test that handle_interrupt exits with code 0."""
        with pytest.raises(SystemExit) as exc_info:
            handle_interrupt(signal.SIGINT, None)

        assert exc_info.value.code == 0


class TestMainFunction:
    """Tests for main() function."""

    @patch("ble2wled.cli_simulator.LEDSimulator")
    @patch("ble2wled.cli_simulator.BeaconRunner")
    @patch("ble2wled.cli_simulator.BeaconState")
    @patch("ble2wled.cli_simulator.time.sleep")
    @patch("ble2wled.cli_simulator.time.time")
    def test_main_with_default_parameters(
        self,
        mock_time,
        mock_sleep,
        mock_beacon_state_cls,
        mock_beacon_runner_cls,
        mock_simulator_cls,
    ):
        """Test main with default parameters."""
        # Setup mocks
        mock_time.side_effect = [0, 0.1, 0.2, 0.3]  # For duration check
        mock_beacon_state = MagicMock()
        mock_beacon_state.snapshot.return_value = {}
        mock_beacon_state_cls.return_value = mock_beacon_state

        mock_simulator = MagicMock()
        mock_simulator_cls.return_value = mock_simulator

        mock_beacon_runner = MagicMock()
        mock_beacon_runner_cls.return_value = mock_beacon_runner

        # Run with duration to avoid infinite loop
        main(duration=0.05)

        # Verify components were created
        mock_simulator_cls.assert_called_once_with(led_count=60, rows=10, cols=6)
        mock_beacon_state_cls.assert_called_once()
        mock_beacon_runner_cls.assert_called_once_with(60)

    @patch("ble2wled.cli_simulator.LEDSimulator")
    @patch("ble2wled.cli_simulator.BeaconRunner")
    @patch("ble2wled.cli_simulator.BeaconState")
    @patch("ble2wled.cli_simulator.time.sleep")
    @patch("ble2wled.cli_simulator.time.time")
    def test_main_with_custom_led_count(
        self,
        mock_time,
        mock_sleep,
        mock_beacon_state_cls,
        mock_beacon_runner_cls,
        mock_simulator_cls,
    ):
        """Test main with custom LED count."""
        mock_time.side_effect = [0, 0.1, 0.2]
        mock_beacon_state = MagicMock()
        mock_beacon_state.snapshot.return_value = {}
        mock_beacon_state_cls.return_value = mock_beacon_state
        mock_simulator = MagicMock()
        mock_simulator_cls.return_value = mock_simulator
        mock_beacon_runner = MagicMock()
        mock_beacon_runner_cls.return_value = mock_beacon_runner

        main(led_count=120, rows=12, cols=10, duration=0.05)

        mock_simulator_cls.assert_called_once_with(led_count=120, rows=12, cols=10)
        mock_beacon_runner_cls.assert_called_once_with(120)

    @patch("ble2wled.cli_simulator.LEDSimulator")
    @patch("ble2wled.cli_simulator.BeaconRunner")
    @patch("ble2wled.cli_simulator.MockBeaconGenerator")
    @patch("ble2wled.cli_simulator.BeaconState")
    @patch("ble2wled.cli_simulator.time.sleep")
    @patch("ble2wled.cli_simulator.time.time")
    def test_main_mock_mode(
        self,
        mock_time,
        mock_sleep,
        mock_beacon_state_cls,
        mock_generator_cls,
        mock_beacon_runner_cls,
        mock_simulator_cls,
    ):
        """Test main with mock beacon generator."""
        # Use itertools.cycle to provide infinite time values
        import itertools

        mock_time.side_effect = itertools.cycle(
            [0, 0, 0.06, 0.12]
        )  # Will loop these values

        mock_beacon_state = MagicMock()
        mock_beacon_state.snapshot.return_value = {"beacon_001": (-50, 1.0)}
        mock_beacon_state_cls.return_value = mock_beacon_state
        mock_simulator = MagicMock()
        mock_simulator_cls.return_value = mock_simulator
        mock_beacon_runner = MagicMock()
        mock_beacon_runner.next_position.return_value = 0
        mock_beacon_runner_cls.return_value = mock_beacon_runner

        mock_generator = MagicMock()
        mock_generator.update.return_value = {"beacon_001": -50}
        mock_generator_cls.return_value = mock_generator

        main(use_mqtt=False, num_beacons=5, duration=0.05)

        # Verify generator was created
        mock_generator_cls.assert_called_once_with(num_beacons=5)
        # Verify generator.update was called
        assert mock_generator.update.called

    @patch("ble2wled.cli_simulator.LEDSimulator")
    @patch("ble2wled.cli_simulator.BeaconRunner")
    @patch("ble2wled.cli_simulator.EspresenseBeaconListener")
    @patch("ble2wled.cli_simulator.time.sleep")
    @patch("ble2wled.cli_simulator.time.time")
    def test_main_mqtt_mode(
        self,
        mock_time,
        mock_sleep,
        mock_mqtt_listener_cls,
        mock_beacon_runner_cls,
        mock_simulator_cls,
    ):
        """Test main with MQTT mode."""
        import itertools

        mock_time.side_effect = itertools.cycle(
            [0, 0, 0.06, 0.12]
        )  # Will loop these values

        mock_simulator = MagicMock()
        mock_simulator_cls.return_value = mock_simulator
        mock_beacon_runner = MagicMock()
        mock_beacon_runner.next_position.return_value = 0
        mock_beacon_runner_cls.return_value = mock_beacon_runner

        mock_beacon_state = MagicMock()
        mock_beacon_state.snapshot.return_value = {}

        mock_mqtt_listener = MagicMock()
        mock_mqtt_listener_cls.return_value = mock_mqtt_listener

        with patch(
            "ble2wled.cli_simulator.StatisticsTrackingBeaconState"
        ) as mock_stats_state:
            mock_stats_state.return_value = mock_beacon_state
            main(
                use_mqtt=True,
                mqtt_broker="192.168.1.100",
                mqtt_port=1883,
                mqtt_location="bedroom",
                duration=0.05,
            )

            # Verify MQTT listener was created with correct params
            call_kwargs = mock_mqtt_listener_cls.call_args[1]
            assert call_kwargs["broker"] == "192.168.1.100"
            assert call_kwargs["port"] == 1883
            assert call_kwargs["location"] == "bedroom"

    @patch("ble2wled.cli_simulator.LEDSimulator")
    @patch("ble2wled.cli_simulator.BeaconRunner")
    @patch("ble2wled.cli_simulator.EspresenseBeaconListener")
    @patch("ble2wled.cli_simulator.time.sleep")
    @patch("ble2wled.cli_simulator.time.time")
    def test_main_mqtt_with_auth(
        self,
        mock_time,
        mock_sleep,
        mock_mqtt_listener_cls,
        mock_beacon_runner_cls,
        mock_simulator_cls,
    ):
        """Test main with MQTT authentication."""
        import itertools

        mock_time.side_effect = itertools.cycle(
            [0, 0, 0.06, 0.12]
        )  # Will loop these values

        mock_simulator = MagicMock()
        mock_simulator_cls.return_value = mock_simulator
        mock_beacon_runner = MagicMock()
        mock_beacon_runner.next_position.return_value = 0
        mock_beacon_runner_cls.return_value = mock_beacon_runner

        mock_beacon_state = MagicMock()
        mock_beacon_state.snapshot.return_value = {}

        mock_mqtt_listener = MagicMock()
        mock_mqtt_listener_cls.return_value = mock_mqtt_listener

        with patch(
            "ble2wled.cli_simulator.StatisticsTrackingBeaconState"
        ) as mock_stats_state:
            mock_stats_state.return_value = mock_beacon_state
            main(
                use_mqtt=True,
                mqtt_broker="broker.example.com",
                mqtt_port=8883,
                mqtt_location="office",
                mqtt_username="user",
                mqtt_password="pass",
                duration=0.05,
            )

            # Verify MQTT listener was created with auth params
            call_kwargs = mock_mqtt_listener_cls.call_args[1]
            assert call_kwargs["username"] == "user"
            assert call_kwargs["password"] == "pass"

    @patch("ble2wled.cli_simulator.LEDSimulator")
    @patch("ble2wled.cli_simulator.BeaconRunner")
    @patch("ble2wled.cli_simulator.BeaconState")
    @patch("ble2wled.cli_simulator.time.sleep")
    @patch("ble2wled.cli_simulator.time.time")
    def test_main_invalid_grid_dimensions(
        self,
        mock_time,
        mock_sleep,
        mock_beacon_state_cls,
        mock_beacon_runner_cls,
        mock_simulator_cls,
    ):
        """Test main with mismatched LED count and grid dimensions."""
        with pytest.raises(ValueError) as exc_info:
            main(led_count=60, rows=10, cols=7)  # 10 * 7 = 70, not 60

        assert "does not equal led_count" in str(exc_info.value)

    @patch("ble2wled.cli_simulator.LEDSimulator")
    @patch("ble2wled.cli_simulator.BeaconRunner")
    @patch("ble2wled.cli_simulator.BeaconState")
    @patch("ble2wled.cli_simulator.time.sleep")
    @patch("ble2wled.cli_simulator.time.time")
    def test_main_update_interval(
        self,
        mock_time,
        mock_sleep,
        mock_beacon_state_cls,
        mock_beacon_runner_cls,
        mock_simulator_cls,
    ):
        """Test that main uses specified update interval."""
        import itertools

        mock_time.side_effect = itertools.cycle(
            [0, 0, 0.06, 0.12]
        )  # Will loop these values

        mock_beacon_state = MagicMock()
        mock_beacon_state.snapshot.return_value = {}
        mock_beacon_state_cls.return_value = mock_beacon_state
        mock_simulator = MagicMock()
        mock_simulator_cls.return_value = mock_simulator
        mock_beacon_runner = MagicMock()
        mock_beacon_runner_cls.return_value = mock_beacon_runner

        main(update_interval=0.05, duration=0.05)

        # Verify sleep was called with update_interval
        assert mock_sleep.called
        # Get the most recent call
        last_call = mock_sleep.call_args_list[-1]
        assert last_call[0][0] == 0.05

    @patch("ble2wled.cli_simulator.LEDSimulator")
    @patch("ble2wled.cli_simulator.BeaconRunner")
    @patch("ble2wled.cli_simulator.BeaconState")
    @patch("ble2wled.cli_simulator.ble_beacon_to_rgb")
    @patch("ble2wled.cli_simulator.add_trail")
    @patch("ble2wled.cli_simulator.time.sleep")
    @patch("ble2wled.cli_simulator.time.time")
    def test_main_renders_beacons(
        self,
        mock_time,
        mock_sleep,
        mock_add_trail,
        mock_beacon_to_rgb,
        mock_beacon_state_cls,
        mock_beacon_runner_cls,
        mock_simulator_cls,
    ):
        """Test that main renders beacons to simulator."""
        import itertools

        mock_time.side_effect = itertools.cycle(
            [0, 0, 0.06, 0.12]
        )  # Will loop these values

        mock_beacon_state = MagicMock()
        mock_beacon_state.snapshot.return_value = {"beacon_001": (-50, 0.8)}
        mock_beacon_state_cls.return_value = mock_beacon_state

        mock_simulator = MagicMock()
        mock_simulator_cls.return_value = mock_simulator

        mock_beacon_runner = MagicMock()
        mock_beacon_runner.next_position.return_value = 5
        mock_beacon_runner_cls.return_value = mock_beacon_runner

        mock_beacon_to_rgb.return_value = [255, 0, 0]

        main(led_count=60, duration=0.05)

        # Verify simulator.update was called
        assert mock_simulator.update.called

    @patch("ble2wled.cli_simulator.LEDSimulator")
    @patch("ble2wled.cli_simulator.BeaconRunner")
    @patch("ble2wled.cli_simulator.BeaconState")
    @patch("ble2wled.cli_simulator.time.sleep")
    @patch("ble2wled.cli_simulator.time.time")
    def test_main_respects_duration(
        self,
        mock_time,
        mock_sleep,
        mock_beacon_state_cls,
        mock_beacon_runner_cls,
        mock_simulator_cls,
    ):
        """Test that main stops after specified duration."""
        # Set times that will exceed duration
        mock_time.side_effect = [0, 5.0, 10.0]  # Start at 0, then 5, then 10
        mock_beacon_state = MagicMock()
        mock_beacon_state.snapshot.return_value = {}
        mock_beacon_state_cls.return_value = mock_beacon_state
        mock_simulator = MagicMock()
        mock_simulator_cls.return_value = mock_simulator
        mock_beacon_runner = MagicMock()
        mock_beacon_runner_cls.return_value = mock_beacon_runner

        main(duration=2.0)  # Should exit when time > 2.0

        # Should not raise error
        assert mock_simulator_cls.called


class TestCLIArgumentParsing:
    """Tests for CLI argument parsing."""

    def test_cli_defaults(self):
        """Test CLI with default arguments."""
        with patch.object(sys, "argv", ["cli_simulator"]):
            from ble2wled.cli_simulator import cli as cli_func

            with patch("ble2wled.cli_simulator.main") as mock_main:
                cli_func()

                # Verify main was called with defaults
                call_kwargs = mock_main.call_args[1]
                assert call_kwargs["led_count"] == 60
                assert call_kwargs["rows"] == 10
                assert call_kwargs["cols"] == 6
                assert call_kwargs["num_beacons"] == 3
                assert call_kwargs["update_interval"] == 0.1

    def test_cli_custom_led_count(self):
        """Test CLI with custom LED count."""
        with patch.object(
            sys,
            "argv",
            ["cli_simulator", "--led-count", "120", "--rows", "12", "--cols", "10"],
        ):
            from ble2wled.cli_simulator import cli as cli_func

            with patch("ble2wled.cli_simulator.main") as mock_main:
                cli_func()

                call_kwargs = mock_main.call_args[1]
                assert call_kwargs["led_count"] == 120
                assert call_kwargs["rows"] == 12
                assert call_kwargs["cols"] == 10

    def test_cli_custom_beacons(self):
        """Test CLI with custom beacon count."""
        with patch.object(sys, "argv", ["cli_simulator", "--beacons", "10"]):
            from ble2wled.cli_simulator import cli as cli_func

            with patch("ble2wled.cli_simulator.main") as mock_main:
                cli_func()

                call_kwargs = mock_main.call_args[1]
                assert call_kwargs["num_beacons"] == 10

    def test_cli_mqtt_mode(self):
        """Test CLI with MQTT mode enabled."""
        with patch.object(
            sys, "argv", ["cli_simulator", "--mqtt", "--mqtt-broker", "192.168.1.100"]
        ):
            from ble2wled.cli_simulator import cli as cli_func

            with patch("ble2wled.cli_simulator.main") as mock_main:
                cli_func()

                call_kwargs = mock_main.call_args[1]
                assert call_kwargs["use_mqtt"] is True
                assert call_kwargs["mqtt_broker"] == "192.168.1.100"

    def test_cli_mqtt_with_auth(self):
        """Test CLI with MQTT authentication."""
        with patch.object(
            sys,
            "argv",
            [
                "cli_simulator",
                "--mqtt",
                "--mqtt-broker",
                "broker.example.com",
                "--mqtt-username",
                "testuser",
                "--mqtt-password",
                "testpass",
            ],
        ):
            from ble2wled.cli_simulator import cli as cli_func

            with patch("ble2wled.cli_simulator.main") as mock_main:
                cli_func()

                call_kwargs = mock_main.call_args[1]
                assert call_kwargs["mqtt_username"] == "testuser"
                assert call_kwargs["mqtt_password"] == "testpass"

    def test_cli_invalid_led_count(self):
        """Test CLI rejects non-positive LED count."""
        with patch.object(sys, "argv", ["cli_simulator", "--led-count", "0"]):
            from ble2wled.cli_simulator import cli as cli_func

            with pytest.raises(SystemExit):
                cli_func()

    def test_cli_invalid_grid_dimensions(self):
        """Test CLI rejects mismatched grid dimensions."""
        with patch.object(
            sys,
            "argv",
            [
                "cli_simulator",
                "--led-count",
                "60",
                "--rows",
                "10",
                "--cols",
                "7",  # 10*7 = 70, not 60
            ],
        ):
            from ble2wled.cli_simulator import cli as cli_func

            with pytest.raises(SystemExit):
                cli_func()

    def test_cli_invalid_fade_factor(self):
        """Test CLI rejects invalid fade factor."""
        with patch.object(sys, "argv", ["cli_simulator", "--fade-factor", "1.5"]):
            from ble2wled.cli_simulator import cli as cli_func

            with pytest.raises(SystemExit):
                cli_func()

    def test_cli_invalid_mqtt_port(self):
        """Test CLI rejects invalid MQTT port."""
        with patch.object(
            sys, "argv", ["cli_simulator", "--mqtt", "--mqtt-port", "99999"]
        ):
            from ble2wled.cli_simulator import cli as cli_func

            with pytest.raises(SystemExit):
                cli_func()

    def test_cli_duration_argument(self):
        """Test CLI with custom duration."""
        with patch.object(sys, "argv", ["cli_simulator", "--duration", "30.5"]):
            from ble2wled.cli_simulator import cli as cli_func

            with patch("ble2wled.cli_simulator.main") as mock_main:
                cli_func()

                call_kwargs = mock_main.call_args[1]
                assert call_kwargs["duration"] == 30.5

    def test_cli_trail_settings(self):
        """Test CLI with custom trail settings."""
        with patch.object(
            sys,
            "argv",
            ["cli_simulator", "--trail-length", "15", "--fade-factor", "0.5"],
        ):
            from ble2wled.cli_simulator import cli as cli_func

            with patch("ble2wled.cli_simulator.main") as mock_main:
                cli_func()

                call_kwargs = mock_main.call_args[1]
                assert call_kwargs["trail_length"] == 15
                assert call_kwargs["fade_factor"] == 0.5
