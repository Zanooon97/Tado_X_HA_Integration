from homeassistant.helpers import config_entry_oauth2_flow
import logging
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class TadoXFlowHandler(config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN):
    """Handle den OAuth2 Login-Flow für Tado X."""

    DOMAIN = DOMAIN

    @property
    def logger(self):
        """Pflicht-Methode: gibt den Logger zurück."""
        return _LOGGER

    async def async_oauth_create_entry(self, data):
        """Wird aufgerufen, wenn der Login erfolgreich war."""
        return self.async_create_entry(
            title="Tado X Account",
            data=data,
    
        )
