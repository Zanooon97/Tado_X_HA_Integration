from __future__ import annotations

import logging

from typing import Any

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVACMode,
    ClimateEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tado X climate entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    api = data["api"]
    rooms = data.get("rooms", {})
    entities = [
        TadoXClimate(api, room_id, info) for room_id, info in rooms.items()
    ]
    async_add_entities(entities)


class TadoXClimate(ClimateEntity):
    """Representation of a Tado X climate device."""

    _attr_hvac_mode = HVACMode.HEAT
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, api, room_id: str, info: dict[str, Any]) -> None:
        """Initialize the climate device."""
        self.api = api
        self._room_id = room_id
        self._attr_unique_id = f"{room_id}_climate"
        self._attr_name = info.get("name") or "Tado X Climate"
        self._attr_target_temperature = info.get("target")
        self._attr_current_temperature = info.get("current")
        self._humidity = info.get("humidity")
        self._heating_power = info.get("heatingPower")
        self._battery_state = info.get("batteryState")
        serial = info.get("serial")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)} if serial else None,
            manufacturer="tado°",
            name=info.get("name"),
            model=info.get("model"),
            sw_version=info.get("firmware"),
        )

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        await self.api.async_set_temperature(self._room_id, temperature)
        self._attr_target_temperature = temperature
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Fetch new state data for the climate entity."""
        try:
            data = await self.api.async_get_temperature(self._room_id)
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error("Error fetching climate data for %s: %s", self._room_id, err)
            return
        if data:
            self._attr_current_temperature = data.get("current")
            self._attr_target_temperature = data.get("target")
            self._humidity = data.get("humidity")
            self._heating_power = data.get("heatingPower")
            self._battery_state = data.get("batteryState")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes of the climate entity."""
        data = {}
        if self._humidity is not None:
            data["humidity"] = self._humidity
        if self._heating_power is not None:
            data["heating_power"] = self._heating_power
        if self._battery_state is not None:
            data["battery_state"] = self._battery_state
        return data
