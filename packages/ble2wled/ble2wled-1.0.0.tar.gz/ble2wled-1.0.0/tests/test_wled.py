"""Tests for WLED LED controller implementations.

Tests cover HTTP and UDP controllers with various scenarios:
- Initialization and configuration
- Successful LED updates
- Error handling and retries
- Socket operations (UDP)
- HTTP timeout and connection errors
"""

import socket
from unittest.mock import MagicMock, patch

import pytest
import requests

from ble2wled.wled import LEDController, WLEDHTTPController, WLEDUDPController


class TestLEDController:
    """Tests for abstract LEDController base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that LEDController cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LEDController(host="192.168.1.100", led_count=60)

    def test_subclass_requires_update_method(self):
        """Test that subclass must implement update method."""

        class IncompleteController(LEDController):
            pass

        with pytest.raises(TypeError):
            IncompleteController(host="192.168.1.100", led_count=60)

    def test_subclass_with_update_method_works(self):
        """Test that subclass with update method can be instantiated."""

        class CompleteController(LEDController):
            def update(self, leds):
                pass

        controller = CompleteController(host="192.168.1.100", led_count=60)
        assert controller.host == "192.168.1.100"
        assert controller.led_count == 60


class TestWLEDHTTPController:
    """Tests for HTTP-based WLED controller."""

    def test_init_default_retries(self):
        """Test HTTP controller initialization with default retry count."""
        controller = WLEDHTTPController(host="192.168.1.100", led_count=60)

        assert controller.host == "192.168.1.100"
        assert controller.led_count == 60
        assert controller.max_retries == 3
        assert controller.timeout == 1
        assert controller.url == "http://192.168.1.100/json/state"

    def test_init_custom_retries(self):
        """Test HTTP controller initialization with custom retry count."""
        controller = WLEDHTTPController(host="wled.local", led_count=100, max_retries=5)

        assert controller.host == "wled.local"
        assert controller.led_count == 100
        assert controller.max_retries == 5
        assert controller.url == "http://wled.local/json/state"

    def test_update_success(self):
        """Test successful LED update via HTTP."""
        controller = WLEDHTTPController(host="192.168.1.100", led_count=2)
        leds = [[255, 0, 0], [0, 255, 0]]

        with patch("ble2wled.wled.requests.post") as mock_post:
            controller.update(leds)

            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0] == "http://192.168.1.100/json/state"
            assert call_args[1]["timeout"] == 1

            # Verify payload structure
            payload = call_args[1]["json"]
            assert payload["on"] is True
            assert payload["seg"][0]["id"] == 0
            assert payload["seg"][0]["i"] == leds

    def test_update_with_single_led(self):
        """Test updating with single LED."""
        controller = WLEDHTTPController(host="test.host", led_count=1)
        leds = [[128, 64, 32]]

        with patch("ble2wled.wled.requests.post") as mock_post:
            controller.update(leds)

            payload = mock_post.call_args[1]["json"]
            assert len(payload["seg"][0]["i"]) == 1
            assert payload["seg"][0]["i"][0] == [128, 64, 32]

    def test_update_with_many_leds(self):
        """Test updating with large LED strip."""
        led_count = 500
        controller = WLEDHTTPController(host="192.168.1.100", led_count=led_count)
        leds = [[i % 256, (i * 2) % 256, (i * 3) % 256] for i in range(led_count)]

        with patch("ble2wled.wled.requests.post") as mock_post:
            controller.update(leds)

            payload = mock_post.call_args[1]["json"]
            assert len(payload["seg"][0]["i"]) == led_count

    def test_update_retries_on_timeout(self):
        """Test that update retries on timeout."""
        controller = WLEDHTTPController(
            host="192.168.1.100", led_count=2, max_retries=3
        )
        leds = [[255, 0, 0], [0, 255, 0]]

        with patch("ble2wled.wled.requests.post") as mock_post:
            # Fail twice, then succeed
            mock_post.side_effect = [
                requests.exceptions.Timeout(),
                requests.exceptions.Timeout(),
                None,  # Success
            ]

            controller.update(leds)

            # Should have tried 3 times
            assert mock_post.call_count == 3

    def test_update_retries_on_connection_error(self):
        """Test that update retries on connection error."""
        controller = WLEDHTTPController(
            host="192.168.1.100", led_count=2, max_retries=3
        )
        leds = [[255, 0, 0]]

        with patch("ble2wled.wled.requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError()

            controller.update(leds)

            # Should have tried 3 times (all failed)
            assert mock_post.call_count == 3

    def test_update_retries_on_read_timeout(self):
        """Test that update retries on ReadTimeout."""
        controller = WLEDHTTPController(
            host="192.168.1.100", led_count=1, max_retries=2
        )
        leds = [[100, 100, 100]]

        with patch("ble2wled.wled.requests.post") as mock_post:
            # Fail once, then succeed
            mock_post.side_effect = [
                requests.exceptions.ReadTimeout(),
                None,
            ]

            controller.update(leds)

            assert mock_post.call_count == 2

    def test_update_continues_on_request_exception(self):
        """Test that other RequestException types continue gracefully through loop."""
        controller = WLEDHTTPController(
            host="192.168.1.100", led_count=1, max_retries=3
        )
        leds = [[50, 50, 50]]

        with patch("ble2wled.wled.requests.post") as mock_post:
            # Non-timeout/connection error - caught by generic RequestException handler
            mock_post.side_effect = requests.exceptions.InvalidURL()

            # Should not raise - continues gracefully
            controller.update(leds)

            # The generic exception handler doesn't break, so it continues through loop
            assert mock_post.call_count == 3

    def test_update_returns_none(self):
        """Test that update method returns None."""
        controller = WLEDHTTPController(host="192.168.1.100", led_count=1)
        leds = [[0, 0, 0]]

        with patch("ble2wled.wled.requests.post"):
            result = controller.update(leds)

            assert result is None

    def test_update_sleep_before_retry(self):
        """Test that update sleeps before retry."""
        controller = WLEDHTTPController(
            host="192.168.1.100", led_count=1, max_retries=2
        )
        leds = [[0, 0, 0]]

        with patch("ble2wled.wled.requests.post") as mock_post:
            with patch("ble2wled.wled.time.sleep") as mock_sleep:
                mock_post.side_effect = [requests.exceptions.Timeout(), None]

                controller.update(leds)

                # Should have slept between attempts
                mock_sleep.assert_called_once_with(0.05)

    def test_update_with_custom_timeout(self):
        """Test that timeout is used in requests."""
        controller = WLEDHTTPController(host="192.168.1.100", led_count=1)
        controller.timeout = 2  # timeout is int, set to 2 seconds
        leds = [[0, 0, 0]]

        with patch("ble2wled.wled.requests.post") as mock_post:
            controller.update(leds)

            # Verify timeout was passed
            assert mock_post.call_args[1]["timeout"] == 2

    def test_update_all_zeros(self):
        """Test updating with all black LEDs."""
        controller = WLEDHTTPController(host="test.host", led_count=3)
        leds = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

        with patch("ble2wled.wled.requests.post") as mock_post:
            controller.update(leds)

            payload = mock_post.call_args[1]["json"]
            assert all(rgb == [0, 0, 0] for rgb in payload["seg"][0]["i"])

    def test_update_all_max_brightness(self):
        """Test updating with all white (max brightness) LEDs."""
        controller = WLEDHTTPController(host="test.host", led_count=3)
        leds = [[255, 255, 255], [255, 255, 255], [255, 255, 255]]

        with patch("ble2wled.wled.requests.post") as mock_post:
            controller.update(leds)

            payload = mock_post.call_args[1]["json"]
            assert all(rgb == [255, 255, 255] for rgb in payload["seg"][0]["i"])


class TestWLEDUDPController:
    """Tests for UDP-based WLED controller."""

    def test_init_default_port(self):
        """Test UDP controller initialization with default port."""
        with patch("ble2wled.wled.socket.socket"):
            controller = WLEDUDPController(host="192.168.1.100", led_count=60)

            assert controller.host == "192.168.1.100"
            assert controller.led_count == 60
            assert controller.addr == ("192.168.1.100", 21324)

    def test_init_custom_port(self):
        """Test UDP controller initialization with custom port."""
        with patch("ble2wled.wled.socket.socket"):
            controller = WLEDUDPController(host="wled.local", led_count=100, port=21325)

            assert controller.host == "wled.local"
            assert controller.led_count == 100
            assert controller.addr == ("wled.local", 21325)

    def test_socket_creation(self):
        """Test that UDP socket is created on init."""
        with patch("ble2wled.wled.socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            controller = WLEDUDPController(host="192.168.1.100", led_count=60)

            # Verify socket was created with correct parameters
            mock_socket_class.assert_called_once_with(socket.AF_INET, socket.SOCK_DGRAM)
            assert controller.sock == mock_socket

    def test_update_sends_drgb_packet(self):
        """Test that update sends DRGB format packet."""
        with patch("ble2wled.wled.socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            controller = WLEDUDPController(host="192.168.1.100", led_count=2)
            leds = [[255, 0, 0], [0, 255, 0]]

            controller.update(leds)

            # Verify sendto was called
            mock_socket.sendto.assert_called_once()

            # Get the packet that was sent
            packet, addr = mock_socket.sendto.call_args[0]

            # Verify packet structure
            assert packet[:4] == b"DRGB"  # Header
            assert addr == ("192.168.1.100", 21324)
            assert len(packet) == 4 + (3 * 2)  # Header + 2 LEDs

    def test_update_drgb_payload_single_led(self):
        """Test DRGB payload for single LED."""
        with patch("ble2wled.wled.socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            controller = WLEDUDPController(host="test.host", led_count=1)
            leds = [[200, 100, 50]]

            controller.update(leds)

            packet, _ = mock_socket.sendto.call_args[0]

            assert packet == b"DRGB\xc8\x64\x32"  # DRGB + RGB bytes

    def test_update_drgb_payload_multiple_leds(self):
        """Test DRGB payload for multiple LEDs."""
        with patch("ble2wled.wled.socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            controller = WLEDUDPController(host="test.host", led_count=3)
            leds = [[255, 0, 0], [0, 255, 0], [0, 0, 255]]

            controller.update(leds)

            packet, _ = mock_socket.sendto.call_args[0]

            # Expected: DRGB + RGB triplets
            expected = (
                b"DRGB" + bytes([255, 0, 0]) + bytes([0, 255, 0]) + bytes([0, 0, 255])
            )
            assert packet == expected

    def test_update_with_large_led_strip(self):
        """Test update with many LEDs."""
        with patch("ble2wled.wled.socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            led_count = 300
            controller = WLEDUDPController(host="test.host", led_count=led_count)
            leds = [[i % 256, (i * 2) % 256, (i * 3) % 256] for i in range(led_count)]

            controller.update(leds)

            packet, _ = mock_socket.sendto.call_args[0]

            # Header is 4 bytes, plus 3 bytes per LED
            assert len(packet) == 4 + (3 * led_count)

    def test_update_returns_none(self):
        """Test that update method returns None."""
        with patch("ble2wled.wled.socket.socket"):
            controller = WLEDUDPController(host="test.host", led_count=1)
            leds = [[0, 0, 0]]

            result = controller.update(leds)

            assert result is None

    def test_update_all_zeros(self):
        """Test update with all black LEDs."""
        with patch("ble2wled.wled.socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            controller = WLEDUDPController(host="test.host", led_count=2)
            leds = [[0, 0, 0], [0, 0, 0]]

            controller.update(leds)

            packet, _ = mock_socket.sendto.call_args[0]

            assert packet == b"DRGB\x00\x00\x00\x00\x00\x00"

    def test_update_all_max_brightness(self):
        """Test update with all white (max brightness) LEDs."""
        with patch("ble2wled.wled.socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            controller = WLEDUDPController(host="test.host", led_count=2)
            leds = [[255, 255, 255], [255, 255, 255]]

            controller.update(leds)

            packet, _ = mock_socket.sendto.call_args[0]

            assert packet == b"DRGB\xff\xff\xff\xff\xff\xff"

    def test_update_custom_port(self):
        """Test that update uses custom port."""
        with patch("ble2wled.wled.socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            controller = WLEDUDPController(host="test.host", led_count=1, port=9999)
            leds = [[100, 100, 100]]

            controller.update(leds)

            _, addr = mock_socket.sendto.call_args[0]

            assert addr == ("test.host", 9999)

    def test_update_different_hosts(self):
        """Test update with different host addresses."""
        with patch("ble2wled.wled.socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            # Test with IP address
            controller1 = WLEDUDPController(host="192.168.1.100", led_count=1)
            leds = [[0, 0, 0]]
            controller1.update(leds)
            addr1 = mock_socket.sendto.call_args[0][1]
            assert addr1[0] == "192.168.1.100"

            # Test with hostname
            mock_socket.reset_mock()
            controller2 = WLEDUDPController(host="wled.local", led_count=1)
            controller2.update(leds)
            addr2 = mock_socket.sendto.call_args[0][1]
            assert addr2[0] == "wled.local"


class TestControllerIntegration:
    """Integration tests comparing HTTP and UDP controllers."""

    def test_both_controllers_same_led_data(self):
        """Test that both controllers handle same LED data."""
        leds = [[255, 0, 0], [0, 255, 0], [0, 0, 255]]

        # HTTP controller
        http_controller = WLEDHTTPController(host="test.host", led_count=3)
        with patch("ble2wled.wled.requests.post") as mock_post:
            http_controller.update(leds)
            http_payload = mock_post.call_args[1]["json"]
            http_leds = http_payload["seg"][0]["i"]

        # UDP controller
        with patch("ble2wled.wled.socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket

            udp_controller = WLEDUDPController(host="test.host", led_count=3)
            udp_controller.update(leds)

            packet, _ = mock_socket.sendto.call_args[0]
            udp_leds = [list(packet[i : i + 3]) for i in range(4, len(packet), 3)]

        # Both should have same LED data
        assert http_leds == leds
        assert udp_leds == leds

    def test_controllers_inherit_from_base(self):
        """Test that both controllers properly inherit from base."""
        with patch("ble2wled.wled.socket.socket"):
            http = WLEDHTTPController(host="test", led_count=10)
            udp = WLEDUDPController(host="test", led_count=10)

            assert isinstance(http, LEDController)
            assert isinstance(udp, LEDController)

            assert http.host == "test"
            assert http.led_count == 10
            assert udp.host == "test"
            assert udp.led_count == 10
