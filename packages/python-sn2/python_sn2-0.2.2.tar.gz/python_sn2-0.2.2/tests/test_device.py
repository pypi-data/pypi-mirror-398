"""
Test suite for the Device class in the SystemNexa2 integration.

This module contains tests for the Device class, including positive and
negative test cases for WebSocket communication, message processing, and
lifecycle events.
"""

import asyncio
import json
import logging
import sys
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, Mock, patch

import pytest

from sn2.device import (
    ConnectionStatus,
    Device,
    InformationUpdate,
    OnOffSetting,
    SettingsUpdate,
    StateChange,
)

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(autouse=True)
def configure_logger() -> None:
    """Configure the logger to output to stdout during tests."""
    logger = logging.getLogger("sn2.device")
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.handlers = [handler]


@pytest.mark.asyncio
class TestDevice:
    """Test suite for the Device class."""

    @pytest.fixture
    def device(self) -> Device:
        """Fixture to create a Device instance."""
        self.on_update_mock = AsyncMock()
        return Device(host="192.168.1.100", on_update=self.on_update_mock)

    @pytest.fixture
    def mock_websocket(self) -> "Generator":
        """Properly patch websockets.connect to work with any URL."""
        with patch("websockets.connect") as mocked_connect:

            async def mock_aenter() -> AsyncMock:
                mocked_websocket = AsyncMock()
                mocked_websocket.recv = AsyncMock(return_value="mocked_message")
                mocked_websocket.send = AsyncMock()
                mocked_websocket.close = AsyncMock()
                return mocked_websocket

            async def mock_aexit(
                _self: object, _exc: object, _val: object, _tb: object
            ) -> None:
                return

            mocked_connect.__aexit__ = mock_aexit
            mocked_connect.__aenter__ = mock_aenter

            yield mocked_connect

    async def test_connect_disconnect_success(
        self, mock_websocket: AsyncMock, device: Device
    ) -> None:
        """Test successful connection and disconnection to the device."""
        mock_ws = mock_websocket.return_value.__aenter__.return_value

        await device.connect()
        await asyncio.sleep(0)  # Allow the task to start

        # Verify login message was sent
        mock_ws.send.assert_called_with(json.dumps({"type": "login", "value": ""}))

        # Verify connection status callback was called
        latest_update = self.on_update_mock.call_args_list[-1]
        assert isinstance(latest_update.args[0], ConnectionStatus)
        latest_args = latest_update.args[0]
        assert latest_args.connected is True

        # Disconnect
        await device.disconnect()
        await asyncio.sleep(0.1)

        # Verify disconnect callback was called
        latest_update = self.on_update_mock.call_args_list[-1]
        assert isinstance(latest_update.args[0], ConnectionStatus)
        latest_args = latest_update.args[0]
        assert latest_args.connected is False

    async def test_connection_failure(
        self, device: Device, mock_websocket: AsyncMock
    ) -> None:
        """Test connection failure handling."""
        mock_websocket.side_effect = ConnectionError("Connection error")

        await device.connect()
        await asyncio.sleep(0.1)  # Allow the task to attempt connection

        # Verify disconnect callback was called due to connection failure
        disconnect_calls = [
            call
            for call in self.on_update_mock.call_args_list
            if isinstance(call[0][0], ConnectionStatus) and not call[0][0].connected
        ]
        assert len(disconnect_calls) > 0

    async def test_information_message_processing(
        self, device: Device, mock_websocket: AsyncMock
    ) -> None:
        """Test processing of information message from device."""
        info_message = json.dumps(
            {
                "type": "information",
                "value": {
                    "fhs": 90752,
                    "u": 261970,
                    "wr": -60,
                    "ss": "0.00",
                    "t": "68.20",
                    "n": "Test Device",
                    "tsc": 3,
                    "lcu": "test-unique-id",
                    "lat": 62,
                    "lon": 15,
                    "cs": True,
                    "sr_h": 8,
                    "sr_m": 1,
                    "ss_h": 15,
                    "ss_m": 25,
                    "tz_o": 3600,
                    "tz_i": 1,
                    "tz_dst": 0,
                    "c": False,
                    "ws": "TestNetwork",
                    "rr": 1,
                    "hwm": "WBD-01",
                    "nhwv": 1,
                    "nswv": "1.1.1",
                    "b": {"s": 1, "v": 0, "bp": 0, "bpr": 0, "bi": 0},
                },
            }
        )

        mock_ws = mock_websocket.return_value.__aenter__.return_value
        mock_ws.recv.return_value = info_message

        await device.connect()
        await asyncio.sleep(0.2)  # Allow message processing

        # Verify information update callback was called
        info_calls = [
            call
            for call in self.on_update_mock.call_args_list
            if isinstance(call[0][0], InformationUpdate)
        ]
        assert len(info_calls) > 0
        info_data = info_calls[0][0][0].information
        assert info_data.name == "Test Device"
        assert info_data.model == "WBD-01"
        assert info_data.dimmable is True  # WBD-01 is a light model

        await device.disconnect()

    async def test_settings_message_processing(
        self, device: Device, mock_websocket: AsyncMock
    ) -> None:
        """Test processing of settings message from device."""
        settings_message = json.dumps(
            {
                "type": "settings",
                "value": {
                    "name": "DeviceName",
                    "tz_id": 1,
                    "auto_on_seconds": 0,
                    "auto_off_seconds": 0,
                    "enable_local_security": 0,
                    "vacation_mode": 0,
                    "state_after_powerloss": 2,
                    "disable_physical_button": 0,
                    "disable_433": 1,
                    "disable_multi_press": 0,
                    "disable_network_ctrl": 0,
                    "disable_led": 0,
                    "disable_on_transmitters": 0,
                    "disable_off_transmitters": 0,
                    "dimmer_edge": 0,
                    "blink_on_433_on": 0,
                    "button_type": 0,
                    "diy_mode": 1,
                    "toggle_433": 0,
                    "position_man_set": 0,
                    "dimmer_on_start_level": 0,
                    "dimmer_off_level": 0,
                    "dimmer_min_dim": 0,
                    "remote_log": 1,
                    "notifcation_on": 1,
                    "notifcation_off": 0,
                },
            }
        )

        mock_ws = mock_websocket.return_value.__aenter__.return_value
        mock_ws.recv.return_value = settings_message

        await device.connect()
        await asyncio.sleep(0.2)  # Allow message processing

        # Verify settings update callback was called
        setting_updates = [
            call.args[0]
            for call in self.on_update_mock.call_args_list
            if isinstance(call.args[0], SettingsUpdate)
        ]
        assert len(setting_updates) == 1
        setting_update = setting_updates[0]
        # Filter OnOffSettings from the list
        onoff_settings = [
            s for s in setting_update.settings if isinstance(s, OnOffSetting)
        ]

        # Verify we have four OnOffSettings
        expected_settings_count = 4
        assert len(onoff_settings) == expected_settings_count

        # Find the 433MHz setting and verify it's off
        # (value == 1 means disabled/off)
        mhz_433_setting = next((s for s in onoff_settings if "433Mhz" in s.name), None)
        assert mhz_433_setting is not None
        assert not mhz_433_setting.is_enabled()
        cloud = next((s for s in onoff_settings if "Cloud Access" in s.name), None)
        assert cloud is not None
        assert not cloud.is_enabled()

        led_setting = next((s for s in onoff_settings if "Led" in s.name), None)
        assert led_setting is not None
        assert led_setting.is_enabled()
        physical_button = next(
            (s for s in onoff_settings if "Physical Button" in s.name), None
        )
        assert physical_button is not None
        assert physical_button.is_enabled()

        await device.disconnect()

    async def test_state_change_message_processing(
        self, device: Device, mock_websocket: AsyncMock
    ) -> None:
        """Test processing of state change message from device."""
        state_message = json.dumps({"type": "state", "value": 0.75})

        mock_ws = mock_websocket.return_value.__aenter__.return_value
        mock_ws.recv.return_value = state_message

        await device.connect()
        await asyncio.sleep(0.2)  # Allow message processing

        # Verify state change callback was called
        expected_brightness = 0.75
        state_calls = [
            call
            for call in self.on_update_mock.call_args_list
            if isinstance(call[0][0], StateChange)
        ]
        assert len(state_calls) > 0
        assert state_calls[0][0][0].state == expected_brightness

        await device.disconnect()

    async def test_get_info_success(self, device: Device) -> None:
        """Test fetching device information via REST API."""
        mock_response_data = {
            "fhs": 90752,
            "u": 261970,
            "wr": -60,
            "ss": "0.00",
            "t": "68.20",
            "n": "Test Device",
            "tsc": 3,
            "lcu": "test-unique-id",
            "lat": 62,
            "lon": 15,
            "cs": True,
            "sr_h": 8,
            "sr_m": 1,
            "ss_h": 15,
            "ss_m": 25,
            "tz_o": 3600,
            "tz_i": 1,
            "tz_dst": 0,
            "c": False,
            "ws": "TestNetwork",
            "rr": 1,
            "hwm": "WBD-01",
            "nhwv": 1,
            "nswv": "1.1.1",
            "b": {"s": 1, "v": 0, "bp": 0, "bpr": 0, "bi": 0},
        }

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_response.raise_for_status = Mock()
            mock_get.return_value.__aenter__.return_value = mock_response

            info = await device.get_info()

            assert info is not None
            assert isinstance(info, InformationUpdate)
            assert info.information.name == "Test Device"
            assert info.information.model == "WBD-01"
            assert info.information.dimmable is True

    async def test_get_info_failure(self, device: Device) -> None:
        """Test failure when fetching device information via REST API."""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.side_effect = RuntimeError("HTTP error")

            with pytest.raises(RuntimeError, match="HTTP error"):
                await device.get_info()

    async def test_get_settings_success(self, device: Device) -> None:
        """Test fetching device settings via REST API."""
        mock_settings_data = {
            "name": "DeviceName",
            "tz_id": 1,
            "disable_433": 1,
            "diy_mode": 1,
            "disable_led": 0,
        }

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value=mock_settings_data)
            mock_response.raise_for_status = Mock()
            mock_get.return_value.__aenter__.return_value = mock_response

            list_of_settings = await device.get_settings()

            assert isinstance(list_of_settings, list)

            # Filter OnOffSettings from the list
            onoff_settings = [
                s for s in list_of_settings if isinstance(s, OnOffSetting)
            ]

            # Verify we have three OnOffSettings
            expected_onoff_count = 3
            assert len(onoff_settings) == expected_onoff_count

            # Find the 433MHz setting and verify it's off
            # (value == 1 means disabled/off)
            mhz_433_setting = next(
                (s for s in onoff_settings if "433Mhz" in s.name), None
            )
            assert mhz_433_setting is not None
            assert not mhz_433_setting.is_enabled()
            cloud = next((s for s in onoff_settings if "Cloud Access" in s.name), None)
            assert cloud is not None
            assert not cloud.is_enabled()

            led_setting = next((s for s in onoff_settings if "Led" in s.name), None)
            assert led_setting is not None
            assert led_setting.is_enabled()

    async def test_get_settings_failure(self, device: Device) -> None:
        """Test failure when fetching device settings via REST API."""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.side_effect = RuntimeError("HTTP error")

            with pytest.raises(RuntimeError, match="HTTP error"):
                await device.get_settings()

    async def test_turn_on(self, device: Device, mock_websocket: AsyncMock) -> None:
        """Test turning on the device."""
        mock_ws = mock_websocket.return_value.__aenter__.return_value

        await device.connect()
        await asyncio.sleep(0.1)

        await device.turn_on()

        # Verify turn on command was sent
        turn_on_calls = [
            call
            for call in mock_ws.send.call_args_list
            if json.loads(call[0][0]).get("type") == "state"
            and json.loads(call[0][0]).get("value") == -1
        ]
        assert len(turn_on_calls) > 0

        await device.disconnect()

    async def test_turn_off(self, device: Device, mock_websocket: AsyncMock) -> None:
        """Test turning off the device."""
        mock_ws = mock_websocket.return_value.__aenter__.return_value

        await device.connect()
        await asyncio.sleep(0.1)

        await device.turn_off()

        # Verify turn off command was sent
        turn_off_calls = [
            call
            for call in mock_ws.send.call_args_list
            if json.loads(call[0][0]).get("type") == "state"
            and json.loads(call[0][0]).get("value") == 0
        ]
        assert len(turn_off_calls) > 0

        await device.disconnect()

    async def test_turn_on_v1_1_8(
        self, device: Device, mock_websocket: AsyncMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test turning on the device with version 1.1.8."""
        mock_ws = mock_websocket.return_value.__aenter__.return_value

        monkeypatch.setattr(device, "_version", "1.1.8")

        await device.connect()
        await asyncio.sleep(0.1)

        await device.turn_on()

        # Verify turn on command was sent
        turn_on_calls = [
            call
            for call in mock_ws.send.call_args_list
            if json.loads(call[0][0]).get("type") == "state"
            and json.loads(call[0][0]).get("on")
        ]
        assert len(turn_on_calls) > 0

        await device.disconnect()

    async def test_turn_off_v1_1_8(
        self, device: Device, mock_websocket: AsyncMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test turning off the device with version 1.1.8."""
        mock_ws = mock_websocket.return_value.__aenter__.return_value

        monkeypatch.setattr(device, "_version", "1.1.8")

        await device.connect()
        await asyncio.sleep(0.1)

        await device.turn_off()

        # Verify turn off command was sent
        turn_off_calls = [
            call
            for call in mock_ws.send.call_args_list
            if json.loads(call[0][0]).get("type") == "state"
            and not json.loads(call[0][0]).get("on")
        ]
        assert len(turn_off_calls) > 0

        await device.disconnect()

    async def test_set_brightness(
        self, device: Device, mock_websocket: AsyncMock
    ) -> None:
        """Test setting device brightness."""
        mock_ws = mock_websocket.return_value.__aenter__.return_value

        await device.connect()
        await asyncio.sleep(0.1)

        test_brightness = 0.5
        await device.set_brightness(test_brightness)

        # Verify brightness command was sent
        brightness_calls = [
            call
            for call in mock_ws.send.call_args_list
            if json.loads(call[0][0]).get("type") == "state"
            and json.loads(call[0][0]).get("value") == test_brightness
        ]
        assert len(brightness_calls) > 0

        await device.disconnect()

    async def test_set_brightness_invalid_value(self, device: Device) -> None:
        """Test setting brightness with invalid value."""
        with pytest.raises(ValueError, match="Brightness value must be between"):
            await device.set_brightness(1.5)

        with pytest.raises(ValueError, match="Brightness value must be between"):
            await device.set_brightness(-0.1)

    async def test_toggle(self, device: Device, mock_websocket: AsyncMock) -> None:
        """Test toggling the device."""
        mock_ws = mock_websocket.return_value.__aenter__.return_value

        await device.connect()
        await asyncio.sleep(0.1)

        await device.toggle()

        # Verify toggle command was sent (value -1)
        toggle_calls = [
            call
            for call in mock_ws.send.call_args_list
            if json.loads(call[0][0]).get("type") == "state"
            and json.loads(call[0][0]).get("value") == -1
        ]
        assert len(toggle_calls) > 0

        await device.disconnect()
