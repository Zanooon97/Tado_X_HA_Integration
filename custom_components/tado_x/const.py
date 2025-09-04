# custom_components/tado_x/const.py
from homeassistant.const import Platform

DOMAIN = "tado_x"
PLATFORMS = [Platform.CLIMATE, Platform.NUMBER]
DEFAULT_SCAN_INTERVAL = 30  # Sekunden, falls du zyklisch aktualisieren willst
