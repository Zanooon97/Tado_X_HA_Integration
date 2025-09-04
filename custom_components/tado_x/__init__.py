"""Tado X integration setup."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client

from .api import TadoXApi
from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tado X from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    session = aiohttp_client.async_get_clientsession(hass)
    api = TadoXApi(hass, entry, session)
    await api.async_refresh_token()

    hass.data[DOMAIN][entry.entry_id] = {**entry.data, "api": api}
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Tado X config entry."""
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True
