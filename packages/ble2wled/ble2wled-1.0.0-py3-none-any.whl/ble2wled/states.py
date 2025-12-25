"""Beacon state management with timeout and fade-out.

This module provides the BeaconState class for tracking BLE beacons with
automatic timeout and fade-out effects. Beacons update their \"life\" value
from 1.0 (fully visible) to 0.0 (faded out) as they age.

Example:
    Track beacons and get their current state::

        state = BeaconState(timeout_seconds=6.0, fade_out_seconds=4.0)
        state.update('beacon_1', -50)  # Update with RSSI
        beacons = state.snapshot()     # Get current beacons
        for beacon_id, (rssi, life) in beacons.items():
            print(f\"{beacon_id}: RSSI={rssi}, life={life}\")
"""

import threading
import time


class BeaconState:
    """Manages the state of detected beacons with automatic timeout and fade-out.

    This class maintains a thread-safe collection of beacons with their RSSI
    values and life metrics. Beacons automatically timeout when not updated
    and fade out gracefully over a configurable period.

    Attributes:
        timeout (float): Seconds before a beacon is considered timed out.
        fade_out (float): Seconds to fade out after timeout.
    """

    def __init__(self, timeout_seconds: float = 5.0, fade_out_seconds: float = 3.0):
        """Initialize beacon state tracker.

        Args:
            timeout_seconds (float): Duration before a beacon is considered
                timed out (no updates received). Default is 5.0 seconds.
            fade_out_seconds (float): Duration to fade out the beacon after
                timeout. Default is 3.0 seconds.

        Example:
            Create a beacon state tracker with 6-second timeout and 4-second fade::

                state = BeaconState(timeout_seconds=6.0, fade_out_seconds=4.0)
        """
        self._lock = threading.Lock()
        self.timeout = timeout_seconds
        self.fade_out = fade_out_seconds
        self._beacons: dict[str, dict] = {}

    def update(self, beacon_id: str, rssi: int) -> None:
        """Update beacon with signal strength.

        Updates or creates a beacon entry with the current timestamp and RSSI.
        Thread-safe operation.

        Args:
            beacon_id (str): Unique beacon identifier (e.g.,
                'iBeacon:2686f39c-bada-4658-854a-a62e7e5e8b8d-1-0').
            rssi (int): Received Signal Strength Indicator in dBm
                (typically -30 to -100).

        Example:
            Update beacon with RSSI value::

                state.update('beacon_1', -50)  # Update beacon_1 with -50 dBm
        """
        now = time.time()
        with self._lock:
            self._beacons[beacon_id] = {
                "rssi": rssi,
                "last_seen": now,
                "life": 1.0,
            }

    def snapshot(self) -> dict[str, tuple[int, float]]:
        """Get current active beacons with RSSI and life values.

        Returns a thread-safe snapshot of all active beacons. Automatically
        removes beacons that have completely faded out. Each beacon entry
        includes its RSSI and life value (0.0 = invisible, 1.0 = fully visible).

        Returns:
            dict: Dictionary mapping beacon_id (str) to (rssi, life) tuples.
                rssi (int): Signal strength in dBm.
                life (float): Beacon visibility (0.0 to 1.0).

        Example:
            Get current beacon snapshot::

                beacons = state.snapshot()
                if 'beacon_1' in beacons:
                    rssi, life = beacons['beacon_1']
                    print(f"Beacon 1: {rssi} dBm, {life*100:.0f}% visible")
        """
        now = time.time()
        active = {}

        with self._lock:
            to_remove = []

            for beacon_id, data in self._beacons.items():
                age = now - data["last_seen"]

                if age <= self.timeout:
                    data["life"] = 1.0
                else:
                    decay = (age - self.timeout) / self.fade_out
                    data["life"] = max(0.0, 1.0 - decay)

                if data["life"] <= 0.0:
                    to_remove.append(beacon_id)
                else:
                    active[beacon_id] = (data["rssi"], data["life"])

            for beacon_id in to_remove:
                del self._beacons[beacon_id]

        return active
