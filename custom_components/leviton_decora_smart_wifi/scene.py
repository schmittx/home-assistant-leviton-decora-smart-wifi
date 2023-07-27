"""Support for Leviton Decora Smart Wi-Fi scene entities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.scene import Scene
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory, EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LevitonEntity
from .const import (
    CONF_DEVICES,
    CONF_RESIDENCES,
    DATA_COORDINATOR,
    DOMAIN,
)

@dataclass
class LevitonSceneEntityDescription(EntityDescription):
    """Class to describe a Leviton Decora Smart Wi-Fi scene entity."""


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a Leviton Decora Smart Wi-Fi scene entity based on a config entry."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    conf_residences = entry[CONF_RESIDENCES]
    conf_devices = entry[CONF_DEVICES]
    coordinator = entry[DATA_COORDINATOR]
    entities: list[LevitonSceneEntity] = []

    for residence in coordinator.data:
        if residence.id in conf_residences:
            for room in residence.rooms:
                for scene in room.scenes:
                    entities.append(
                        LevitonSceneEntity(
                            coordinator=coordinator,
                            residence_id=residence.id,
                            room_id=room.id,
                            scene_id=scene.id,
                            entity_description=LevitonSceneEntityDescription(
                                key=None,
                                entity_category=EntityCategory.CONFIG,
                                name=None,
                            ),
                        )
                    )

    async_add_entities(entities)


class LevitonSceneEntity(Scene, LevitonEntity):
    """Representation of a Leviton Decora Smart Wi-Fi scene entity."""

    entity_description: LevitonSceneEntityDescription

    def activate(self, **kwargs: Any) -> None:
        """Activate scene. Try to get entities into requested state."""
        self.scene.execute()

    async def async_activate(self, **kwargs: Any) -> None:
        """Activate scene. Try to get entities into requested state."""
        await super().async_activate()
        await self.coordinator.async_request_refresh()
