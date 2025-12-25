"""Color conversion and distance estimation from RSSI.

This module provides functions for converting BLE beacon signal strength (RSSI)
to distance estimates, mapping distance to colors on a gradient, and generating
beacon-specific colors with life-based brightness modulation.

The distance estimation uses the Friis path loss model::

    distance = 10^((TX_POWER - RSSI) / (10 * N))

Color Mapping:
    - Beacons near (< 0.5m): Yellow (255, 255, 0)
    - Beacons far (> 10m): Red (255, 0, 0)
    - Linear gradient between near and far distances

Example:
    Convert beacon data to RGB color::

        rssi = -50
        distance = estimate_distance_from_rssi(rssi)
        color = ble_beacon_to_rgb('beacon_1', rssi, life=0.8)
        print(f\"Beacon at {distance:.2f}m: RGB{color}\")
"""


def estimate_distance_from_rssi(
    rssi: int, tx_power: int = -59, n: float = 2.0
) -> float:
    """Estimate distance from signal strength using path loss model.

    Uses the Friis free space path loss model to estimate distance from
    RSSI. The accuracy depends on the environment and the TX power of
    the beacon.

    Args:
        rssi (int): Received Signal Strength Indicator in dBm
            (typically -30 to -100).
        tx_power (int): Transmit power in dBm. Typical beacon values are
            -59 dBm at 1 meter. Default: -59.
        n (float): Path loss exponent. 2.0 for free space, up to 4.0 in
            indoor environments. Default: 2.0.

    Returns:
        float: Estimated distance in meters.

    Example:
        Estimate distance from RSSI values::

            distance = estimate_distance_from_rssi(-50)  # ~1 meter
            distance = estimate_distance_from_rssi(-70)  # ~10 meters
    """
    return 10 ** ((tx_power - rssi) / (10 * n))


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between two values.

    Args:
        a (float): Start value.
        b (float): End value.
        t (float): Interpolation factor (0.0 to 1.0).
            0.0 returns a, 1.0 returns b.

    Returns:
        float: Interpolated value between a and b.

    Example:
        Interpolate between colors::

            mid_value = lerp(0, 255, 0.5)  # Returns 127.5
    """
    return a + (b - a) * t


def gradient_color(
    distance: float, near: float = 0.5, far: float = 10.0
) -> tuple[float, float, float]:
    """Map distance to RGB color gradient (yellow to red).

    Maps distance to a color gradient from yellow (near) to red (far).
    Uses linear interpolation in the middle range. Returns values in 0-1 range.

    Color Mapping:
        - distance < near: Yellow (1.0, 1.0, 0.0)
        - distance between near and far: Gradient yellow → red
        - distance > far: Red (1.0, 0.0, 0.0)

    Args:
        distance (float): Distance in meters.
        near (float): Distance threshold for \"near\" color in meters.
            Default: 0.5 meters (yellow).
        far (float): Distance threshold for \"far\" color in meters.
            Default: 10.0 meters (red).

    Returns:
        tuple: RGB tuple with values in range 0.0-1.0.

    Example:
        Get color for different distances::

            close_color = gradient_color(0.3)   # Yellow-ish
            mid_color = gradient_color(5.0)    # Yellow-Red transition
            far_color = gradient_color(15.0)   # Red
    """
    d = max(near, min(far, distance))
    t = (d - near) / (far - near)

    if t < 0.5:
        return lerp(0, 1, t / 0.5), 1.0, 0.0
    else:
        return 1.0, lerp(1, 0, (t - 0.5) / 0.5), 0.0


def ble_beacon_to_rgb(beacon_id: str, rssi: int, life: float) -> tuple[int, int, int]:
    """Convert beacon data to RGB color.

    Applies distance-based gradient coloring with unique hue offset per beacon,
    and modulates brightness based on life value. Each beacon gets a consistent
    hue offset based on its ID hash, ensuring the same beacon is always the
    same base color.

    Algorithm:
        1. Estimate distance from RSSI
        2. Map distance to base color (yellow to red gradient)
        3. Apply unique hue offset per beacon (0-8% range)
        4. Scale brightness by life value (0-1)

    Args:
        beacon_id (str): Unique beacon identifier.
        rssi (int): Signal strength in dBm (typically -30 to -100).
        life (float): Beacon life value (0.0 to 1.0), modulates brightness.
            1.0 = full brightness, 0.0 = invisible.

    Returns:
        tuple: RGB tuple with values 0-255.

    Example:
        Convert beacon to RGB color::

            color = ble_beacon_to_rgb('beacon_1', rssi=-50, life=0.8)
            r, g, b = color
            print(f\"Color: RGB({r}, {g}, {b})\")
    """
    import colorsys
    import hashlib

    distance = estimate_distance_from_rssi(rssi)
    r, g, b = gradient_color(distance)

    # Create unique hue offset for each beacon based on its hash
    beacon_hash = hashlib.sha256(beacon_id.encode()).hexdigest()
    hue_offset = (int(beacon_hash[:6], 16) / 0xFFFFFF) * 0.08

    # Apply hue shift and life-based brightness
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    h = (h + hue_offset) % 1.0
    r, g, b = colorsys.hsv_to_rgb(h, s, v * life)

    return int(r * 255), int(g * 255), int(b * 255)
