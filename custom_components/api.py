import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)

class TadoXApi:
    def __init__(self, session: aiohttp.ClientSession, base_url: str):
        self._session = session
        self._base_url = base_url

    async def async_get_data(self):
        """Beispielhafter API-Aufruf an Tado X."""
        url = f"{self._base_url}/devices"
        try:
            async with self._session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    _LOGGER.error("TadoX API returned %s", resp.status)
                    return None
                data = await resp.json()
                _LOGGER.debug("Received data: %s", data)
                return data
        except Exception as e:
            _LOGGER.error("Error connecting to TadoX API: %s", e)
            return None
