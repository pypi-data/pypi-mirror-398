"""Tests for color and distance conversion functions."""

from ble2wled.colors import (
    ble_beacon_to_rgb,
    estimate_distance_from_rssi,
    gradient_color,
)


class TestDistanceEstimation:
    """Test cases for RSSI to distance estimation."""

    def test_estimate_distance_reference(self):
        """Test distance estimation with reference values."""
        # At tx_power, distance should be approximately 1 meter
        distance = estimate_distance_from_rssi(-59, tx_power=-59, n=2.0)
        assert 0.9 < distance < 1.1

    def test_estimate_distance_farther(self):
        """Test that lower RSSI results in greater distance."""
        near = estimate_distance_from_rssi(-50, tx_power=-59, n=2.0)
        far = estimate_distance_from_rssi(-70, tx_power=-59, n=2.0)
        assert far > near


class TestGradientColor:
    """Test cases for gradient color function."""

    def test_near_distance_yellow(self):
        """Test color at near distance (yellow range)."""
        r, g, b = gradient_color(0.6)
        # At near distance, should be in yellow (R and G, no B)
        assert r <= 1.0 and r >= 0.0
        assert g == 1.0
        assert b == 0.0

    def test_far_distance_red(self):
        """Test color at far distance (red range)."""
        r, g, b = gradient_color(10.0)
        # At far distance, should be red
        assert r == 1.0
        assert g < 1.0
        assert b == 0.0

    def test_mid_distance(self):
        """Test color at middle distance."""
        r, g, b = gradient_color(5.0)
        # At middle, should transition to more red
        assert 0.0 <= r <= 1.0
        assert 0.0 <= g <= 1.0
        assert b == 0.0


class TestBeaconToRGB:
    """Test cases for beacon to RGB conversion."""

    def test_rgb_in_valid_range(self):
        """Test that RGB values are in valid range."""
        r, g, b = ble_beacon_to_rgb("beacon_1", -50, 1.0)
        assert 0 <= r <= 255
        assert 0 <= g <= 255
        assert 0 <= b <= 255

    def test_life_affects_brightness(self):
        """Test that life parameter affects brightness."""
        r1, g1, b1 = ble_beacon_to_rgb("beacon_1", -50, 1.0)
        r2, g2, b2 = ble_beacon_to_rgb("beacon_1", -50, 0.5)

        # Lower life should result in lower brightness
        assert (r2 + g2 + b2) <= (r1 + g1 + b1)

    def test_different_beacons_different_hue(self):
        """Test that different beacon IDs result in different hues."""
        r1, g1, b1 = ble_beacon_to_rgb("beacon_1", -50, 1.0)
        r2, g2, b2 = ble_beacon_to_rgb("beacon_2", -50, 1.0)

        # Different beacons should have different colors (not all equal)
        assert (r1, g1, b1) != (r2, g2, b2)
