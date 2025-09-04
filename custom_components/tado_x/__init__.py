"""Tado X integration setup."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client

from .api import TadoXApi
from .const import CONF_HOME_ID, DOMAIN, PLATFORMS


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tado X from a config entry."""
    session = aiohttp_client.async_get_clientsession(hass)
    api = TadoXApi(hass, entry, session)
    await api.async_refresh_token()
    home_id = int(entry.data[CONF_HOME_ID])

    rooms_data = await api.async_get_rooms_devices(home_id)
    rooms: dict[str, dict[str, str | float | None]] = {}
    for room in rooms_data or []:
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

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"api": api, "rooms": rooms}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Tado X config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
