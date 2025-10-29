from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session

async def async_get_token(config_entry, hass):
    oauth_session = OAuth2Session(hass, config_entry)
    token = await oauth_session.async_ensure_token_valid()
    return token["access_token"]
