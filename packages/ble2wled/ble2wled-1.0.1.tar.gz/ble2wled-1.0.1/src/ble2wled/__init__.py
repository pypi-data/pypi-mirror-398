"""
BLE2WLED - Bluetooth Low Energy to WLED LED Controller

This package provides real-time BLE beacon detection and visualization
on WLED devices through MQTT integration.
"""

from .animation import BeaconRunner, add_trail
from .colors import (
    ble_beacon_to_rgb,
    estimate_distance_from_rssi,
    gradient_color,
)
from .config import Config
from .main import run_wled_beacons
from .mqtt import BeaconMQTTListener, EspresenseBeaconListener
from .simulator import LEDSimulator, MockBeaconGenerator
from .states import BeaconState
from .wled import LEDController, WLEDHTTPController, WLEDUDPController

__all__ = [
    "BeaconState",
    "BeaconRunner",
    "BeaconMQTTListener",
    "EspresenseBeaconListener",
    "Config",
    "LEDController",
    "WLEDHTTPController",
    "WLEDUDPController",
    "LEDSimulator",
    "MockBeaconGenerator",
    "estimate_distance_from_rssi",
    "gradient_color",
    "ble_beacon_to_rgb",
    "add_trail",
    "run_wled_beacons",
]
