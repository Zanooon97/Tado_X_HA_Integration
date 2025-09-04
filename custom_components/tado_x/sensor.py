from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigType,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tado X sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    api = data["api"]
    rooms = data.get("rooms", {})
    entities: list[SensorEntity] = []

    for room_id, info in rooms.items():
        if info.get("humidity") is not None:
            entities.append(TadoXHumiditySensor(api, room_id, info))
        if info.get("heatingPower") is not None:
            entities.append(TadoXHeatingPowerSensor(api, room_id, info))
        if info.get("batteryState") is not None:
            entities.append(TadoXBatterySensor(api, room_id, info))

    async_add_entities(entities)


class TadoXBaseSensor(SensorEntity):
    """Base class for Tado X sensors."""

    def __init__(self, api, room_id: str, info: dict[str, Any]) -> None:
        self.api = api
        self._room_id = room_id
        self._serial = info.get("serial")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._serial)} if self._serial else None,
            manufacturer="tado°",
            name=info.get("name"),
            model=info.get("model"),
            sw_version=info.get("firmware"),
        )

    async def async_update(self) -> None:
        try:
            data = await self.api.async_get_temperature(self._room_id)
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error("Error updating sensor for %s: %s", self._room_id, err)
            return
        if data:
            self._process_data(data)

    def _process_data(self, data: dict[str, Any]) -> None:
        """Handle updated data for the sensor."""
        raise NotImplementedError


class TadoXHumiditySensor(TadoXBaseSensor):
    """Sensor for room humidity."""

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, api, room_id: str, info: dict[str, Any]) -> None:
        super().__init__(api, room_id, info)
        room_name = info.get("name")
        self._attr_name = f"{room_name} Humidity" if room_name else "Humidity"
        self._attr_unique_id = f"{room_id}_humidity"
        self._attr_native_value = info.get("humidity")

    def _process_data(self, data: dict[str, Any]) -> None:
        self._attr_native_value = data.get("humidity")


class TadoXHeatingPowerSensor(TadoXBaseSensor):
    """Sensor for heating power percentage."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, api, room_id: str, info: dict[str, Any]) -> None:
        super().__init__(api, room_id, info)
        room_name = info.get("name")
        self._attr_name = (
            f"{room_name} Heating Power" if room_name else "Heating Power"
        )
        self._attr_unique_id = f"{room_id}_heating_power"
        self._attr_native_value = info.get("heatingPower")

    def _process_data(self, data: dict[str, Any]) -> None:
        self._attr_native_value = data.get("heatingPower")


class TadoXBatterySensor(TadoXBaseSensor):
    """Sensor for reporting the battery state of a device."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, api, room_id: str, info: dict[str, Any]) -> None:
        super().__init__(api, room_id, info)
        room_name = info.get("name")
        self._attr_name = (
            f"{room_name} Battery State" if room_name else "Battery State"
        )
        self._attr_unique_id = f"{room_id}_battery_state"
        self._attr_native_value = info.get("batteryState")

    def _process_data(self, data: dict[str, Any]) -> None:
        self._attr_native_value = data.get("batteryState")
