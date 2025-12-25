"""
Device client for SystemNexa2 integration.

Handles connection, message processing, and lifecycle events for devices.
"""

import asyncio
import contextlib
import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Final

import aiohttp
import websockets

from sn2.json_model import DeviceInformation, Settings

_LOGGER = logging.getLogger(__name__)


class DeviceInitializationError(Exception):
    """Exception raised when device initialization fails."""

    def __init__(self, message: str = "Failed to initialize device") -> None:
        """Initialize the exception with an optional message."""
        self.message = message
        super().__init__(self.message)


class DeviceUnsupportedError(Exception):
    """Exception raised when device is unsupported."""

    def __init__(self, message: str = "Device not supported") -> None:
        """Initialize the exception with an optional message."""
        self.message = message
        super().__init__(self.message)


class NotConnectedError(Exception):
    """Exception raised when device has not been connected before running commands."""

    def __init__(self, message: str = "Device not connected") -> None:
        """Initialize the exception with an optional message."""
        self.message = message
        super().__init__(self.message)


SWITCH_MODELS: Final = ["WBR-01"]
PLUG_MODELS: Final = ["WPR-01", "WPO-01"]
LIGHT_MODELS: Final = ["WBD-01", "WPD-01"]


@dataclass
class InformationData:
    """
    Device information data container.

    Attributes
    ----------
    dimmable : bool
        Whether the device supports dimming.
    model : str | None
        The hardware model of the device.
    sw_version : str | None
        The software version of the device.
    hw_version : str | None
        The hardware version of the device.
    name : str | None
        The name of the device.
    wifi_dbm : int | None
        The WiFi signal strength in dBm.
    wifi_ssid : str | None
        The WiFi SSID the device is connected to.
    unique_id : str | None
        The unique identifier of the device.

    """

    model: str
    sw_version: str | None
    hw_version: str | None
    name: str
    wifi_dbm: int | None
    wifi_ssid: str | None
    unique_id: str
    dimmable: bool

    @staticmethod
    def convert_device_information_to_data(
        info: DeviceInformation,
    ) -> "InformationData":
        """
        Create InformationData from a DeviceInformation object.

        Parameters
        ----------
        info : DeviceInformation
            The device information object to convert.

        Returns
        -------
        InformationData
            A new InformationData instance populated with the device information.

        """
        if info.lcu is None:
            msg = "lcu (unique id) cannot be None, broken/corrupt device?"
            raise ValueError(msg)
        if info.hwm is None:
            msg = "hwm (model) cannot be None, broken/corrupt device?"
            raise ValueError(msg)
        if info.n is None:
            msg = "n (name) cannot be None, broken/corrupt device?"
            raise ValueError(msg)
        return InformationData(
            model=info.hwm or "",
            sw_version=info.nswv or "",
            hw_version=str(info.nhwv) if info.nhwv is not None else "",
            name=info.n,
            wifi_dbm=info.wr,
            wifi_ssid=info.ws,
            unique_id=info.lcu,
            dimmable=info.hwm in LIGHT_MODELS,
        )


@dataclass
class ConnectionStatus:
    """Connection status event."""

    connected: bool


@dataclass
class InformationUpdate:
    """Information status event."""

    information: InformationData


@dataclass
class StateChange:
    """
    State change event.

    Attributes
    ----------
    state : float
        The new state value of the device.

    """

    state: float


class Setting:
    """
    Base class for device settings.

    Attributes
    ----------
    name : str
        The display name of the setting.

    """

    name: str


class OnOffSetting(Setting):
    """
    A setting that represents an on/off state with configurable values.

    This class extends the Setting base class to provide a binary state setting
    that can be toggled between two predefined values (on and off).

    Args:
        name (str): The display name for this setting.
        param_key (str): The parameter key to use when communicating with the device.
        current: The current value/state of the setting.
        on_value: The value that represents the enabled/on state.
        off_value: The value that represents the disabled/off state.

    """

    def __init__(
        self, name: str, param_key: str, current: Any, on_value: Any, off_value: Any
    ) -> None:
        """
        Initialize a Device instance.

        Args:
            name (str): The name of the device.
            param_key (str): The parameter key used to identify the device
                parameter.
            current (Any): The current state/value of the device.
            on_value (Any): The value that represents the device being in an
                "on" state.
            off_value (Any): The value that represents the device being in an
                "off" state.

        Returns:
            None

        """
        self.name = name
        self._param_key = param_key
        self._enable_value = on_value
        self._disable_value = off_value
        self._current_state = current

    async def enable(self, device: "Device") -> None:
        """
        Enable a setting with the enable value.

        Args:
            device (Device): The device instance to which the setting should be enabled.

        """
        await device.update_setting({self._param_key: self._enable_value})

    async def disable(self, device: "Device") -> None:
        """
        Disable the setting.

        Args:
            device (Device): The device instance to which the setting should be
                disabled.

        """
        await device.update_setting({self._param_key: self._disable_value})

    def is_enabled(self) -> bool:
        """
        Check if the setting is currently enabled.

        Returns:
            bool: True if the device's current state matches the enable value,
                False otherwise.

        """
        return self._current_state == self._enable_value


@dataclass
class SettingsUpdate:
    """Settings update event."""

    settings: list[Setting]


UpdateEvent = ConnectionStatus | InformationUpdate | SettingsUpdate | StateChange


class Device:
    """
    Represents a client for SystemNexa2 device integration.

    Handles connection, message processing, and lifecycle events for devices.

    """

    @staticmethod
    def _is_version_compatible(version: str | None, min_version: str) -> bool:
        """Check if a version string meets minimum version requirements."""
        if version is None:
            return False
        if min_version is None:
            msg = "min_version needs to be set when comparing"
            raise ValueError(msg)
        try:
            # Clean up version strings - remove any pre-release indicators
            # Example: "0.9.5-beta.2" becomes "0.9.5"
            clean_version = version.split("-")[0].split("+")[0]
            clean_min_version = min_version.split("-")[0].split("+")[0]

            version_parts = [int(part) for part in clean_version.split(".")]
            min_version_parts = [int(part) for part in clean_min_version.split(".")]

            while len(version_parts) < len(min_version_parts):
                version_parts.append(0)
            while len(min_version_parts) < len(version_parts):
                min_version_parts.append(0)

            # Compare version components
            for v, m in zip(version_parts, min_version_parts, strict=False):
                if v > m:
                    return True
                if v < m:
                    return False

            # All components are equal, so versions are equal

        except (ValueError, IndexError):
            # If parsing fails, log the error and reject the version
            _LOGGER.exception(
                "Error parsing version strings '%s' and '%s'",
                version,
                min_version,
            )
            return False
        return True

    @staticmethod
    def is_device_supported(
        model: str | None, device_version: str | None
    ) -> tuple[bool, str]:
        """Check if a device is supported based on model and firmware version."""
        # Check if this is a supported device
        if model is None:
            return False, "Missing model information"

        # Verify model is in our supported lists
        if (
            model not in SWITCH_MODELS
            and model not in LIGHT_MODELS
            and model not in PLUG_MODELS
        ):
            return False, f"Unsupported model: {model}"

        # Check firmware version requirement
        if device_version is None:
            return False, "Missing firmware version"

        # Version check - require at least 0.9.5
        if not Device._is_version_compatible(device_version, min_version="0.9.5"):
            return (
                False,
                f"Incompatible firmware version {device_version} (min required: 0.9.5)",
            )

        return True, ""

    def __init__(
        self,
        host: str,
        on_update: Callable[[UpdateEvent], Awaitable[None] | None] | None = None,
    ) -> None:
        """
        Initialize the Device client.

        Args:
            host (str): The host address of the device.
            on_update (Callable[[UpdateEvent], Awaitable[None] | None] | None):
                Callback for device update events.

        """
        self.host = host
        self._trying_to_connect = False
        self._websocket: websockets.ClientConnection | None = None
        self._ws_task: asyncio.Task[None] | None = None
        self._login_key = None
        self._version: str | None = None
        self.info_data: InformationData | None = None
        self.initialized = False
        self.settings: list[Setting] = []

        # Callbacks
        self._on_update = on_update

    async def initialize(self) -> None:
        """
        Initialize the device by fetching settings and information.

        Raises
        ------
        DeviceInitializationError
            If fetching settings or information fails.

        """
        try:
            self.settings = await self.get_settings()
            info = await self.get_info()
            self._version = info.information.sw_version
            self.info_data = info.information
        except Exception as e:
            msg = "Failed to initialize device"
            raise DeviceInitializationError(msg) from e

    async def _emit(self, event: UpdateEvent) -> None:
        """Invoke unified callback if provided."""
        if not self._on_update:
            return
        try:
            result = self._on_update(event)
            if isinstance(result, Awaitable):
                await result
        except Exception:
            _LOGGER.exception("on_update callback failed for %s", event)

    async def connect(self) -> None:
        """
        Establish a connection to the device via websocket.

        Starts the websocket client task for handling device communication.
        """
        if self._ws_task is not None:
            return  # Already connected

        self._trying_to_connect = True
        self._ws_task = asyncio.create_task(self._handle_connection())

    # Set up connection and cleanup
    async def _handle_connection(self) -> None:
        """Start the websocket client for the device."""
        uri = f"ws://{self.host}:3000/live"

        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    self._websocket = websocket
                    # Set device as available since connection is established

                    # Send login message immediately after connection
                    login_message = {"type": "login", "value": ""}
                    await websocket.send(json.dumps(login_message))

                    await self._emit(ConnectionStatus(connected=True))
                    _LOGGER.debug("Sent login message: %s", login_message)

                    # Listen for messages from the device
                    while True:
                        try:
                            message = await websocket.recv()
                            _LOGGER.debug("Received message: %s", message)
                            # Process the message and update entity states
                            match message:
                                case bytes():
                                    await self._process_message(message.decode("utf-8"))
                                case str():
                                    await self._process_message(message)

                        except websockets.exceptions.ConnectionClosed:
                            await self._emit(ConnectionStatus(connected=False))

                            break
                        await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except BaseException:
                # Set device as unavailable when connection attempt fails
                await self._emit(ConnectionStatus(connected=False))
                _LOGGER.exception("Lost connection to: %s", self.host)
            # Wait before trying to reconnect
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break

    async def disconnect(self) -> None:
        """Stop the websocket client."""
        self._trying_to_connect = False
        if self._ws_task is not None:
            self._ws_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._ws_task

        if self._websocket is not None:
            await self._websocket.close()
            self._websocket = None
        await self._emit(ConnectionStatus(connected=False))

    async def _process_message(self, message: str) -> None:
        """Process a message from the device."""
        try:
            data = json.loads(message)

            # Handle reset message - device wants to be removed
            match data.get("type"):
                case "device_reset":
                    _LOGGER.info("device_reset")
                    return
                case "state":
                    # Handle state updates
                    state_value = float(data.get("value", 0))
                    # Find the entity directly from the device_info
                    await self._emit(StateChange(state_value))
                case "information":
                    info_message = data.get("value")
                    information = DeviceInformation(**info_message)
                    _LOGGER.debug("information received %s", information)
                    await self._emit(
                        InformationUpdate(
                            InformationData.convert_device_information_to_data(
                                information
                            )
                        )
                    )
                case "settings":
                    settings = data.get("value")
                    settings = Settings(**settings)
                    await self._emit(
                        SettingsUpdate(settings=await self._parse_settings(settings))
                    )
                case "ack":
                    _LOGGER.debug("Ack received?")
                case unknown:
                    _LOGGER.error("unknown data received %s", unknown)

        except json.JSONDecodeError:
            _LOGGER.exception("Invalid JSON received %s", unknown)
        except Exception:
            _LOGGER.exception("Error processing message %s", message)

    async def set_brightness(self, value: float) -> None:
        """
        Set the brightness level of the device.

        Parameters
        ----------
        value : float
            The brightness value between 0.0 (off) and 1.0 (full brightness).

        Raises
        ------
        ValueError
            If the brightness value is not between 0 and 1.

        """
        if not 0 <= value <= 1:
            msg = f"Brightness value must be between 0 and 1, got {value}"
            raise ValueError(msg)
        await self.send_command({"type": "state", "value": value})

    async def toggle(self) -> None:
        """Toggle the device state between on and off."""
        await self.send_command({"type": "state", "value": -1})

    async def turn_off(self) -> None:
        """Turn off the device."""
        if self._is_version_compatible(self._version, "1.1.8"):
            await self.send_command({"type": "state", "on": False})
        else:
            await self.send_command({"type": "state", "value": 0})

    async def turn_on(self) -> None:
        """Turn on the device."""
        if self._is_version_compatible(self._version, "1.1.8"):
            await self.send_command({"type": "state", "on": True})
        else:
            await self.send_command({"type": "state", "value": -1})

    async def send_command(
        self,
        command: dict[str, Any],
        retries: int = 3,
    ) -> None:
        """
        Send a command to the device via WebSocket.

        This method serializes the command dictionary to JSON and sends it through
        the WebSocket connection. It handles connection errors and updates the
        connection status accordingly.

        Args:
            command: A dictionary containing the command data to send to the device.
            timeout_seconds: Maximum time in seconds to wait for the send operation.
            retries: Number of retry attempts if the command fails to send.

        Returns:
            None

        Raises:
            NotConnectedError: If there is no active WebSocket connection.
            TimeoutError: If the command send operation times out.

        """
        if self._websocket is None and not self._trying_to_connect:
            _LOGGER.error(
                "Cannot send command to %s - Please connect() first",
                self.host,
            )
            raise NotConnectedError

        command_str = json.dumps(command)
        last_exception: Exception | None = None

        for attempt in range(1, retries + 1):
            try:
                _LOGGER.debug(
                    "Sending command to %s (attempt %d/%d): %s",
                    self.host,
                    attempt,
                    retries,
                    command_str,
                )
                if self._websocket:
                    await self._websocket.send(command_str)
            except websockets.exceptions.ConnectionClosedError as err:
                last_exception = err
                _LOGGER.exception(
                    "Failed to send command to %s - connection closed: %s %s",
                    self.host,
                    err.code,
                    err.reason,
                )
                # Mark entity as unavailable when command fails due to connection
                await self._emit(ConnectionStatus(connected=False))
            except websockets.exceptions.ConnectionClosedOK as err:
                last_exception = err
                _LOGGER.exception(
                    "Failed to send command to %s - connection closed due to : %s %s",
                    self.host,
                    err.code,
                    err.reason,
                )
                # Mark entity as unavailable when command fails due to connection
                await self._emit(ConnectionStatus(connected=False))
                raise NotConnectedError from err
            except Exception as err:
                last_exception = err
                _LOGGER.exception(
                    "Failed to send command to %s (attempt %d/%d)",
                    self.host,
                    attempt,
                    retries,
                )
                await self._emit(ConnectionStatus(connected=False))
            else:
                _LOGGER.info(
                    "Command %s sent successfully to %s", command_str, self.host
                )
                return

            if attempt < retries:
                await asyncio.sleep(0.5 * (2**attempt))  # (exponential backoff)

        _LOGGER.error(
            "Failed to send command to %s after %d attempts", self.host, retries
        )
        if last_exception:
            raise last_exception

    async def _parse_settings(self, settings: Settings) -> list[Setting]:
        settings_list: list[Setting] = []
        if settings.disable_433 is not None:
            settings_list.append(
                OnOffSetting(
                    param_key="disable_433",
                    name="433Mhz",
                    off_value=1,
                    on_value=0,
                    current=settings.disable_433,
                )
            )
        if settings.disable_physical_button is not None:
            settings_list.append(
                OnOffSetting(
                    param_key="disable_physical_button",
                    name="Physical Button",
                    off_value=1,
                    on_value=0,
                    current=settings.disable_physical_button,
                )
            )
        if settings.disable_led is not None:
            settings_list.append(
                OnOffSetting(
                    param_key="disable_led",
                    name="Led",
                    off_value=1,
                    on_value=0,
                    current=settings.disable_led,
                )
            )
        if settings.diy_mode is not None:
            settings_list.append(
                OnOffSetting(
                    param_key="diy_mode",
                    name="Cloud Access",
                    off_value=1,
                    on_value=0,
                    current=settings.diy_mode,
                )
            )
        return settings_list

    async def update_setting(self, settings: dict[str, Any]) -> None:
        """Update device settings via REST API."""
        url = f"http://{self.host}:3000/settings"
        try:
            async with (
                aiohttp.ClientSession() as session,
                session.post(url, json=settings) as response,
            ):
                response.raise_for_status()
                _LOGGER.debug("Updated settings at %s with %s", url, settings)
        except:
            _LOGGER.exception("Failed to update settings at %s", url)
            raise

    async def get_settings(self) -> list[Setting]:
        """Fetch device settings via REST API."""
        url = f"http://{self.host}:3000/settings"
        try:
            async with aiohttp.ClientSession() as session, session.get(url) as response:
                response.raise_for_status()
                json_resp = await response.json()
                return await self._parse_settings(Settings(**json_resp))
        except Exception:
            _LOGGER.exception("Failed to fetch settings from %s", url)
            raise

    async def get_info(self) -> InformationUpdate:
        """Fetch device information via REST API."""
        url = f"http://{self.host}:3000/info"
        try:
            async with aiohttp.ClientSession() as session, session.get(url) as response:
                response.raise_for_status()
                information = DeviceInformation(**await response.json())
                self.info_data = InformationData.convert_device_information_to_data(
                    information
                )
                return InformationUpdate(self.info_data)
        except:
            _LOGGER.exception("Failed to fetch device information from %s:", url)
            raise
