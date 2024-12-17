"""Support for Leviton Decora Smart Wi-Fi switch entities."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
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
class LevitonSwitchEntityDescription(SwitchEntityDescription):
    """Class to describe a Leviton Decora Smart Wi-Fi switch entity."""

    entity_category: str[EntityCategory] | None = EntityCategory.CONFIG
    is_supported: Callable[[Any], bool] = lambda device: device.has_motion_sensor

SWITCH_DESCRIPTIONS: list[LevitonSwitchEntityDescription] = [
    LevitonSwitchEntityDescription(
        key="auto_update_enabled",
        name="Automatic Updates",
        icon="mdi:update",
    ),
    LevitonSwitchEntityDescription(
        key="buzzer_enabled",
        name="Audible Alert",
        icon="mdi:volume-high",
        is_supported=lambda device: device.is_gfci,
    ),
    LevitonSwitchEntityDescription(
        key="light_sensor_enabled",
        name="Light Sensor",
        icon="mdi:lightbulb-on",
        is_supported=lambda device: device.has_light_sensor,
    ),
    LevitonSwitchEntityDescription(
        key="motion_detection_enabled",
        name="Motion Detection",
        icon="mdi:motion-sensor",
    ),
    LevitonSwitchEntityDescription(
        key="motion_led_feedback_enabled",
        name="Motion LED Feedback",
        icon="mdi:led-on",
    ),
    LevitonSwitchEntityDescription(
        key="status_led_enabled",
        name="Status LED",
        icon="mdi:led-on",
        is_supported=lambda device: device.is_controller,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a Leviton Decora Smart Wi-Fi switch entity based on a config entry."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    conf_residences = entry[CONF_RESIDENCES]
    conf_devices = entry[CONF_DEVICES]
    coordinator = entry[DATA_COORDINATOR]
    entities: list[LevitonSwitchEntity] = []

    for residence in coordinator.data:
        if residence.id in conf_residences:
            for description in SWITCH_DESCRIPTIONS:
                if hasattr(residence, description.key):
                    entities.append(
                        LevitonSwitchEntity(
                            coordinator=coordinator,
                            residence_id=residence.id,
                            entity_description=description,
                        )
                    )
            for schedule in residence.schedules:
                entities.append(
                    LevitonSwitchEntity(
                        coordinator=coordinator,
                        residence_id=residence.id,
                        schedule_id=schedule.id,
                        entity_description=LevitonSwitchEntityDescription(
                            key=None,
                            name=None,
                            icon="mdi:calendar-clock",
                        ),
                    )
                )
            for device in residence.devices:
                if device.id in conf_devices:
                    if any(
                        [
                            device.is_outlet,
                            device.is_switch,
                        ]
                    ):
                        entities.append(
                            LevitonSwitchEntity(
                                coordinator=coordinator,
                                residence_id=residence.id,
                                device_id=device.id,
                                entity_description=LevitonSwitchEntityDescription(
                                    entity_category=None,
                                    key=None,
                                    name=None,
                                ),
                            )
                        )
                    for description in SWITCH_DESCRIPTIONS:
                        if all(
                            [
                                hasattr(device, description.key),
                                description.is_supported(device),
                            ]
                        ):
                            entities.append(
                                LevitonSwitchEntity(
                                    coordinator=coordinator,
                                    residence_id=residence.id,
                                    device_id=device.id,
                                    entity_description=description,
                                )
                            )

    async_add_entities(entities)


class LevitonSwitchEntity(SwitchEntity, LevitonEntity):
    """Representation of a Leviton Decora Smart Wi-Fi switch entity."""

    entity_description: LevitonSwitchEntityDescription

    @property
    def device_class(self) -> SwitchDeviceClass | str | None:
        """Return the class of this device, from component DEVICE_CLASSES."""
        if self.device:
            if self.device.is_outlet:
                return SwitchDeviceClass.OUTLET
            return SwitchDeviceClass.SWITCH
        return None

    @property
    def is_on(self) -> bool:
        """Return True if entity is on."""
        if self.schedule:
            return self.schedule.enabled
        elif key := self.entity_description.key:
            return getattr(self.target, key)
        return self.device.is_on

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        if self.schedule:
            self.schedule.enable()
        elif key := self.entity_description.key:
            setattr(self.target, key, True)
        else:
            self.device.turn_on()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await super().async_turn_on(**kwargs)
        await self.coordinator.async_request_refresh()

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        if self.schedule:
            self.schedule.disable()
        elif key := self.entity_description.key:
            setattr(self.target, key, False)
        else:
            self.device.turn_off()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await super().async_turn_off(**kwargs)
        await self.coordinator.async_request_refresh()
