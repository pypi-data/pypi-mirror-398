"""Tests for LED simulator and mock beacon generator."""

import pytest

from ble2wled.simulator import LEDSimulator, MockBeaconGenerator


class TestLEDSimulator:
    """Test cases for LEDSimulator class."""

    def test_init_valid(self):
        """Test simulator initialization with valid parameters."""
        sim = LEDSimulator(led_count=60, rows=10, cols=6)
        assert sim.led_count == 60
        assert sim.rows == 10
        assert sim.cols == 6
        assert len(sim.current_leds) == 60
        assert all(led == [0, 0, 0] for led in sim.current_leds)

    def test_init_mismatched_dimensions(self):
        """Test initialization with mismatched rows/cols."""
        with pytest.raises(ValueError):
            LEDSimulator(led_count=60, rows=10, cols=5)

    def test_update_basic(self):
        """Test basic LED update."""
        sim = LEDSimulator(led_count=4, rows=2, cols=2)
        leds = [[255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0]]
        sim.update(leds)

        snapshot = sim.get_snapshot()
        assert snapshot == leds

    def test_update_copies_data(self):
        """Test that update creates copies, not references."""
        sim = LEDSimulator(led_count=2, rows=1, cols=2)
        leds = [[255, 0, 0], [0, 255, 0]]
        sim.update(leds)

        # Modify original list
        leds[0] = [0, 0, 0]

        # Simulator should have unchanged data
        snapshot = sim.get_snapshot()
        assert snapshot[0] == [255, 0, 0]

    def test_get_snapshot_returns_copy(self):
        """Test that get_snapshot returns copy, not reference."""
        sim = LEDSimulator(led_count=2, rows=1, cols=2)
        leds = [[255, 0, 0], [0, 255, 0]]
        sim.update(leds)

        snapshot = sim.get_snapshot()
        snapshot[0] = [0, 0, 0]

        # Original should be unchanged
        new_snapshot = sim.get_snapshot()
        assert new_snapshot[0] == [255, 0, 0]

    def test_different_grid_sizes(self):
        """Test various valid grid configurations."""
        configs = [
            (30, 6, 5),
            (100, 10, 10),
            (120, 12, 10),
            (20, 4, 5),
        ]

        for led_count, rows, cols in configs:
            sim = LEDSimulator(led_count=led_count, rows=rows, cols=cols)
            assert sim.led_count == led_count
            assert len(sim.current_leds) == led_count

    def test_update_with_gradients(self):
        """Test updating with gradient values."""
        sim = LEDSimulator(led_count=10, rows=2, cols=5)
        leds = [[i * 25, 0, 0] for i in range(10)]
        sim.update(leds)

        snapshot = sim.get_snapshot()
        for i, led in enumerate(snapshot):
            assert led[0] == i * 25
            assert led[1] == 0
            assert led[2] == 0

    def test_rgb_bounds(self):
        """Test LED values within RGB bounds."""
        sim = LEDSimulator(led_count=3, rows=1, cols=3)
        leds = [[0, 0, 0], [255, 255, 255], [128, 200, 64]]
        sim.update(leds)

        snapshot = sim.get_snapshot()
        assert snapshot == leds


class TestMockBeaconGenerator:
    """Test cases for MockBeaconGenerator class."""

    def test_init_default(self):
        """Test generator initialization with defaults."""
        gen = MockBeaconGenerator()
        assert gen.num_beacons == 3
        assert len(gen.beacon_ids) == 3
        assert gen.rssi_range == (-90, -30)

    def test_init_custom(self):
        """Test generator with custom parameters."""
        gen = MockBeaconGenerator(num_beacons=5, rssi_range=(-100, -20))
        assert gen.num_beacons == 5
        assert len(gen.beacon_ids) == 5
        assert gen.rssi_range == (-100, -20)

    def test_beacon_ids_format(self):
        """Test beacon ID naming."""
        gen = MockBeaconGenerator(num_beacons=3)
        expected_ids = ["beacon_0", "beacon_1", "beacon_2"]
        assert gen.beacon_ids == expected_ids

    def test_update_returns_dict(self):
        """Test that update returns proper dictionary."""
        gen = MockBeaconGenerator(num_beacons=3)
        beacons = gen.update()

        assert isinstance(beacons, dict)
        assert len(beacons) == 3
        assert all(bid in beacons for bid in gen.beacon_ids)

    def test_rssi_within_range(self):
        """Test RSSI values stay within specified range."""
        rssi_min, rssi_max = -95, -25
        gen = MockBeaconGenerator(num_beacons=5, rssi_range=(rssi_min, rssi_max))

        for _ in range(100):
            beacons = gen.update()
            for rssi in beacons.values():
                # Allow small overshoot due to noise
                assert rssi_min - 10 <= rssi <= rssi_max + 10

    def test_rssi_values_are_integers(self):
        """Test RSSI values are integers."""
        gen = MockBeaconGenerator(num_beacons=3)
        beacons = gen.update()

        for rssi in beacons.values():
            assert isinstance(rssi, int)

    def test_beacon_movement_over_time(self):
        """Test beacons change position over time."""
        gen = MockBeaconGenerator(num_beacons=3)

        # Get initial readings
        beacons1 = gen.update(time_delta=0.1)
        values1 = list(beacons1.values())

        # Get readings after time step
        beacons2 = gen.update(time_delta=0.1)
        values2 = list(beacons2.values())

        # Values should be different (beacons moving)
        assert values1 != values2

    def test_multiple_updates(self):
        """Test multiple sequential updates."""
        gen = MockBeaconGenerator(num_beacons=2)
        previous_beacons = None
        changed = False

        for _ in range(20):
            beacons = gen.update(time_delta=0.05)
            assert len(beacons) == 2
            if previous_beacons and beacons != previous_beacons:
                changed = True
                break
            previous_beacons = beacons

        # Over 20 updates, values should change at least once
        assert changed, "Beacon values did not change over multiple updates"

    def test_different_time_deltas(self):
        """Test that different time deltas affect beacon movement."""
        gen1 = MockBeaconGenerator(num_beacons=1)
        gen2 = MockBeaconGenerator(num_beacons=1)

        # Update gen1 with small time delta
        b1 = gen1.update(time_delta=0.01)

        # Update gen2 with large time delta
        b2 = gen2.update(time_delta=1.0)

        # Beacons should have different RSSI values due to different motion
        assert b1 != b2

    def test_deterministic_behavior(self):
        """Test that same initial state produces predictable output."""
        gen1 = MockBeaconGenerator(num_beacons=2)
        gen2 = MockBeaconGenerator(num_beacons=2)

        # Both should produce same sequence for same updates
        for _ in range(5):
            b1 = gen1.update(time_delta=0.1)
            b2 = gen2.update(time_delta=0.1)
            assert b1 == b2

    def test_single_beacon(self):
        """Test with single beacon."""
        gen = MockBeaconGenerator(num_beacons=1)
        beacons = gen.update()

        assert len(beacons) == 1
        assert "beacon_0" in beacons

    def test_many_beacons(self):
        """Test with many beacons."""
        gen = MockBeaconGenerator(num_beacons=100)
        beacons = gen.update()

        assert len(beacons) == 100
        assert all(f"beacon_{i}" in beacons for i in range(100))
