"""Tado X API client."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_HOME_ID

API_BASE = "https://my.tado.com/api/v2"
HOPS_BASE = "https://hops.tado.com"
TOKEN_URL = "https://login.tado.com/oauth2/token"
CLIENT_ID = "1bb50063-6b0c-4d11-bd99-387f4a91cc46"

_LOGGER = logging.getLogger(__name__)


class TadoXApi:
    """Simple API wrapper for Tado X."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, session: aiohttp.ClientSession) -> None:
        """Initialize the API wrapper."""
        self._hass = hass
        self._entry = entry
        self._session = session
        self._access_token: str | None = entry.data.get("access_token")
        self._refresh_token: str | None = entry.data.get("refresh_token")

    async def async_refresh_token(self) -> None:
        """Refresh the OAuth token using the refresh token."""
        if not self._refresh_token:
            raise RuntimeError("No refresh token available")

        payload = {
            "client_id": CLIENT_ID,
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
        }

        async with self._session.post(TOKEN_URL, data=payload) as resp:
            resp.raise_for_status()
            data = await resp.json()

        self._access_token = data.get("access_token")
        self._refresh_token = data.get("refresh_token", self._refresh_token)

        # Persist new tokens in the config entry
        new_data = {**self._entry.data, "access_token": self._access_token, "refresh_token": self._refresh_token}
        self._hass.config_entries.async_update_entry(self._entry, data=new_data)

    async def _async_request(self, method: str, url: str, **kwargs: Any) -> Any:
        """Make an authenticated request and handle token refresh on 401."""
        headers = kwargs.pop("headers", {})
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"

        try:
            async with self._session.request(method, url, headers=headers, **kwargs) as resp:
                if resp.status == 401:
                    _LOGGER.debug("401 received, refreshing token")
                    await self.async_refresh_token()
                    headers["Authorization"] = f"Bearer {self._access_token}"
                    async with self._session.request(method, url, headers=headers, **kwargs) as resp2:
                        resp2.raise_for_status()
                        return await resp2.json()
                resp.raise_for_status()
                return await resp.json()
        except aiohttp.ClientError as err:
            _LOGGER.error("API request error for %s %s: %s", method, url, err)
            raise

    async def async_get_rooms_devices(self, home_id: int) -> Any:
        """Return rooms with their devices for a home."""
        url = f"{API_BASE}/homes/{home_id}/zones"
        return await self._async_request("GET", url)

    async def async_get_devices(self, home_id: int) -> Any:
        """Return devices for a home."""
        url = f"{API_BASE}/homes/{home_id}/devices"
        return await self._async_request("GET", url)

    async def async_get_temperature(self, serial: str) -> dict[str, Any] | None:
        """Retrieve current and target temperatures for a device."""
        home_id = self._entry.data.get(CONF_HOME_ID)
        url = f"{HOPS_BASE}/homes/{home_id}/rooms/{serial}"
        try:
            data = await self._async_request("GET", url)
        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching temperature for %s: %s", serial, err)
            raise
        return {
            "current": data.get("current")
            or data.get("currentTemp")
            or data.get("currentTemperature"),
            "target": data.get("target")
            or data.get("targetTemp")
            or data.get("targetTemperature"),
        }

    async def async_set_temperature(self, serial: str, value: float) -> None:
        """Set a new target temperature for a device."""
        home_id = self._entry.data.get(CONF_HOME_ID)
        url = f"{HOPS_BASE}/homes/{home_id}/rooms/{serial}"
        payload = {"target": value}
        try:
            await self._async_request("PUT", url, json=payload)
        except aiohttp.ClientError as err:
            _LOGGER.error("Error setting temperature for %s: %s", serial, err)
            raise

    async def async_get_temperature_offset(self, device_id: str) -> float | None:
        """Retrieve the current temperature offset for a device."""
        url = f"{API_BASE}/devices/{device_id}/temperatureOffset"
        data = await self._async_request("GET", url)
        return data.get("celsius")

    async def async_update_temperature_offset(self, device_id: str, offset: float) -> Any:
        """Update the temperature offset for a device."""
        url = f"{API_BASE}/devices/{device_id}/temperatureOffset"
        payload = {"celsius": offset}
        return await self._async_request("POST", url, json=payload)
