import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)

class TadoXApi:
    def __init__(self, session: aiohttp.ClientSession, token: str):
        self._session = session
        self._token = token

    async def async_get_me(self):
        """Hole Benutzerinformationen von Tado."""
        url = "https://api.tado.com/v2/me"
        headers = {"Authorization": f"Bearer {self._token}"}
        async with self._session.get(url, headers=headers) as resp:
            data = await resp.json()
            _LOGGER.info("TadoX Benutzerinfo: %s", data)
            return data

    async def async_get_home(self, home_id: int):
        """Hole Home-Daten (Geräte, Räume, etc.)."""
        url = f"https://api.tado.com/v2/homes/{home_id}"
        headers = {"Authorization": f"Bearer {self._token}"}
        async with self._session.get(url, headers=headers) as resp:
            data = await resp.json()
            _LOGGER.info("TadoX Home %s Daten: %s", home_id, data)
            return data
