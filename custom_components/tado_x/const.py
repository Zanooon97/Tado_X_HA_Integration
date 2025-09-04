# custom_components/tado_x/const.py
from homeassistant.const import Platform

CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_HOME_ID = "home_id"

DOMAIN = "tado_x"
PLATFORMS = [Platform.CLIMATE, Platform.NUMBER]
DEFAULT_SCAN_INTERVAL = 30  # Sekunden, falls du zyklisch aktualisieren willst
