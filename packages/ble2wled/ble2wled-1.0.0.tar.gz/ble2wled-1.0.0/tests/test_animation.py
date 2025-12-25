"""Comprehensive tests for animation module functions.

Tests for BeaconRunner and add_trail function covering:
- Beacon position management
- Motion trail rendering
- Color blending and fade calculations
- Edge cases and boundary conditions
"""

from ble2wled.animation import BeaconRunner, add_trail


class TestBeaconRunnerComprehensive:
    """Comprehensive tests for BeaconRunner class."""

    def test_init_stores_led_count(self):
        """Test that initialization stores led_count."""
        for count in [1, 10, 60, 256, 1000]:
            runner = BeaconRunner(led_count=count)
            assert runner.led_count == count

    def test_init_creates_empty_positions_dict(self):
        """Test that positions dictionary is initialized empty."""
        runner = BeaconRunner(led_count=60)
        assert runner.positions == {}

    def test_next_position_returns_integer(self):
        """Test that next_position returns integer values."""
        runner = BeaconRunner(led_count=10)
        pos = runner.next_position("beacon_1")
        assert isinstance(pos, int)

    def test_next_position_sequence(self):
        """Test that positions increment sequentially."""
        runner = BeaconRunner(led_count=5)
        expected_sequence = [0, 1, 2, 3, 4, 0, 1, 2]

        actual_sequence = [runner.next_position("b") for _ in range(8)]
        assert actual_sequence == expected_sequence

    def test_next_position_wraps_at_led_count(self):
        """Test wrapping at exact LED count."""
        runner = BeaconRunner(led_count=7)
        # Advance to position 6 (last position)
        for _ in range(7):
            pos = runner.next_position("b")
        assert pos == 6
        # Next should wrap to 0
        pos = runner.next_position("b")
        assert pos == 0

    def test_next_position_multiple_beacons_independent(self):
        """Test that different beacons have independent positions."""
        runner = BeaconRunner(led_count=10)

        # Advance beacon_1 several times
        for _ in range(5):
            runner.next_position("beacon_1")

        # beacon_2 should start fresh
        pos = runner.next_position("beacon_2")
        assert pos == 0

        # beacon_1 should continue from where it was
        pos = runner.next_position("beacon_1")
        assert pos == 5

    def test_next_position_many_beacons(self):
        """Test handling of many concurrent beacons."""
        runner = BeaconRunner(led_count=10)
        beacon_ids = [f"beacon_{i}" for i in range(20)]

        # Each beacon should start at 0
        positions = [runner.next_position(bid) for bid in beacon_ids]
        assert all(p == 0 for p in positions)

        # Each beacon should advance independently
        positions = [runner.next_position(bid) for bid in beacon_ids]
        assert all(p == 1 for p in positions)

    def test_next_position_with_single_led(self):
        """Test with LED count of 1 (always position 0)."""
        runner = BeaconRunner(led_count=1)

        positions = [runner.next_position("b") for _ in range(10)]
        assert all(p == 0 for p in positions)

    def test_next_position_stores_in_positions_dict(self):
        """Test that positions are stored in positions dictionary."""
        runner = BeaconRunner(led_count=10)

        runner.next_position("beacon_1")
        assert "beacon_1" in runner.positions
        assert runner.positions["beacon_1"] == 0

        runner.next_position("beacon_1")
        assert runner.positions["beacon_1"] == 1


class TestAddTrail:
    """Comprehensive tests for add_trail function."""

    def test_add_trail_basic_operation(self):
        """Test basic trail addition."""
        leds = [[0, 0, 0] for _ in range(10)]
        color = (255, 0, 0)  # Red

        add_trail(leds, position=5, color=color, trail_length=1, fade_factor=0.75)

        # Only position 5 should be lit
        assert leds[5] == [255, 0, 0]
        assert leds[4] == [0, 0, 0]
        assert leds[6] == [0, 0, 0]

    def test_add_trail_with_multiple_segments(self):
        """Test trail with multiple segments."""
        leds = [[0, 0, 0] for _ in range(10)]
        color = (100, 0, 0)  # Red

        add_trail(leds, position=5, color=color, trail_length=3, fade_factor=0.5)

        # Position 5: full color (100)
        assert leds[5][0] == 100
        # Position 4: 50% (100 * 0.5)
        assert leds[4][0] == 50
        # Position 3: 25% (100 * 0.5^2)
        assert leds[3][0] == 25

    def test_add_trail_wraps_around(self):
        """Test that trail wraps around LED array."""
        leds = [[0, 0, 0] for _ in range(10)]
        color = (100, 0, 0)

        # Position 0 with trail extending backwards should wrap
        add_trail(leds, position=0, color=color, trail_length=3, fade_factor=0.5)

        assert leds[0][0] == 100  # Current position
        assert leds[9][0] == 50  # Wrapped position -1
        assert leds[8][0] == 25  # Wrapped position -2

    def test_add_trail_green_color(self):
        """Test trail with green color."""
        leds = [[0, 0, 0] for _ in range(10)]
        color = (0, 200, 0)  # Green

        add_trail(leds, position=5, color=color, trail_length=2, fade_factor=0.75)

        assert leds[5] == [0, 200, 0]
        assert leds[4][1] == 150  # 200 * 0.75

    def test_add_trail_blue_color(self):
        """Test trail with blue color."""
        leds = [[0, 0, 0] for _ in range(10)]
        color = (0, 0, 150)  # Blue

        add_trail(leds, position=3, color=color, trail_length=2, fade_factor=0.6)

        assert leds[3] == [0, 0, 150]
        assert leds[2][2] == 90  # 150 * 0.6

    def test_add_trail_white_color(self):
        """Test trail with white color."""
        leds = [[0, 0, 0] for _ in range(10)]
        color = (255, 255, 255)  # White

        add_trail(leds, position=5, color=color, trail_length=2, fade_factor=0.5)

        assert leds[5] == [255, 255, 255]
        assert leds[4] == [127, 127, 127]  # 255 * 0.5 ≈ 127

    def test_add_trail_additively_blends(self):
        """Test that colors blend additively."""
        leds = [[100, 100, 100] for _ in range(10)]
        color = (100, 0, 0)  # Red

        add_trail(leds, position=5, color=color, trail_length=1, fade_factor=0.75)

        # Should add: 100 (existing) + 100 (new) = 200
        assert leds[5] == [200, 100, 100]

    def test_add_trail_clamps_at_255(self):
        """Test that values are clamped at 255."""
        leds = [[200, 200, 200] for _ in range(10)]
        color = (100, 100, 100)

        add_trail(leds, position=5, color=color, trail_length=2, fade_factor=1.0)

        # 200 + 100 = 300, should be clamped to 255
        assert leds[5] == [255, 255, 255]
        # 200 + 100 = 300, should be clamped to 255
        assert leds[4] == [255, 255, 255]

    def test_add_trail_zero_fade_factor(self):
        """Test with fade factor of 0 (trail disappears immediately)."""
        leds = [[0, 0, 0] for _ in range(10)]
        color = (100, 0, 0)

        add_trail(leds, position=5, color=color, trail_length=3, fade_factor=0.0)

        assert leds[5] == [100, 0, 0]  # Current position has full brightness
        assert leds[4] == [0, 0, 0]  # Fade: 100 * 0^1 = 0
        assert leds[3] == [0, 0, 0]  # Fade: 100 * 0^2 = 0

    def test_add_trail_unit_fade_factor(self):
        """Test with fade factor of 1.0 (no fading)."""
        leds = [[0, 0, 0] for _ in range(10)]
        color = (50, 0, 0)

        add_trail(leds, position=5, color=color, trail_length=3, fade_factor=1.0)

        # All trail positions should have same brightness
        assert leds[5] == [50, 0, 0]  # 50 * 1^0
        assert leds[4] == [50, 0, 0]  # 50 * 1^1
        assert leds[3] == [50, 0, 0]  # 50 * 1^2

    def test_add_trail_long_trail(self):
        """Test with trail longer than LED array."""
        leds = [[0, 0, 0] for _ in range(5)]
        color = (100, 0, 0)

        # Trail length longer than LED count - will wrap and overlap
        add_trail(leds, position=2, color=color, trail_length=10, fade_factor=0.5)

        # Position 2: 100 * 0.5^0 + 100 * 0.5^5 (wraps around) = 103
        assert leds[2][0] == 103
        # Position 1: 100 * 0.5^1 + 100 * 0.5^6 = 51
        assert leds[1][0] == 51
        # Position 0: 100 * 0.5^2 = 25
        assert leds[0][0] == 25
        # Positions wrap and accumulate
        assert leds[4][0] > 0

    def test_add_trail_trail_length_one(self):
        """Test with trail length of 1 (just the point)."""
        leds = [[0, 0, 0] for _ in range(10)]
        color = (200, 100, 50)

        add_trail(leds, position=3, color=color, trail_length=1, fade_factor=0.75)

        assert leds[3] == [200, 100, 50]
        assert leds[2] == [0, 0, 0]

    def test_add_trail_different_positions(self):
        """Test trail at different positions."""
        for position in [0, 1, 5, 9]:
            leds = [[0, 0, 0] for _ in range(10)]
            color = (100, 0, 0)

            add_trail(
                leds, position=position, color=color, trail_length=2, fade_factor=0.5
            )

            assert leds[position][0] == 100

    def test_add_trail_multiple_applications(self):
        """Test applying multiple trails to same array."""
        leds = [[0, 0, 0] for _ in range(10)]

        # Add red trail
        add_trail(leds, position=3, color=(255, 0, 0), trail_length=2, fade_factor=0.5)

        # Add blue trail at different position
        add_trail(leds, position=6, color=(0, 0, 255), trail_length=2, fade_factor=0.5)

        # Both trails should be visible
        assert leds[3][0] == 255  # Red
        assert leds[6][2] == 255  # Blue
        assert leds[2][0] == 127  # Red trail, faded

    def test_add_trail_overlapping_trails(self):
        """Test overlapping trails blend correctly."""
        leds = [[0, 0, 0] for _ in range(10)]

        # Add red trail at position 5
        add_trail(leds, position=5, color=(100, 0, 0), trail_length=3, fade_factor=0.5)

        # Add blue trail at position 4 (overlaps)
        add_trail(leds, position=4, color=(0, 100, 0), trail_length=3, fade_factor=0.5)

        # Position 4 should have both colors blended
        assert leds[4] == [50, 100, 0]  # Red trail faded + Blue current

    def test_add_trail_preserves_existing_values(self):
        """Test that existing LED values are preserved and blended."""
        leds = [[50, 50, 50] for _ in range(10)]
        color = (50, 50, 50)

        add_trail(leds, position=5, color=color, trail_length=2, fade_factor=1.0)

        # Should add to existing values
        assert leds[5] == [100, 100, 100]
        assert leds[4] == [100, 100, 100]

    def test_add_trail_high_precision_fade(self):
        """Test fade calculation with high precision values."""
        leds = [[0, 0, 0] for _ in range(10)]
        color = (200, 0, 0)
        fade_factor = 0.7

        add_trail(
            leds, position=5, color=color, trail_length=4, fade_factor=fade_factor
        )

        expected = [
            int(200 * (0.7**0)),  # 200
            int(200 * (0.7**1)),  # 140
            int(200 * (0.7**2)),  # 98
            int(200 * (0.7**3)),  # 68
        ]

        assert leds[5][0] == expected[0]
        assert leds[4][0] == expected[1]
        assert leds[3][0] == expected[2]
        assert leds[2][0] == expected[3]

    def test_add_trail_small_led_array(self):
        """Test with minimal LED array."""
        leds = [[0, 0, 0] for _ in range(1)]
        color = (100, 100, 100)

        add_trail(leds, position=0, color=color, trail_length=5, fade_factor=0.5)

        # All trails wrap to position 0
        # Multiple overlapping contributions: 100 + 50 + 25 + 12 + 6 ≈ 193
        assert leds[0][0] > 100  # Should accumulate from multiple trail segments

    def test_add_trail_large_led_array(self):
        """Test with large LED array."""
        leds = [[0, 0, 0] for _ in range(1000)]
        color = (100, 0, 0)

        add_trail(leds, position=500, color=color, trail_length=10, fade_factor=0.5)

        assert leds[500][0] == 100
        assert leds[499][0] == 50
        # Check that fade extends several positions
        assert leds[495][0] > 0  # Still has some brightness after ~5 fades

    def test_add_trail_dim_color(self):
        """Test with very dim color values."""
        leds = [[0, 0, 0] for _ in range(10)]
        color = (1, 0, 0)  # Very dim red

        add_trail(leds, position=5, color=color, trail_length=3, fade_factor=0.5)

        assert leds[5][0] == 1
        assert leds[4][0] == 0  # 1 * 0.5 = 0.5, truncated to 0

    def test_add_trail_max_color(self):
        """Test with maximum color values."""
        leds = [[0, 0, 0] for _ in range(10)]
        color = (255, 255, 255)

        add_trail(leds, position=5, color=color, trail_length=2, fade_factor=0.75)

        assert leds[5] == [255, 255, 255]
        assert leds[4][0] == 191  # 255 * 0.75 ≈ 191

    def test_add_trail_float_fade_calculation(self):
        """Test that float fade calculations work correctly."""
        leds = [[0, 0, 0] for _ in range(10)]
        color = (100, 0, 0)
        fade_factor = 0.33  # Float value

        add_trail(
            leds, position=5, color=color, trail_length=3, fade_factor=fade_factor
        )

        # Should handle float multiplication and int conversion
        assert leds[5][0] == 100
        assert leds[4][0] == int(100 * 0.33)
        assert leds[3][0] == int(100 * (0.33**2))


class TestAnimationIntegration:
    """Integration tests for BeaconRunner and add_trail."""

    def test_beacon_runner_with_add_trail(self):
        """Test BeaconRunner positions with add_trail rendering."""
        runner = BeaconRunner(led_count=10)
        leds = [[0, 0, 0] for _ in range(10)]

        # Get position and render trail
        pos = runner.next_position("beacon_1")
        add_trail(leds, pos, (100, 0, 0), trail_length=3, fade_factor=0.5)

        assert leds[0][0] == 100  # Position 0 has beacon

    def test_multiple_beacons_rendering(self):
        """Test rendering multiple beacons with different colors."""
        runner = BeaconRunner(led_count=20)
        leds = [[0, 0, 0] for _ in range(20)]

        # All beacons start at position 0, then advance
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        positions = []
        for i, color in enumerate(colors):
            pos = runner.next_position(f"beacon_{i}")
            positions.append(pos)
            add_trail(leds, pos, color, trail_length=1, fade_factor=0.5)

        # All beacons should be at position 0 on first call
        assert all(p == 0 for p in positions)

        # Position 0 should have additive blend of all colors
        assert leds[0][0] > 0  # Has red
        assert leds[0][1] > 0  # Has green
        assert leds[0][2] > 0  # Has blue

    def test_animated_beacon_sequence(self):
        """Test beacon movement over multiple frames."""
        runner = BeaconRunner(led_count=5)

        positions = []
        for _ in range(10):
            pos = runner.next_position("moving_beacon")
            positions.append(pos)

        # Should see pattern: 0,1,2,3,4,0,1,2,3,4
        assert positions == [0, 1, 2, 3, 4, 0, 1, 2, 3, 4]
