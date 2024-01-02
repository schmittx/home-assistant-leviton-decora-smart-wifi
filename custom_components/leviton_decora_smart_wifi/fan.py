"""Support for Leviton Decora Smart Wi-Fi fan entities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.fan import (
    FanEntity,
    FanEntityDescription,
    FanEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LevitonEntity
from .const import (
    CONF_DEVICES,
    CONF_RESIDENCES,
    DATA_COORDINATOR,
    DOMAIN,
)

@dataclass
class LevitonFanEntityDescription(FanEntityDescription):
    """Class to describe a Leviton Decora Smart Wi-Fi fan entity."""


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a Leviton Decora Smart Wi-Fi fan entity based on a config entry."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    conf_residences = entry[CONF_RESIDENCES]
    conf_devices = entry[CONF_DEVICES]
    coordinator = entry[DATA_COORDINATOR]
    entities: list[LevitonFanEntity] = []

    for residence in coordinator.data:
        if residence.id in conf_residences:
            for device in residence.devices:
                if all(
                    [
                        device.id in conf_devices,
                        device.is_fan,
                    ]
                ):
                    entities.append(
                        LevitonFanEntity(
                            coordinator=coordinator,
                            residence_id=residence.id,
                            device_id=device.id,
                            entity_description=LevitonFanEntityDescription(
                                key=None,
                                name=None,
                            ),
                        )
                    )

    async_add_entities(entities)


class LevitonFanEntity(FanEntity, LevitonEntity):
    """Representation of a Leviton Decora Smart Wi-Fi fan entity."""

    entity_description: LevitonFanEntityDescription

    @property
    def is_on(self) -> bool:
        """Return True if entity is on."""
        return self.device.is_on

    @property
    def percentage(self) -> int:
        """Return the current speed percentage."""
        return self.device.brightness

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return int(self.device.max_level / self.device.min_level)

    @property
    def supported_features(self) -> FanEntityFeature:
        """Flag supported features."""
        if self.device.can_set_level:
            return FanEntityFeature.SET_SPEED
        return FanEntityFeature(0)

    def turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn the entity on."""
        self.device.turn_on()

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn the entity on."""
        await super().async_turn_on(percentage, preset_mode, **kwargs)
        await self.coordinator.async_request_refresh()

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        self.device.turn_off()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await super().async_turn_off(**kwargs)
        await self.coordinator.async_request_refresh()

    def set_percentage(self, percentage: int) -> None:
        """Set the speed of the fan, as a percentage."""
        self.device.set_speed(percentage)

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        await super().async_set_percentage(percentage)
        await self.coordinator.async_request_refresh()
