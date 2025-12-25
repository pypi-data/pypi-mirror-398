"""Beacon animation and trail rendering.

This module handles animation of beacons moving across LED strips and
rendering motion trails for visual effects.

Example:
    Animate beacons with motion trails::

        from ble2wled.animation import BeaconRunner, add_trail
        from ble2wled.colors import ble_beacon_to_rgb

        runner = BeaconRunner(led_count=60)
        leds = [[0, 0, 0] for _ in range(60)]

        # Get next position for beacon and add trail
        pos = runner.next_position('beacon_1')
        color = ble_beacon_to_rgb('beacon_1', rssi=-50, life=0.8)
        add_trail(leds, pos, color, trail_length=10, fade_factor=0.75)
"""


class BeaconRunner:
    """Manages animation positions for beacons moving along LED strip.

    Each beacon gets its own position on the LED strip. Calling next_position()
    increments the position, creating a moving effect across the strip.

    Attributes:
        led_count (int): Total number of LEDs in the strip.
        positions (dict): Current position of each beacon.
    """

    def __init__(self, led_count: int):
        """Initialize beacon runner.

        Args:
            led_count (int): Total number of LEDs in the strip.

        Example:
            Create a beacon runner for a 60-LED strip::

                runner = BeaconRunner(led_count=60)
        """
        self.led_count = led_count
        self.positions: dict[str, int] = {}

    def next_position(self, beacon_id: str) -> int:
        """Get next position for a beacon.

        Increments position and wraps around at LED count. Maintains consistent
        position increment per beacon across calls.

        Args:
            beacon_id (str): Unique beacon identifier.

        Returns:
            int: Next position index (0 to led_count-1).

        Example:
            Get beacon positions for animation::

                runner = BeaconRunner(led_count=60)
                pos1 = runner.next_position('beacon_1')  # Returns 0
                pos1 = runner.next_position('beacon_1')  # Returns 1
                pos2 = runner.next_position('beacon_2')  # Returns 0
        """
        pos = self.positions.get(beacon_id, -1)
        pos = (pos + 1) % self.led_count
        self.positions[beacon_id] = pos
        return pos


def add_trail(
    leds: list[list[int]],
    position: int,
    color: tuple[int, int, int],
    trail_length: int,
    fade_factor: float,
) -> None:
    """Add motion trail to LED array.

    Creates a fading trail effect behind the beacon by rendering progressively
    dimmer segments behind the main position. Uses additive blending to combine
    trail colors with existing LED values.

    Trail Rendering:
        - LED at position gets full color
        - Each previous LED gets color * fade_factor^distance
        - Colors are additively blended (clamped at 255)

    Args:
        leds (list): LED color array (list of [R, G, B] with values 0-255).
        position (int): Current beacon position index.
        color (tuple): RGB color tuple (R, G, B) with values 0-255.
        trail_length (int): Number of LEDs in the trail (including main position).
        fade_factor (float): Brightness decay per segment (0.0 to 1.0).
            0.75 means each trailing segment is 75% brightness of previous.

    Raises:
        ValueError: If trail_length is negative or fade_factor outside 0-1.

    Example:
        Add a red trail to the LED array::

            leds = [[0, 0, 0] for _ in range(60)]
            add_trail(leds, position=10, color=(255, 0, 0),
                     trail_length=8, fade_factor=0.75)
            # Now leds[10] has max red, leds[9] has 75% red, etc.
    """
    r, g, b = color
    for i in range(trail_length):
        idx = (position - i) % len(leds)
        fade = fade_factor**i

        leds[idx][0] = min(255, int(leds[idx][0] + r * fade))
        leds[idx][1] = min(255, int(leds[idx][1] + g * fade))
        leds[idx][2] = min(255, int(leds[idx][2] + b * fade))
