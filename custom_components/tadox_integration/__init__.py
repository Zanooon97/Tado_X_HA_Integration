import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session
from .const import DOMAIN, UPDATE_INTERVAL, API_BASE
from .api import TadoXApi

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry):
    session = async_get_clientsession(hass)
    oauth_session = OAuth2Session(hass, entry)
    await oauth_session.async_ensure_token_valid()
    token = oauth_session.token["access_token"]

    api = TadoXApi(session, token)

    async def async_update_data():
        """Hole und logge Tado-Daten."""
        try:
            user = await api.async_get_me()
            home_id = user["homes"][0]["id"]
            await api.async_get_home(home_id)
        except Exception as e:
            _LOGGER.error("Fehler beim Abrufen der Tado-Daten: %s", e)
            raise UpdateFailed from e

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
