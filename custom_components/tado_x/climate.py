from __future__ import annotations

import logging

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVACMode,
    ClimateEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_HOME_ID

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tado X climate entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    api = data["api"]
    home_id = entry.data[CONF_HOME_ID]
    rooms = await api.async_get_rooms_devices(home_id)
    entities = []
    for room in rooms:
        room_id = room.get("id") or room.get("serialNo")
        if room_id is None:
            continue
        name = room.get("name") or "Tado X Climate"
        current = room.get("current") or room.get("currentTemp") or room.get("currentTemperature")
        target = room.get("target") or room.get("targetTemp") or room.get("targetTemperature")
        entities.append(TadoXClimate(api, room_id, name, current, target))
    async_add_entities(entities)


class TadoXClimate(ClimateEntity):
    """Representation of a Tado X climate device."""

    _attr_hvac_mode = HVACMode.HEAT
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, api, room_id: str, name: str, current: float | None, target: float | None) -> None:
        """Initialize the climate device."""
        self.api = api
        self._room_id = room_id
        self._attr_unique_id = f"{room_id}_climate"
        self._attr_name = name
        self._attr_target_temperature = target
        self._attr_current_temperature = current

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
