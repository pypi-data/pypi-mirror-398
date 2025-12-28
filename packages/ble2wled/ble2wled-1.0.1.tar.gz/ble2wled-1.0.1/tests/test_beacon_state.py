"""Tests for BeaconState class."""

import time

from ble2wled.states import BeaconState


class TestBeaconState:
    """Test cases for BeaconState."""

    def test_init(self):
        """Test BeaconState initialization."""
        state = BeaconState(timeout_seconds=5.0, fade_out_seconds=3.0)
        assert state.timeout == 5.0
        assert state.fade_out == 3.0

    def test_update_beacon(self):
        """Test updating a beacon."""
        state = BeaconState()
        state.update("beacon_1", -50)
        snapshot = state.snapshot()

        assert "beacon_1" in snapshot
        rssi, life = snapshot["beacon_1"]
        assert rssi == -50
        assert life == 1.0

    def test_beacon_timeout(self):
        """Test beacon timeout and fade out."""
        state = BeaconState(timeout_seconds=0.1, fade_out_seconds=0.2)
        state.update("beacon_1", -50)

        # Beacon should be active initially
        snapshot = state.snapshot()
        assert "beacon_1" in snapshot
        assert snapshot["beacon_1"][1] == 1.0

        # Wait for timeout
        time.sleep(0.15)
        snapshot = state.snapshot()
        assert "beacon_1" in snapshot
        rssi, life = snapshot["beacon_1"]
        assert rssi == -50
        assert 0.0 < life < 1.0

    def test_beacon_removal(self):
        """Test beacon removal after fade out."""
        state = BeaconState(timeout_seconds=0.1, fade_out_seconds=0.1)
        state.update("beacon_1", -50)

        # Wait for complete fade out
        time.sleep(0.25)
        snapshot = state.snapshot()
        assert "beacon_1" not in snapshot

    def test_multiple_beacons(self):
        """Test tracking multiple beacons."""
        state = BeaconState()
        state.update("beacon_1", -50)
        state.update("beacon_2", -60)
        state.update("beacon_3", -70)

        snapshot = state.snapshot()
        assert len(snapshot) == 3
        assert "beacon_1" in snapshot
        assert "beacon_2" in snapshot
        assert "beacon_3" in snapshot
