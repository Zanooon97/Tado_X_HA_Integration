from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity
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
    """Set up the Tado X offset number entity."""
    data = hass.data[DOMAIN][entry.entry_id]
    api = data["api"]
    serial = data["serial"]
    async_add_entities([TadoXOffsetNumber(api, serial)])


class TadoXOffsetNumber(NumberEntity):
    """Entity to control the temperature offset of a Tado X device."""

    _attr_name = "Temperature Offset"
    _attr_native_min_value = -5.0
    _attr_native_max_value = 5.0
    _attr_native_step = 0.1

    def __init__(self, api, serial: str) -> None:
        """Initialize the offset number."""
        self.api = api
        self._serial = serial
        self._attr_unique_id = f"{serial}_temperature_offset"
        self._attr_native_value = None

    async def async_set_value(self, value: float) -> None:
        """Update the offset value via the API."""
        await self.api.async_update_temperature_offset(self._serial, value)
        self._attr_native_value = value
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Fetch the latest offset from the API."""
        try:
            offset = await self.api.async_get_temperature_offset(self._serial)
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error(
                "Error fetching temperature offset for %s: %s", self._serial, err
            )
            return
        if offset is not None:
            self._attr_native_value = offset
