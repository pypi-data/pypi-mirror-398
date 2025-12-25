"""LED strip simulator with visual CLI output.

This module provides a simulator for testing beacon visualization without
requiring a real WLED device. The simulator displays the LED strip state
as colored dots in the terminal using ANSI escape codes.

The simulator implements the LEDController interface and can be used as a
drop-in replacement for WLEDHTTPController or WLEDUDPController.

Example:
    Simulate beacon visualization::

        from ble2wled.simulator import LEDSimulator
        from ble2wled import BeaconState, run_wled_beacons

        # Create simulator
        simulator = LEDSimulator(led_count=60, rows=10, cols=6)

        # Create beacon state
        beacon_state = BeaconState()

        # Run animation with simulator (no real WLED needed)
        run_wled_beacons(
            simulator,
            led_count=60,
            beacon_state=beacon_state,
            update_interval=0.05
        )
"""

import threading

from .wled import LEDController


class LEDSimulator(LEDController):
    """LED strip simulator with visual terminal output.

    Displays the LED strip as a grid of colored dots in the terminal using
    ANSI 24-bit color codes. Useful for testing beacon visualization without
    a real WLED device.

    The grid is arranged in rows x cols format. For example, with 60 LEDs in
    a 10x6 grid, LED 0 is top-left, LED 5 is top-right, LED 6 is
    second-row-left, etc.

    Attributes:
        led_count (int): Total number of LEDs.
        rows (int): Number of rows in display grid.
        cols (int): Number of columns in display grid.
        current_leds (List[List[int]]): Current LED RGB values.
        lock (threading.Lock): Thread-safe access to LED data.

    Example:
        Create a 10x6 grid simulator::

            simulator = LEDSimulator(led_count=60, rows=10, cols=6)
            leds = [[255, 0, 0] for _ in range(60)]  # All red
            simulator.update(leds)
    """

    def __init__(self, led_count: int = 60, rows: int = 10, cols: int = 6):
        """Initialize the LED simulator.

        Args:
            led_count (int): Total number of LEDs. Default: 60.
                Must equal rows x cols.
            rows (int): Number of rows in display grid. Default: 10.
            cols (int): Number of columns in display grid. Default: 6.

        Raises:
            ValueError: If rows x cols does not equal led_count.

        Example:
            Create 120-LED simulator (12 rows x 10 cols)::

                simulator = LEDSimulator(led_count=120, rows=12, cols=10)
        """
        super().__init__(host="simulator", led_count=led_count)
        if rows * cols != led_count:
            raise ValueError(
                f"rows ({rows}) x cols ({cols}) = {rows * cols} "
                f"does not equal led_count ({led_count})"
            )

        self.led_count = led_count
        self.rows = rows
        self.cols = cols
        self.current_leds: list[list[int]] = [[0, 0, 0] for _ in range(led_count)]
        self.lock = threading.Lock()
        self._running = False

    def update(self, leds: list[list[int]]) -> None:
        """Update and display the LED strip.

        Updates the current LED state and renders the grid to terminal.
        Uses ANSI 24-bit true color escape codes for each LED.

        Args:
            leds (List[List[int]]): LED data as list of [R, G, B] triplets.
                Expected length: led_count.

        Example:
            Display a gradient::

                import time
                from ble2wled.simulator import LEDSimulator

                simulator = LEDSimulator(led_count=60)
                for i in range(60):
                    leds = [[0, 0, 0] for _ in range(60)]
                    leds[i] = [255, 100, 0]  # Orange
                    simulator.update(leds)
                    time.sleep(0.05)
        """
        with self.lock:
            self.current_leds = [list(led) for led in leds]

        self._render()

    def _render(self) -> None:
        """Render the LED grid to terminal.

        Clears the terminal and displays the LED grid as a table of colored
        squares using ANSI 24-bit color codes. Each LED is represented by
        a colored space character.

        Uses terminal escape sequences:
        - Clear screen: \\033[H\\033[J
        - Set color: \\033[38;2;R;G;Bm (foreground)
        - Reset color: \\033[0m
        - Cursor position: \\033[H
        """
        with self.lock:
            # Clear screen and move cursor to top-left
            print("\033[H\033[J", end="", flush=True)

            # Print header
            print("LED Strip Simulator - Press Ctrl+C to exit")
            print("=" * (self.cols * 4 + 2))

            # Print LED grid
            for row in range(self.rows):
                for col in range(self.cols):
                    led_idx = row * self.cols + col
                    r, g, b = self.current_leds[led_idx]

                    # ANSI 24-bit color code for foreground
                    color_code = f"\033[38;2;{r};{g};{b}m"
                    reset_code = "\033[0m"

                    # Print colored block (use block character for better visibility)
                    print(f"{color_code}█{reset_code}  ", end="")

                print()  # Newline after each row

            # Print footer with stats
            print("=" * (self.cols * 4 + 2))
            avg_brightness = sum(
                (r + g + b) // 3 for r, g, b in self.current_leds
            ) / len(self.current_leds)
            print(f"Average brightness: {avg_brightness:.1f}/255")

    def get_snapshot(self) -> list[list[int]]:
        """Get current LED state.

        Returns:
            List[List[int]]: Copy of current LED state as list of [R, G, B].

        Example:
            Check current state::

                leds = simulator.get_snapshot()
                print(f"LED 0 color: RGB{tuple(leds[0])}")
        """
        with self.lock:
            return [list(led) for led in self.current_leds]


class MockBeaconGenerator:
    """Generate mock beacon data for simulator testing.

    Creates synthetic BLE beacon data that changes over time to simulate
    real beacon movement and signal strength variation.

    Attributes:
        beacon_ids (List[str]): List of simulated beacon IDs.
        positions (dict): Current position (0.0-1.0) for each beacon.
        rssi_base (dict): Base RSSI value for each beacon.

    Example:
        Generate beacon updates::

            from ble2wled.simulator import MockBeaconGenerator
            from ble2wled import BeaconState

            generator = MockBeaconGenerator(num_beacons=3)
            beacon_state = BeaconState()

            for _ in range(100):
                beacons = generator.update()
                for beacon_id, rssi in beacons.items():
                    beacon_state.update(beacon_id, rssi)
    """

    def __init__(self, num_beacons: int = 3, rssi_range: tuple = (-90, -30)):
        """Initialize mock beacon generator.

        Args:
            num_beacons (int): Number of simulated beacons. Default: 3.
            rssi_range (tuple): (min_rssi, max_rssi) signal range. Default: (-90, -30).
                Typical RSSI range for BLE: -90 (far/weak) to -30 (close/strong).

        Example:
            Generate 5 beacons with custom RSSI range::

                generator = MockBeaconGenerator(
                    num_beacons=5,
                    rssi_range=(-100, -20)
                )
        """
        self.num_beacons = num_beacons
        self.rssi_range = rssi_range
        self.beacon_ids = [f"beacon_{i}" for i in range(num_beacons)]
        self.positions = {bid: i / num_beacons for i, bid in enumerate(self.beacon_ids)}
        self.rssi_base = {
            bid: rssi_range[0] + (i / num_beacons) * (rssi_range[1] - rssi_range[0])
            for i, bid in enumerate(self.beacon_ids)
        }
        self._time = 0.0

    def update(self, time_delta: float = 0.1) -> dict:
        """Update beacon positions and signal strengths.

        Beacons move in a circular pattern and signal strength oscillates
        around their base RSSI value, simulating realistic beacon movement.

        Args:
            time_delta (float): Time step for simulation. Default: 0.1 seconds.

        Returns:
            dict: Beacon data as {beacon_id: rssi_value}.

        Example:
            Step through beacon updates::

                import time
                generator = MockBeaconGenerator(num_beacons=3)
                for _ in range(100):
                    beacons = generator.update(time_delta=0.05)
                    # Update beacon_state with beacons data
                    time.sleep(0.05)
        """
        import math

        self._time += time_delta
        beacons = {}

        for i, beacon_id in enumerate(self.beacon_ids):
            # Circular motion: beacon moves around circle over time
            angle = 2 * math.pi * (self._time / 10.0 + i / self.num_beacons)
            pos = 0.5 + 0.4 * math.cos(angle)

            # Signal strength varies with position (closer = stronger)
            # Add some noise for realism
            noise = 3 * math.sin(self._time * 2 + i)
            rssi_base = self.rssi_range[0] + pos * (
                self.rssi_range[1] - self.rssi_range[0]
            )
            rssi = rssi_base + noise

            beacons[beacon_id] = int(rssi)

        return beacons
