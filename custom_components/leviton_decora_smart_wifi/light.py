"""Support for Leviton Decora Smart Wi-Fi light entities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
    LightEntityDescription,
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
class LevitonLightEntityDescription(LightEntityDescription):
    """Class to describe a Leviton Decora Smart Wi-Fi light entity."""


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a Leviton Decora Smart Wi-Fi light entity based on a config entry."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    conf_residences = entry[CONF_RESIDENCES]
    conf_devices = entry[CONF_DEVICES]
    coordinator = entry[DATA_COORDINATOR]
    entities: list[LevitonLightEntity] = []

    for residence in coordinator.data:
        if residence.id in conf_residences:
            for device in residence.devices:
                if all(
                    [
                        device.id in conf_devices,
                        device.is_light,
                    ]
                ):
                    entities.append(
                        LevitonLightEntity(
                            coordinator=coordinator,
                            residence_id=residence.id,
                            device_id=device.id,
                            entity_description=LevitonLightEntityDescription(
                                key=None,
                                name=None,
                            ),
                        )
                    )

    async_add_entities(entities)


class LevitonLightEntity(LightEntity, LevitonEntity):
    """Representation of a Leviton Decora Smart Wi-Fi light entity."""

    entity_description: LevitonLightEntityDescription

    @property
    def is_on(self) -> bool:
        """Return True if entity is on."""
        return self.device.is_on

    @property
    def brightness(self) -> int:
        """Return the brightness of this light between 0..255."""
        return int(self.device.brightness * 255 / 100)

    @property
    def color_mode(self) -> ColorMode:
        """Return the color mode of the light."""
        if self.device.can_set_level:
            return ColorMode.BRIGHTNESS
        return ColorMode.ONOFF

    @property
    def supported_color_modes(self) -> set[ColorMode]:
        """Flag supported color modes."""
        if self.device.can_set_level:
            return set([ColorMode.BRIGHTNESS])
        return set([ColorMode.ONOFF])

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        if ATTR_BRIGHTNESS in kwargs:
            self.device.set_brightness(int(kwargs[ATTR_BRIGHTNESS] * 100 / 255))
        else:
            self.device.turn_on()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await super().async_turn_on(**kwargs)
        await self.coordinator.async_request_refresh()

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        self.device.turn_off()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await super().async_turn_off(**kwargs)
        await self.coordinator.async_request_refresh()
