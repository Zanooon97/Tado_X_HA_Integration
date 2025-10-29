import asyncio
import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN, UPDATE_INTERVAL
from .api import TadoXApi

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry):
    session = async_get_clientsession(hass)
    api = TadoXApi(session, base_url="https://api.tado.com/x/v1")  # Beispiel-URL

    async def async_update_data():
        """Daten abrufen und loggen."""
        data = await api.async_get_data()
        if data is None:
            raise UpdateFailed("Fehler beim Abruf der TadoX-Daten.")
        _LOGGER.info("Tado X API Daten: %s", data)
        return data

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=UPDATE_INTERVAL),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    return True
