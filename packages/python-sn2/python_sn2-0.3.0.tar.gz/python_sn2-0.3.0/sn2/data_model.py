"""Data models for device information and settings."""

from dataclasses import dataclass
from typing import Any

from .constants import LIGHT_MODELS


@dataclass(frozen=True, slots=True)
class InformationData:
    """Device information data container."""

    model: str
    sw_version: str | None
    hw_version: str | None
    name: str
    wifi_dbm: int | None
    wifi_ssid: str | None
    unique_id: str
    dimmable: bool

    @staticmethod
    def from_device_dict(
        info: dict[str, Any],
    ) -> "InformationData":
        """Create InformationData from a dict object."""
        uniq_id = info.get("lcu")
        if uniq_id is None:
            msg = "lcu (unique id) cannot be None, broken/corrupt device?"
            raise ValueError(msg)
        hwm = info.get("hwm")
        if hwm is None:
            msg = "hwm (model) cannot be None, broken/corrupt device?"
            raise ValueError(msg)
        name = info.get("n")
        if name is None:
            msg = "n (name) cannot be None, broken/corrupt device?"
            raise ValueError(msg)
        hw_version = info.get("nhwv")
        return InformationData(
            model=hwm,
            sw_version=info.get("nswv"),
            hw_version=str(hw_version) if hw_version is not None else None,
            name=name,
            wifi_dbm=info.get("wr"),
            wifi_ssid=info.get("ws"),
            unique_id=uniq_id,
            dimmable=hwm in LIGHT_MODELS,
        )


@dataclass(frozen=True, slots=True)
class Settings:
    """Represents device settings with various configuration attributes."""

    name: str | None = None
    disable_physical_button: int | None = None
    disable_433: int | None = None
    disable_led: int | None = None
    diy_mode: int | None = None

    @staticmethod
    def from_device_dict(data: dict) -> "Settings":
        """Create a Settings instance from a device dictionary."""
        return Settings(
            name=data.get("name"),
            disable_physical_button=data.get("disable_physical_button"),
            disable_433=data.get("disable_433"),
            disable_led=data.get("disable_led"),
            diy_mode=data.get("diy_mode"),
        )
