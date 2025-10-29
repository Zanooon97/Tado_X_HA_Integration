from homeassistant.helpers import config_entry_oauth2_flow
from .const import DOMAIN

class TadoXFlowHandler(config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN):
    """Handle the OAuth2 flow."""

    DOMAIN = DOMAIN

    async def async_oauth_create_entry(self, data):
        return self.async_create_entry(title="Tado X Account", data=data)
