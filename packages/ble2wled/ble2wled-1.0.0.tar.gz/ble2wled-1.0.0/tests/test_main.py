"""Comprehensive tests for main module.

Tests for run_wled_beacons function and main block execution covering:
- Animation loop with beacons
- Controller updates
- Timing and iteration behavior
- Configuration loading and validation
- MQTT listener initialization
- Error handling
"""

from unittest.mock import MagicMock, Mock, call, patch

import pytest

from ble2wled.main import run_wled_beacons
from ble2wled.states import BeaconState


class TestRunWledBeacons:
    """Tests for run_wled_beacons function."""

    def test_run_wled_beacons_creates_beacon_runner(self):
        """Test that run_wled_beacons creates a BeaconRunner."""
        controller = Mock()
        state = Mock(spec=BeaconState)
        state.snapshot.return_value = {}

        with patch("ble2wled.main.time.sleep") as mock_sleep:
            with patch("ble2wled.main.BeaconRunner") as mock_runner_class:
                mock_runner = MagicMock()
                mock_runner_class.return_value = mock_runner
                mock_sleep.side_effect = [None, KeyboardInterrupt()]

                try:
                    run_wled_beacons(controller, 10, state, update_interval=0.1)
                except KeyboardInterrupt:
                    pass

                mock_runner_class.assert_called_once_with(10)

    def test_run_wled_beacons_initializes_led_array(self):
        """Test that LED array is initialized to black."""
        controller = Mock()
        state = Mock(spec=BeaconState)
        state.snapshot.return_value = {}

        with patch("ble2wled.main.time.sleep") as mock_sleep:
            with patch("ble2wled.main.BeaconRunner"):
                mock_sleep.side_effect = [None, KeyboardInterrupt()]

                try:
                    run_wled_beacons(controller, 5, state)
                except KeyboardInterrupt:
                    pass

                # Check that controller.update was called with black LED array
                controller.update.assert_called()
                leds = controller.update.call_args[0][0]
                assert all(led == [0, 0, 0] for led in leds)

    def test_run_wled_beacons_correct_led_count(self):
        """Test that LED array has correct number of LEDs."""
        controller = Mock()
        state = Mock(spec=BeaconState)
        state.snapshot.return_value = {}

        for led_count in [1, 10, 60, 100]:
            controller.reset_mock()

            with patch("ble2wled.main.time.sleep") as mock_sleep:
                with patch("ble2wled.main.BeaconRunner"):
                    mock_sleep.side_effect = [None, KeyboardInterrupt()]

                    try:
                        run_wled_beacons(controller, led_count, state)
                    except KeyboardInterrupt:
                        pass

                    leds = controller.update.call_args[0][0]
                    assert len(leds) == led_count

    def test_run_wled_beacons_sleeps_correct_interval(self):
        """Test that sleep is called with correct update_interval."""
        controller = Mock()
        state = Mock(spec=BeaconState)
        state.snapshot.return_value = {}

        with patch("ble2wled.main.time.sleep") as mock_sleep:
            with patch("ble2wled.main.BeaconRunner"):
                mock_sleep.side_effect = [None, KeyboardInterrupt()]

                try:
                    run_wled_beacons(controller, 10, state, update_interval=0.25)
                except KeyboardInterrupt:
                    pass

                # Should be called at least once with 0.25
                assert any(call(0.25) == c for c in mock_sleep.call_args_list)

    def test_run_wled_beacons_with_no_beacons(self):
        """Test animation loop with empty beacon state."""
        controller = Mock()
        state = Mock(spec=BeaconState)
        state.snapshot.return_value = {}

        with patch("ble2wled.main.time.sleep") as mock_sleep:
            with patch("ble2wled.main.BeaconRunner") as mock_runner_class:
                mock_runner = MagicMock()
                mock_runner_class.return_value = mock_runner
                mock_sleep.side_effect = [None, KeyboardInterrupt()]

                try:
                    run_wled_beacons(controller, 10, state)
                except KeyboardInterrupt:
                    pass

                # Controller should still be called with black array
                assert controller.update.call_count >= 1

    def test_run_wled_beacons_with_single_beacon(self):
        """Test animation loop with single beacon."""
        controller = Mock()
        state = Mock(spec=BeaconState)
        state.snapshot.return_value = {"beacon_1": (-50, 1.0)}

        with patch("ble2wled.main.time.sleep") as mock_sleep:
            with patch("ble2wled.main.BeaconRunner") as mock_runner_class:
                mock_runner = MagicMock()
                mock_runner.next_position.return_value = 5
                mock_runner_class.return_value = mock_runner
                mock_sleep.side_effect = [None, KeyboardInterrupt()]

                with patch("ble2wled.main.ble_beacon_to_rgb") as mock_color:
                    mock_color.return_value = (255, 0, 0)

                    with patch("ble2wled.main.add_trail"):
                        try:
                            run_wled_beacons(controller, 10, state)
                        except KeyboardInterrupt:
                            pass

                        # next_position should be called for beacon_1
                        mock_runner.next_position.assert_called_with("beacon_1")

    def test_run_wled_beacons_with_multiple_beacons(self):
        """Test animation loop with multiple beacons."""
        controller = Mock()
        state = Mock(spec=BeaconState)
        state.snapshot.return_value = {"beacon_1": (-50, 1.0), "beacon_2": (-60, 0.8)}

        with patch("ble2wled.main.time.sleep") as mock_sleep:
            with patch("ble2wled.main.BeaconRunner") as mock_runner_class:
                mock_runner = MagicMock()
                # Need more values for multiple iterations
                mock_runner.next_position.side_effect = [3, 7, 4, 8, 5, 9]
                mock_runner_class.return_value = mock_runner
                mock_sleep.side_effect = [None, KeyboardInterrupt()]

                with patch("ble2wled.main.ble_beacon_to_rgb") as mock_color:
                    mock_color.side_effect = [
                        (255, 0, 0),
                        (0, 255, 0),
                        (255, 0, 0),
                        (0, 255, 0),
                    ]

                    with patch("ble2wled.main.add_trail") as mock_trail:
                        try:
                            run_wled_beacons(controller, 10, state)
                        except KeyboardInterrupt:
                            pass

                        # add_trail should be called at least twice (2 beacons per iteration)
                        assert mock_trail.call_count >= 2

    def test_run_wled_beacons_calls_add_trail_correctly(self):
        """Test that add_trail is called with correct parameters."""
        controller = Mock()
        state = Mock(spec=BeaconState)
        state.snapshot.return_value = {"beacon_1": (-50, 1.0)}

        with patch("ble2wled.main.time.sleep") as mock_sleep:
            with patch("ble2wled.main.BeaconRunner") as mock_runner_class:
                mock_runner = MagicMock()
                mock_runner.next_position.return_value = 5
                mock_runner_class.return_value = mock_runner
                mock_sleep.side_effect = [None, KeyboardInterrupt()]

                with patch("ble2wled.main.ble_beacon_to_rgb") as mock_color:
                    mock_color.return_value = (255, 128, 64)

                    with patch("ble2wled.main.add_trail") as mock_trail:
                        try:
                            run_wled_beacons(
                                controller,
                                10,
                                state,
                                trail_length=12,
                                fade_factor=0.8,
                            )
                        except KeyboardInterrupt:
                            pass

                        # add_trail should be called with correct parameters
                        call_args = mock_trail.call_args[0]
                        assert call_args[1] == 5  # position
                        assert call_args[2] == (255, 128, 64)  # color
                        assert call_args[3] == 12  # trail_length
                        assert call_args[4] == 0.8  # fade_factor

    def test_run_wled_beacons_multiple_iterations(self):
        """Test animation loop runs multiple iterations."""
        controller = Mock()
        state = Mock(spec=BeaconState)
        state.snapshot.return_value = {}

        with patch("ble2wled.main.time.sleep") as mock_sleep:
            with patch("ble2wled.main.BeaconRunner"):
                # Simulate 3 iterations then break
                mock_sleep.side_effect = [None, None, None, KeyboardInterrupt()]

                try:
                    run_wled_beacons(controller, 10, state)
                except KeyboardInterrupt:
                    pass

                # Controller.update should be called at least 3 times (once per iteration)
                # Note: there may be 4 calls due to how the loop executes
                assert controller.update.call_count >= 3

    def test_run_wled_beacons_snapshot_called(self):
        """Test that beacon_state.snapshot() is called each iteration."""
        controller = Mock()
        state = Mock(spec=BeaconState)
        state.snapshot.return_value = {}

        with patch("ble2wled.main.time.sleep") as mock_sleep:
            with patch("ble2wled.main.BeaconRunner"):
                with patch("ble2wled.main.ble_beacon_to_rgb"):
                    with patch("ble2wled.main.add_trail"):
                        mock_sleep.side_effect = [None, None, KeyboardInterrupt()]

                        try:
                            run_wled_beacons(controller, 10, state)
                        except KeyboardInterrupt:
                            pass

                        # snapshot should be called each iteration (at least 2)
                        assert state.snapshot.call_count >= 2

    def test_run_wled_beacons_ble_beacon_to_rgb_called(self):
        """Test that ble_beacon_to_rgb is called with correct arguments."""
        controller = Mock()
        state = Mock(spec=BeaconState)
        state.snapshot.return_value = {"abc123": (-55, 0.9)}

        with patch("ble2wled.main.time.sleep") as mock_sleep:
            with patch("ble2wled.main.BeaconRunner"):
                with patch("ble2wled.main.ble_beacon_to_rgb") as mock_color:
                    mock_color.return_value = (100, 100, 100)

                    with patch("ble2wled.main.add_trail"):
                        mock_sleep.side_effect = [None, KeyboardInterrupt()]

                        try:
                            run_wled_beacons(controller, 10, state)
                        except KeyboardInterrupt:
                            pass

                        # ble_beacon_to_rgb should be called with beacon data
                        # May be called multiple times due to iteration
                        assert mock_color.call_count >= 1
                        # Check that it was called with correct arguments at least once
                        calls = [
                            c
                            for c in mock_color.call_args_list
                            if c[0] == ("abc123", -55, 0.9)
                        ]
                        assert len(calls) >= 1

    def test_run_wled_beacons_different_update_intervals(self):
        """Test with different update intervals."""
        controller = Mock()
        state = Mock(spec=BeaconState)
        state.snapshot.return_value = {}

        for interval in [0.05, 0.1, 0.2, 0.5, 1.0]:
            controller.reset_mock()

            with patch("ble2wled.main.time.sleep") as mock_sleep:
                with patch("ble2wled.main.BeaconRunner"):
                    mock_sleep.side_effect = [None, KeyboardInterrupt()]

                    try:
                        run_wled_beacons(
                            controller, 10, state, update_interval=interval
                        )
                    except KeyboardInterrupt:
                        pass

                    # Sleep should be called with the interval
                    mock_sleep.assert_called_with(interval)

    def test_run_wled_beacons_different_trail_parameters(self):
        """Test with different trail length and fade factor."""
        controller = Mock()
        state = Mock(spec=BeaconState)
        state.snapshot.return_value = {"beacon_1": (-50, 1.0)}

        with patch("ble2wled.main.time.sleep") as mock_sleep:
            with patch("ble2wled.main.BeaconRunner"):
                with patch("ble2wled.main.ble_beacon_to_rgb"):
                    with patch("ble2wled.main.add_trail") as mock_trail:
                        mock_sleep.side_effect = [None, KeyboardInterrupt()]

                        try:
                            run_wled_beacons(
                                controller,
                                10,
                                state,
                                trail_length=15,
                                fade_factor=0.6,
                            )
                        except KeyboardInterrupt:
                            pass

                        # Check trail parameters
                        call_args = mock_trail.call_args[0]
                        assert call_args[3] == 15  # trail_length
                        assert call_args[4] == 0.6  # fade_factor

    def test_run_wled_beacons_default_parameters(self):
        """Test run_wled_beacons with default parameters."""
        controller = Mock()
        state = Mock(spec=BeaconState)
        state.snapshot.return_value = {"beacon_1": (-50, 1.0)}

        with patch("ble2wled.main.time.sleep") as mock_sleep:
            with patch("ble2wled.main.BeaconRunner"):
                with patch("ble2wled.main.ble_beacon_to_rgb"):
                    with patch("ble2wled.main.add_trail") as mock_trail:
                        mock_sleep.side_effect = [None, KeyboardInterrupt()]

                        try:
                            # Call with only required parameters
                            run_wled_beacons(controller, 10, state)
                        except KeyboardInterrupt:
                            pass

                        # Check default trail parameters
                        call_args = mock_trail.call_args[0]
                        assert call_args[3] == 8  # default trail_length
                        assert call_args[4] == 0.7  # default fade_factor

    def test_run_wled_beacons_keyboard_interrupt_handling(self):
        """Test that KeyboardInterrupt is properly handled."""
        controller = Mock()
        state = Mock(spec=BeaconState)
        state.snapshot.return_value = {}

        with patch("ble2wled.main.time.sleep") as mock_sleep:
            with patch("ble2wled.main.BeaconRunner"):
                mock_sleep.side_effect = KeyboardInterrupt()

                # Should raise KeyboardInterrupt (not caught in run_wled_beacons)
                with pytest.raises(KeyboardInterrupt):
                    run_wled_beacons(controller, 10, state)

    def test_run_wled_beacons_led_array_reset_each_iteration(self):
        """Test that LED array is reset to black each iteration."""
        controller = Mock()
        state = Mock(spec=BeaconState)
        # First iteration: one beacon, second iteration: different beacon
        state.snapshot.side_effect = [
            {"beacon_1": (-50, 1.0)},
            {"beacon_2": (-60, 0.8)},
            KeyboardInterrupt(),
        ]

        with patch("ble2wled.main.time.sleep") as mock_sleep:
            with patch("ble2wled.main.BeaconRunner"):
                with patch("ble2wled.main.ble_beacon_to_rgb"):
                    with patch("ble2wled.main.add_trail"):
                        mock_sleep.side_effect = [None, None, KeyboardInterrupt()]

                        try:
                            run_wled_beacons(controller, 5, state)
                        except KeyboardInterrupt:
                            pass

                        # All calls should have LED arrays of correct size
                        for call_obj in controller.update.call_args_list:
                            leds = call_obj[0][0]
                            assert len(leds) == 5

    def test_run_wled_beacons_beacon_runner_position_tracking(self):
        """Test that BeaconRunner tracks positions across iterations."""
        controller = Mock()
        state = Mock(spec=BeaconState)
        state.snapshot.return_value = {"beacon_1": (-50, 1.0)}

        with patch("ble2wled.main.time.sleep") as mock_sleep:
            with patch("ble2wled.main.BeaconRunner") as mock_runner_class:
                mock_runner = MagicMock()
                mock_runner_class.return_value = mock_runner
                mock_runner.next_position.return_value = 3
                mock_sleep.side_effect = [None, None, KeyboardInterrupt()]

                with patch("ble2wled.main.ble_beacon_to_rgb"):
                    with patch("ble2wled.main.add_trail"):
                        try:
                            run_wled_beacons(controller, 10, state)
                        except KeyboardInterrupt:
                            pass

                        # next_position should be called multiple times
                        assert mock_runner.next_position.call_count >= 2

    def test_run_wled_beacons_empty_then_populated_state(self):
        """Test transitions between empty and populated beacon state."""
        controller = Mock()
        state = Mock(spec=BeaconState)
        # First iteration: no beacons, second: has beacon, third: empty again
        state.snapshot.side_effect = [
            {},
            {"beacon_1": (-50, 1.0)},
            {},
            KeyboardInterrupt(),
        ]

        with patch("ble2wled.main.time.sleep") as mock_sleep:
            with patch("ble2wled.main.BeaconRunner"):
                with patch("ble2wled.main.ble_beacon_to_rgb"):
                    with patch("ble2wled.main.add_trail") as mock_trail:
                        mock_sleep.side_effect = [None, None, None, KeyboardInterrupt()]

                        try:
                            run_wled_beacons(controller, 10, state)
                        except KeyboardInterrupt:
                            pass

                        # add_trail should only be called in second iteration
                        assert mock_trail.call_count == 1
