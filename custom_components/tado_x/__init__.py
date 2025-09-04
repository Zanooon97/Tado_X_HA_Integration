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
    devices = await api.async_get_devices(home_id)
    serial = devices[0].get("serialNo") if devices else None

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"api": api, "serial": serial}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Tado X config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
