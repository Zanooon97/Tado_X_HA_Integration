"""Tado X API client."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed

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

        try:
            async with self._session.post(TOKEN_URL, data=payload) as resp:
                resp.raise_for_status()
                data = await resp.json()
        except aiohttp.ClientResponseError as err:
            _LOGGER.error(
                "Token refresh failed with status %s: %s", err.status, err.message
            )
            raise ConfigEntryAuthFailed("Token refresh failed") from err

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
        """Return rooms with their devices for a home.

        The raw rooms endpoint does not always include all telemetry such as
        humidity, heating power or the battery state.  This helper fetches the
        base room list, enriches it with detailed room information and merges
        available device data so the caller receives all relevant fields in one
        structure.
        """
        rooms_url = f"{HOPS_BASE}/homes/{home_id}/rooms"
        rooms = await self._async_request("GET", rooms_url)

        # Map devices by their serial number to easily merge additional
        # information (e.g. battery state) into the room structure.
        devices = await self.async_get_devices(home_id)
        device_map: dict[str, dict[str, Any]] = {}
        for device in devices or []:
            serial = device.get("serialNo") or device.get("serial")
            if serial:
                device_map[serial] = device

        for room in rooms or []:
            room_id = room.get("id") or room.get("serialNo")
            # Fetch detailed room information if important fields are missing.
            if any(
                room.get(field) is None
                for field in ("humidity", "heatingPower", "batteryState")
            ) and room_id is not None:
                try:
                    detail_url = f"{HOPS_BASE}/homes/{home_id}/rooms/{room_id}"
                    details = await self._async_request("GET", detail_url)
                except aiohttp.ClientError:
                    details = {}
                room.setdefault(
                    "current",
                    details.get("current")
                    or details.get("currentTemp")
                    or details.get("currentTemperature"),
                )
                room.setdefault(
                    "target",
                    details.get("target")
                    or details.get("targetTemp")
                    or details.get("targetTemperature"),
                )
                for field in ("humidity", "heatingPower", "batteryState"):
                    if field in details and room.get(field) is None:
                        room[field] = details.get(field)

            # Merge additional device info if available
            for dev in room.get("devices") or []:
                serial = dev.get("serialNo") or dev.get("serial")
                if serial and (info := device_map.get(serial)):
                    for key in ("batteryState", "model", "type", "firmware", "firmwareVersion"):
                        if dev.get(key) is None and info.get(key) is not None:
                            dev[key] = info.get(key)

            # Ensure battery state on room level if present on the first device
            if room.get("batteryState") is None:
                first_device = (room.get("devices") or [None])[0] or {}
                if first_device.get("batteryState") is not None:
                    room["batteryState"] = first_device.get("batteryState")

        return rooms

    async def async_get_devices(self, home_id: int) -> Any:
        """Return devices for a home."""
        url = f"{API_BASE}/homes/{home_id}/devices"
        return await self._async_request("GET", url)

    async def async_get_temperature(self, room_id: str) -> dict[str, Any] | None:
        """Retrieve room information including temperatures and other stats."""
        home_id = self._entry.data.get(CONF_HOME_ID)
        url = f"{HOPS_BASE}/homes/{home_id}/rooms/{room_id}"
        try:
            data = await self._async_request("GET", url)
        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching temperature for %s: %s", room_id, err)
            raise
        return {
            "current": data.get("current")
            or data.get("currentTemp")
            or data.get("currentTemperature"),
            "target": data.get("target")
            or data.get("targetTemp")
            or data.get("targetTemperature"),
            "humidity": data.get("humidity"),
            "heatingPower": data.get("heatingPower"),
            "batteryState": data.get("batteryState"),
        }

    async def async_set_temperature(self, room_id: str, value: float) -> None:
        """Set a new target temperature for a room."""
        home_id = self._entry.data.get(CONF_HOME_ID)
        url = f"{HOPS_BASE}/homes/{home_id}/rooms/{room_id}"
        payload = {"target": value}
        try:
            await self._async_request("PUT", url, json=payload)
        except aiohttp.ClientError as err:
            _LOGGER.error("Error setting temperature for %s: %s", room_id, err)
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
