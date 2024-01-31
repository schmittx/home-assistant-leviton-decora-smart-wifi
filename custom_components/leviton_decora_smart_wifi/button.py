"""Support for Leviton Decora Smart Wi-Fi button entities."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
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
class LevitonButtonEntityDescription(ButtonEntityDescription):
    """Class to describe a Leviton Decora Smart Wi-Fi button entity."""

    entity_category: str[EntityCategory] | None = EntityCategory.CONFIG

BUTTON_DESCRIPTIONS: list[LevitonButtonEntityDescription] = [
    LevitonButtonEntityDescription(
        key="identify",
        name="Identify",
        icon="mdi:flash",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a Leviton Decora Smart Wi-Fi button entity based on a config entry."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    conf_residences = entry[CONF_RESIDENCES]
    conf_devices = entry[CONF_DEVICES]
    coordinator = entry[DATA_COORDINATOR]
    entities: list[LevitonButtonEntity] = []

    for residence in coordinator.data:
        if residence.id in conf_residences:
            for activity in residence.activities:
                entities.append(
                    LevitonButtonEntity(
                        coordinator=coordinator,
                        residence_id=residence.id,
                        activity_id=activity.id,
                        entity_description=LevitonButtonEntityDescription(
                            key=None,
                            name=None,
                        ),
                    )
                )
            for device in residence.devices:
                if device.id in conf_devices:
                    if device.is_controller:
                        for button in device.buttons:
                            entities.append(
                                LevitonButtonEntity(
                                    coordinator=coordinator,
                                    residence_id=residence.id,
                                    device_id=device.id,
                                    button_id=button.id,
                                    entity_description=LevitonButtonEntityDescription(
                                        key=None,
                                        name=None,
                                    ),
                                )
                            )
                    for description in BUTTON_DESCRIPTIONS:
                        if hasattr(device, description.key):
                            entities.append(
                                LevitonButtonEntity(
                                    coordinator=coordinator,
                                    residence_id=residence.id,
                                    device_id=device.id,
                                    entity_description=description,
                                )
                            )

    async_add_entities(entities)


class LevitonButtonEntity(ButtonEntity, LevitonEntity):
    """Representation of a Leviton Decora Smart Wi-Fi button entity."""

    entity_description: LevitonButtonEntityDescription

    def press(self) -> None:
        """Press the button."""
        if self.activity:
            self.activity.execute()
        elif self.button:
            self.button.press()
        else:
            getattr(self.device, self.entity_description.key)()

    async def async_press(self) -> None:
        """Press the button."""
        await super().async_press()
        await self.coordinator.async_request_refresh()
