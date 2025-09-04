# Tado X Home Assistant Integration

This custom component integrates Tado devices using the OAuth2 device authorization flow and a home ID. The config flow validates your credentials against the Tado API and prevents duplicate entries.

## Installation

### HACS
1. In Home Assistant, open HACS and add this repository (`Zanooon97/Tado_X_HA_Integration`) as a custom integration.
2. Install **Tado X Integration** from HACS.
3. Restart Home Assistant and add the integration via *Einstellungen → Geräte & Dienste*.

### Manuelle Installation
1. Kopiere den Ordner `custom_components/tado_x` in dein Home Assistant Konfigurationsverzeichnis `custom_components`.
2. Starte Home Assistant neu und richte die Integration über *Einstellungen → Geräte & Dienste* ein.

## Erforderliche API-Daten

Für die Einrichtung wird lediglich die **Home ID** benötigt.

## Geräteautorisierung

1. Füge in Home Assistant die Integration *Tado X Integration* hinzu.
2. Ein Dialog zeigt `verification_uri` und `user_code` an.
3. Öffne den Link im Browser, melde dich bei Tado an und gib den Code ein.
4. Kehre zu Home Assistant zurück und gib deine `home_id` ein.
5. Die erhaltenen Tokens werden im Config Entry gespeichert und bei Bedarf automatisch aktualisiert. Eine manuelle Tokenverwaltung ist nicht erforderlich.

## Beispielkonfiguration

```yaml
# configuration.yaml
tado_x:
  home_id: 123456
```

Alternativ kann die Integration vollständig über die Benutzeroberfläche hinzugefügt werden.

## Ressourcen

- [Home Assistant Community Thread](https://community.home-assistant.io/t/tado-x-home-assistant-integration/)
- [Tado API Dokumentation](https://developer.tado.com/)
