"""Tests for BeaconRunner class."""

from ble2wled.animation import BeaconRunner


class TestBeaconRunner:
    """Test cases for BeaconRunner."""

    def test_init(self):
        """Test BeaconRunner initialization."""
        runner = BeaconRunner(led_count=60)
        assert runner.led_count == 60

    def test_next_position_single_beacon(self):
        """Test position increments for a single beacon."""
        runner = BeaconRunner(led_count=10)

        for expected in range(10):
            pos = runner.next_position("beacon_1")
            assert pos == expected

        # Should wrap around
        pos = runner.next_position("beacon_1")
        assert pos == 0

    def test_multiple_beacons_independent(self):
        """Test that multiple beacons have independent positions."""
        runner = BeaconRunner(led_count=10)

        pos1 = runner.next_position("beacon_1")
        pos2 = runner.next_position("beacon_2")

        assert pos1 == 0
        assert pos2 == 0

        pos1 = runner.next_position("beacon_1")
        pos2 = runner.next_position("beacon_2")

        assert pos1 == 1
        assert pos2 == 1

    def test_wrapping(self):
        """Test position wrapping at LED count."""
        runner = BeaconRunner(led_count=3)

        positions = [runner.next_position("b") for _ in range(6)]
        assert positions == [0, 1, 2, 0, 1, 2]
