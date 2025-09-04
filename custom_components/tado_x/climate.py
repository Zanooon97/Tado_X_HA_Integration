from __future__ import annotations

import logging

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVACMode,
    ClimateEntityFeature,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigType,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tado X climate entity."""
    data = hass.data[DOMAIN][entry.entry_id]
    api = data["api"]
    serial = data["serial"]
    async_add_entities([TadoXClimate(api, serial)])


class TadoXClimate(ClimateEntity):
    """Representation of a Tado X climate device."""

    _attr_hvac_mode = HVACMode.HEAT
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, api, serial: str) -> None:
        """Initialize the climate device."""
        self.api = api
        self._serial = serial
        self._attr_unique_id = f"{serial}_climate"
        self._attr_name = "Tado X Climate"
        self._attr_target_temperature = None
        self._attr_current_temperature = None

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        await self.api.async_set_temperature(self._serial, temperature)
        self._attr_target_temperature = temperature
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Fetch new state data for the climate entity."""
        try:
            data = await self.api.async_get_temperature(self._serial)
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error("Error fetching climate data for %s: %s", self._serial, err)
            return
        if data:
            self._attr_current_temperature = data.get("current")
            self._attr_target_temperature = data.get("target")
