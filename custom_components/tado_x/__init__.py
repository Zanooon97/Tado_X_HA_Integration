"""Tado X integration setup."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import TadoXApi
from .const import CONF_HOME_ID, DEFAULT_SCAN_INTERVAL, DOMAIN, PLATFORMS


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tado X from a config entry."""
    session = aiohttp_client.async_get_clientsession(hass)
    api = TadoXApi(hass, entry, session)
    await api.async_refresh_token()
    home_id = int(entry.data[CONF_HOME_ID])

    rooms_data = await api.async_get_rooms_devices(home_id)
    rooms_list = rooms_data.get("rooms") if isinstance(rooms_data, dict) else rooms_data
    rooms: dict[str, dict[str, str | float | None]] = {}
    for room in rooms_list or []:
        room_id = str(
            room.get("id") or room.get("serialNo") or room.get("serial")
        )
        if not room_id:
            continue
        room_name = room.get("name")
        current = (
            room.get("current")
            or room.get("currentTemp")
            or room.get("currentTemperature")
        )
        target = (
            room.get("target")
            or room.get("targetTemp")
            or room.get("targetTemperature")
        )
        humidity = room.get("humidity")
        heating_power = room.get("heatingPower")

        device = (room.get("devices") or [None])[0] or {}
        serial = device.get("serialNo") or device.get("serial")
        model = device.get("model") or device.get("type")
        firmware = device.get("firmware") or device.get("firmwareVersion")
        battery_state = device.get("batteryState") or room.get("batteryState")

        rooms[room_id] = {
            "serial": serial,
            "model": model,
            "firmware": firmware,
            "name": room_name,
            "current": current,
            "target": target,
            "humidity": humidity,
            "heatingPower": heating_power,
            "batteryState": battery_state,
        }

    async def _async_update_data() -> dict[str, dict[str, Any]]:
        data: dict[str, dict[str, Any]] = {}
        for room_id in rooms:
            try:
                data[room_id] = await api.async_get_temperature(room_id)
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.error("Error updating room %s: %s", room_id, err)
        return data

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="tado_x",
        update_method=_async_update_data,
        update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "rooms": rooms,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Tado X config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
