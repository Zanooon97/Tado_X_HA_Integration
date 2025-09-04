"""Config flow for Tado X integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client

from .const import CONF_HOME_ID, CONF_REFRESH_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)

CLIENT_ID = "1bb50063-6b0c-4d11-bd99-387f4a91cc46"
DEVICE_AUTHORIZE_URL = "https://login.tado.com/oauth2/device_authorize"
TOKEN_URL = "https://login.tado.com/oauth2/token"

HOME_ID_SCHEMA = vol.Schema({vol.Required(CONF_HOME_ID): str})


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    session = aiohttp_client.async_get_clientsession(hass)
    token_payload = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "refresh_token": data[CONF_REFRESH_TOKEN],
    }
    try:
        resp = await session.post(TOKEN_URL, data=token_payload, timeout=10)
    except aiohttp.ClientError as err:  # pragma: no cover - network failure
        raise CannotConnect from err
    if resp.status != 200:
        raise InvalidAuth
    token = await resp.json()

    headers = {"Authorization": f"Bearer {token['access_token']}"}
    try:
        dev_resp = await session.get(
            f"https://my.tado.com/api/v2/homes/{data[CONF_HOME_ID]}/devices",
            headers=headers,
            timeout=10,
        )
    except aiohttp.ClientError as err:  # pragma: no cover - network failure
        raise CannotConnect from err

    if dev_resp.status != 200:
        raise InvalidAuth

    devices = await dev_resp.json()
    return {"title": f"Tado {data[CONF_HOME_ID]}", "devices": devices}


class TadoXConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tado X."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self._device_auth: dict[str, Any] | None = None
        self._tokens: dict[str, Any] | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Start device authorization."""
        session = aiohttp_client.async_get_clientsession(self.hass)
        payload = {"client_id": CLIENT_ID, "scope": "offline_access"}
        try:
            resp = await session.post(DEVICE_AUTHORIZE_URL, data=payload, timeout=10)
            resp.raise_for_status()
        except aiohttp.ClientError as err:  # pragma: no cover - network failure
            _LOGGER.error("Device authorize failed: %s", err)
            return self.async_abort(reason="cannot_connect")

        self._device_auth = await resp.json()
        return await self.async_step_authorize()

    async def async_step_authorize(self, user_input: dict[str, Any] | None = None):
        """Prompt user to authorize the device and fetch tokens."""
        assert self._device_auth is not None

        if user_input is None:
            schema = vol.Schema(
                {
                    vol.Required("user_code", default=self._device_auth["user_code"]): str,
                    vol.Required(
                        "verification_uri",
                        default=self._device_auth["verification_uri_complete"],
                    ): str,
                }
            )
            return self.async_show_form(step_id="authorize", data_schema=schema)

        session = aiohttp_client.async_get_clientsession(self.hass)
        payload = {
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": self._device_auth["device_code"],
            "client_id": CLIENT_ID,
        }
        try:
            resp = await session.post(TOKEN_URL, data=payload, timeout=10)
            data = await resp.json()
        except aiohttp.ClientError as err:  # pragma: no cover - network failure
            _LOGGER.error("Token exchange failed: %s", err)
            return self.async_abort(reason="cannot_connect")

        error = data.get("error")
        if resp.status != 200 or error in ("authorization_pending", "slow_down"):
            errors = {"base": "authorization_pending"}
            schema = vol.Schema(
                {
                    vol.Required("user_code", default=self._device_auth["user_code"]): str,
                    vol.Required(
                        "verification_uri",
                        default=self._device_auth["verification_uri_complete"],
                    ): str,
                }
            )
            return self.async_show_form(step_id="authorize", data_schema=schema, errors=errors)

        if error:
            return self.async_abort(reason="invalid_auth")

        self._tokens = data
        self._tokens["client_id"] = CLIENT_ID
        return await self.async_step_home_id()

    async def async_step_home_id(self, user_input: dict[str, Any] | None = None):
        """Ask for home id and create entry."""
        assert self._tokens is not None

        errors: dict[str, str] = {}
        if user_input is not None:
            data = {
                CONF_REFRESH_TOKEN: self._tokens["refresh_token"],
                CONF_HOME_ID: user_input[CONF_HOME_ID],
            }
            try:
                info = await validate_input(self.hass, data)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            else:
                entry_data = {
                    CONF_HOME_ID: user_input[CONF_HOME_ID],
                    CONF_REFRESH_TOKEN: self._tokens["refresh_token"],
                }
                for key, value in self._tokens.items():
                    if key not in entry_data:
                        entry_data[key] = value
                for entry in self._async_current_entries():
                    if entry.data.get(CONF_HOME_ID) == user_input[CONF_HOME_ID]:
                        self.hass.config_entries.async_update_entry(entry, data=entry_data)
                        await self.hass.config_entries.async_reload(entry.entry_id)
                        return self.async_abort(reason="reauth_successful")
                return self.async_create_entry(title=info["title"], data=entry_data)

        return self.async_show_form(step_id="home_id", data_schema=HOME_ID_SCHEMA, errors=errors)


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""

