"""Config flow for Tado X integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
import aiohttp

from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client

from .const import (
    DOMAIN,
    CONF_REFRESH_TOKEN,
    CONF_HOME_ID,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
)

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_REFRESH_TOKEN): str,
        vol.Required(CONF_HOME_ID): str,
        vol.Required(CONF_CLIENT_ID): str,
        vol.Required(CONF_CLIENT_SECRET): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    session = aiohttp_client.async_get_clientsession(hass)
    token_payload = {
        "grant_type": "refresh_token",
        "client_id": data[CONF_CLIENT_ID],
        "client_secret": data[CONF_CLIENT_SECRET],
        "refresh_token": data[CONF_REFRESH_TOKEN],
        "scope": "home.user",
    }
    try:
        resp = await session.post("https://auth.tado.com/oauth/token", data=token_payload, timeout=10)
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

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
                
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pragma: no cover - unexpected
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                for entry in self._async_current_entries():
                    if entry.data.get(CONF_HOME_ID) == user_input[CONF_HOME_ID]:
                        self.hass.config_entries.async_update_entry(entry, data=user_input)
                        await self.hass.config_entries.async_reload(entry.entry_id)
                        return self.async_abort(reason="reauth_successful")
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
