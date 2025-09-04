from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
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
    rooms = data.get("rooms", {})
    entities = [
        TadoXOffsetNumber(api, info) for info in rooms.values()
    ]
    async_add_entities(entities)


class TadoXOffsetNumber(NumberEntity):
    """Entity to control the temperature offset of a Tado X device."""

    _attr_native_min_value = -5.0
    _attr_native_max_value = 5.0
    _attr_native_step = 0.1

    def __init__(self, api, info: dict[str, Any]) -> None:
        """Initialize the offset number."""
        self.api = api
        self._serial = info.get("serial")
        room_name = info.get("name")
        self._attr_name = (
            f"{room_name} Temperature Offset" if room_name else "Temperature Offset"
        )
        if self._serial:
            self._attr_unique_id = f"{self._serial}_temperature_offset"
        else:
            self._attr_unique_id = None
        self._attr_native_value = None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._serial)} if self._serial else None,
            manufacturer="tado°",
            name=info.get("name"),
            model=info.get("model"),
            sw_version=info.get("firmware"),
        )

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
