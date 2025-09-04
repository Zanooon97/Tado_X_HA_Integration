# Tado X Home Assistant Integration

Custom integration to control Tado heating devices from Home Assistant.

## Features

- Adds climate entities for each Tado zone.
- Provides number entities for adjustable parameters such as temperature offsets.
- Uses the Tado Web API.

## Installation

1. Ensure [HACS](https://hacs.xyz/) is installed in your Home Assistant setup.
2. In HACS, add this repository as a custom integration.
3. Install **Tado X** through HACS and restart Home Assistant.
4. Add the integration configuration to your `configuration.yaml`.

## Configuration

```yaml
# Example configuration.yaml
tado_x:
  username: YOUR_TADO_USERNAME
  password: YOUR_TADO_PASSWORD
  scan_interval: 30  # seconds
```

## Usage

After setup, Home Assistant exposes `climate` entities for every room and additional `number` entities for features like temperature offsets. Use these entities in automations, dashboards or scripts as any other Home Assistant entity.

## References

- Tado API documentation: <https://my.tado.com/api/v2>
- Community discussion thread: <https://community.home-assistant.io/t/tado-x-integration/>

