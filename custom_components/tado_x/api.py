"""Tado X API client."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

API_BASE = "https://my.tado.com/api/v2"
TOKEN_URL = "https://login.tado.com/oauth2/token"

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
        self._client_id: str | None = entry.data.get("client_id")
        self._client_secret: str | None = entry.data.get("client_secret")

    async def async_refresh_token(self) -> None:
        """Refresh the OAuth token using the refresh token."""
        if not self._refresh_token:
            raise RuntimeError("No refresh token available")

        payload = {
            "client_id": self._client_id,
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
        }
        if self._client_secret:
            payload["client_secret"] = self._client_secret

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

    async def async_get_rooms_devices(self, home_id: int) -> Any:
        """Return rooms with their devices for a home."""
        url = f"{API_BASE}/homes/{home_id}/zones"
        return await self._async_request("GET", url)

    async def async_get_devices(self, home_id: int) -> Any:
        """Return devices for a home."""
        url = f"{API_BASE}/homes/{home_id}/devices"
        return await self._async_request("GET", url)

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
