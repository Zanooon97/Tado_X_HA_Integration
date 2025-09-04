"""Climate platform for Tado X devices."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import UnitOfTemperature


@dataclass
class TadoXAPI:  # placeholder for actual API client
    async def get_temperature(self) -> float:
        """Return current measured temperature."""
        raise NotImplementedError

    async def get_target_setpoint(self) -> float:
        """Return current target temperature setpoint."""
        raise NotImplementedError

    async def get_heating_power(self) -> float:
        """Return current heating power in percent."""
        raise NotImplementedError

    async def set_target_temperature(self, temperature: float) -> None:
        """Set new target temperature."""
        raise NotImplementedError


class TadoXClimate(ClimateEntity):
    """Representation of a Tado X climate zone."""

    _attr_hvac_modes = [HVACMode.HEAT]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 0.1

    def __init__(self, api: TadoXAPI) -> None:
        self._api = api
        self._attr_hvac_mode = HVACMode.HEAT
        self._attr_current_temperature: float | None = None
        self._attr_target_temperature: float | None = None
        self._heating_power: float | None = None

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature via API."""
        temperature = kwargs.get("temperature")
        if temperature is None:
            return
        await self._api.set_target_temperature(temperature)
        self._attr_target_temperature = temperature

    async def async_update(self) -> None:
        """Fetch updated data from the API."""
        self._attr_current_temperature = await self._api.get_temperature()
        self._attr_target_temperature = await self._api.get_target_setpoint()
        self._heating_power = await self._api.get_heating_power()

    @property
    def hvac_action(self) -> HVACAction | None:
        if self._heating_power is None:
            return None
        return HVACAction.HEATING if self._heating_power > 0 else HVACAction.IDLE

    @property
    def extra_state_attributes(self) -> dict[str, float | None]:
        return {"heatingPower": self._heating_power}
