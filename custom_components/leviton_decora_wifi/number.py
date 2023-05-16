"""Support for Leviton Decora Smart Wi-Fi number entities."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, TIME_MINUTES
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LevitonEntity
from .api.const import (
    MAXIMUM_LEVEL,
    MINIMUM_LEVEL_FAN,
    MINIMUM_LEVEL_LIGHT,
    PRESET_LEVEL_OFF,
    STEP_LEVEL_FAN,
    STEP_LEVEL_LIGHT,
)
from .const import (
    CONF_DEVICES,
    CONF_RESIDENCES,
    DATA_COORDINATOR,
    DOMAIN,
)

@dataclass
class LevitonNumberEntityDescription(NumberEntityDescription):
    """Class to describe a Leviton Decora Smart Wi-Fi number entity."""

    entity_category: str[EntityCategory] | None = EntityCategory.CONFIG
    native_max_value: float = MAXIMUM_LEVEL
    native_min_value: float = PRESET_LEVEL_OFF
    native_step: float = STEP_LEVEL_LIGHT
    is_supported: Callable[[Any], bool] = lambda device: device.can_set_level


NUMBER_DESCRIPTIONS: list[LevitonNumberEntityDescription] = [
    LevitonNumberEntityDescription(
        key="min_level",
        name="Minimum Level",
        device_class=NumberDeviceClass.POWER_FACTOR,
        native_min_value=MINIMUM_LEVEL_LIGHT,
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:format-vertical-align-bottom",
    ),
    LevitonNumberEntityDescription(
        key="max_level",
        name="Maximum Level",
        device_class=NumberDeviceClass.POWER_FACTOR,
        native_min_value=MINIMUM_LEVEL_LIGHT,
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:format-vertical-align-top",
    ),
    LevitonNumberEntityDescription(
        key="night_preset_level",
        name="Night Preset Level",
        device_class=NumberDeviceClass.POWER_FACTOR,
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:bookmark",
        is_supported=lambda device: device.can_set_level and not device.is_fan,
    ),
    LevitonNumberEntityDescription(
        key="preset_level",
        name="Preset Level",
        device_class=NumberDeviceClass.POWER_FACTOR,
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:bookmark",
    ),
]


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a Leviton Decora Smart Wi-Fi number entity based on a config entry."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    conf_residences = entry[CONF_RESIDENCES]
    conf_devices = entry[CONF_DEVICES]
    coordinator = entry[DATA_COORDINATOR]
    entities: list[LevitonNumberEntity] = []

    for residence in coordinator.data:
        if residence.id in conf_residences:
            for device in residence.devices:
                for description in NUMBER_DESCRIPTIONS:
                    if all(
                        [
                            device.serial in conf_devices,
                            hasattr(device, description.key),
                            description.is_supported(device),
                        ]
                    ):
                        entities.append(
                            LevitonNumberEntity(
                                coordinator=coordinator,
                                residence_id=residence.id,
                                device_id=device.id,
                                button_id=None,
                                entity_description=description,
                            )
                        )

    async_add_entities(entities)


class LevitonNumberEntity(NumberEntity, LevitonEntity):
    """Representation of a Leviton Decora Smart Wi-Fi number entity."""

    entity_description: LevitonNumberEntityDescription

    @property
    def native_min_value(self) -> float:
        """Return the minimum value."""
        if self.device.is_fan:
            return MINIMUM_LEVEL_FAN
        return self.entity_description.native_min_value

    @property
    def native_step(self) -> float | None:
        """Return the increment/decrement step."""
        if self.device.is_fan:
            return STEP_LEVEL_FAN
        return self.entity_description.native_step

    @property
    def native_value(self) -> float | None:
        """Return the value reported by the number."""
        return getattr(self.device, self.entity_description.key)

    def set_native_value(self, value: float) -> None:
        """Set new value."""
        setattr(self.device, self.entity_description.key, value)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await super().async_set_native_value(value)
        await self.coordinator.async_request_refresh()
