# Tado X Home Assistant Integration

This custom component integrates Tado devices using a refresh token and home ID. The config flow validates your credentials against the Tado API and prevents duplicate entries.

## Installation

### HACS
1. In Home Assistant, open HACS and add this repository (`Zanooon97/Tado_X_HA_Integration`) as a custom integration.
2. Install **Tado X Integration** from HACS.
3. Restart Home Assistant and add the integration via *Einstellungen → Geräte & Dienste*.

### Manuelle Installation
1. Kopiere den Ordner `custom_components/tado_x` in dein Home Assistant Konfigurationsverzeichnis `custom_components`.
2. Starte Home Assistant neu und richte die Integration über *Einstellungen → Geräte & Dienste* ein.

## Erforderliche API-Daten

Für die Einrichtung werden folgende Daten benötigt:

- **Refresh Token** – OAuth2 `refresh_token` aus deinem Tado-Konto.
- **Home ID** – eindeutige ID deines Tado-Zuhauses.

## Beispielkonfiguration

```yaml
# configuration.yaml
tado_x:
  refresh_token: "DEIN_REFRESH_TOKEN"
  home_id: 123456
```

Alternativ kann die Integration vollständig über die Benutzeroberfläche hinzugefügt werden.

## Ressourcen

- [Home Assistant Community Thread](https://community.home-assistant.io/t/tado-x-home-assistant-integration/)
- [Tado API Dokumentation](https://developer.tado.com/)
