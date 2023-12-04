"""Support for Leviton Decora Smart Wi-Fi select entities."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LevitonEntity
from .const import (
    CONF_DEVICES,
    CONF_RESIDENCES,
    DATA_COORDINATOR,
    DOMAIN,
)

@dataclass
class LevitonSelectEntityDescription(SelectEntityDescription):
    """Class to describe a Leviton Decora Smart Wi-Fi select entity."""

    entity_category: str[EntityCategory] | None = EntityCategory.CONFIG
    is_supported: Callable[[Any], bool] = lambda device: (
        device.can_set_level and device.is_light
    )
    translation_key: str | None = "all"

SELECT_DESCRIPTIONS: list[LevitonSelectEntityDescription] = [
    LevitonSelectEntityDescription(
        key="auto_shutoff",
        name="Auto Shutoff",
        options="auto_shutoff_options",
        icon="mdi:timer",
        is_supported=lambda device: not device.is_motion_sensor,
    ),
    LevitonSelectEntityDescription(
        key="bulb_threshold",
        name="Bulb Threshold",
        options="bulb_threshold_options",
        icon="mdi:tune",
    ),
    LevitonSelectEntityDescription(
        key="bulb_type",
        name="Bulb Type",
        options="bulb_type_options",
        icon="mdi:lightbulb-cfl",
    ),
    LevitonSelectEntityDescription(
        key="fade_off_rate",
        name="Fade Off Rate",
        options="fade_on_off_rate_options",
        icon="mdi:network-strength-1",
    ),
    LevitonSelectEntityDescription(
        key="fade_on_rate",
        name="Fade On Rate",
        options="fade_on_off_rate_options",
        icon="mdi:network-strength-3",
    ),
    LevitonSelectEntityDescription(
        key="led_bar_behavior",
        name="LED Bar Behavior",
        options="led_bar_behavior_options",
        icon="mdi:dots-vertical",
        is_supported=lambda device: device.has_led_bar,
    ),
    LevitonSelectEntityDescription(
        key="motion_mode",
        name="Motion Mode",
        options="motion_mode_options",
        icon="mdi:exit-run",
        is_supported=lambda device: device.is_motion_sensor,
    ),
    LevitonSelectEntityDescription(
        key="motion_night_mode",
        name="Motion Night Mode",
        options="motion_night_mode_options",
        icon="mdi:lightbulb-night",
        is_supported=lambda device: device.is_motion_sensor,
    ),
    LevitonSelectEntityDescription(
        key="motion_snooze",
        name="Motion Snooze",
        options="motion_snooze_options",
        icon="mdi:alarm-snooze",
        is_supported=lambda device: device.is_motion_sensor,
    ),
    LevitonSelectEntityDescription(
        key="motion_timeout",
        name="Motion Timeout",
        options="motion_timeout_options",
        icon="mdi:timer",
        is_supported=lambda device: device.is_motion_sensor,
    ),
    LevitonSelectEntityDescription(
        key="status",
        name="Status",
        options="status_options",
        icon="mdi:home-switch-outline",
    ),
    LevitonSelectEntityDescription(
        key="status_led_behavior",
        name="Status LED Behavior",
        options="status_led_behavior_options",
        icon="mdi:led-on",
        is_supported=lambda device: not device.is_controller,
    ),
]


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a Leviton Decora Smart Wi-Fi select entity based on a config entry."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    conf_residences = entry[CONF_RESIDENCES]
    conf_devices = entry[CONF_DEVICES]
    coordinator = entry[DATA_COORDINATOR]
    entities: list[LevitonSelectEntity] = []

    for residence in coordinator.data:
        if residence.id in conf_residences:
            for description in SELECT_DESCRIPTIONS:
                if hasattr(residence, description.key):
                    entities.append(
                        LevitonSelectEntity(
                            coordinator=coordinator,
                            residence_id=residence.id,
                            entity_description=description,
                        )
                    )

            for device in residence.devices:
                for description in SELECT_DESCRIPTIONS:
                    if all(
                        [
                            device.id in conf_devices,
                            hasattr(device, description.key),
                            description.is_supported(device),
                        ]
                    ):
                        entities.append(
                            LevitonSelectEntity(
                                coordinator=coordinator,
                                residence_id=residence.id,
                                device_id=device.id,
                                entity_description=description,
                            )
                        )

    async_add_entities(entities)


class LevitonSelectEntity(SelectEntity, LevitonEntity):
    """Representation of a Leviton Decora Smart Wi-Fi select entity."""

    entity_description: LevitonSelectEntityDescription

    @property
    def options(self) -> list[str]:
        """Return a set of selectable options."""
        return getattr(self.target, self.entity_description.options)

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        return getattr(self.target, self.entity_description.key)

    def select_option(self, option: str) -> None:
        """Change the selected option."""
        setattr(self.target, self.entity_description.key, option)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await super().async_select_option(option)
        await self.coordinator.async_request_refresh()
