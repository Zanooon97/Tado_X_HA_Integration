"""Climate platform for Tado X."""
from __future__ import annotations

from homeassistant.components.climate import ClimateEntity, HVACMode
from homeassistant.const import TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigType,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tado X climate entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([TadoXClimate(data)])


class TadoXClimate(ClimateEntity):
    """Representation of a Tado X climate entity."""

    _attr_temperature_unit = TEMP_CELSIUS
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]

    def __init__(self, data: dict) -> None:
        """Initialize the climate device."""
        self._data = data
        self._attr_name = data.get("name", "Tado X Climate")
        self._attr_unique_id = f"{data.get('serial', 'tado_x')}_climate"

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        return self._data.get("mode", HVACMode.OFF)

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._data.get("temperature")

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        return {"heating_power": self._data.get("heatingPower")}
