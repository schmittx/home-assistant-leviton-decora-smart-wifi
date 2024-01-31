"""Support for Leviton Decora Smart Wi-Fi image entities."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.image import ImageEntity, ImageEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from . import LevitonEntity
from .const import (
    CONF_DEVICES,
    CONF_RESIDENCES,
    DATA_COORDINATOR,
    DOMAIN,
)


@dataclass
class LevitonImageEntityDescription(ImageEntityDescription):
    """Class to describe a Leviton image entity."""

    entity_category: str[EntityCategory] | None = EntityCategory.DIAGNOSTIC
    is_supported: Callable[[Any], bool] = lambda device: device.is_matter_capable
    state: str | None = None

IMAGE_DESCRIPTIONS: list[LevitonImageEntityDescription] = [
    LevitonImageEntityDescription(
        key="matter_qr_code",
        name="Matter Pairing Code",
        state="matter_manual_code",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a Leviton image entity based on a config entry."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    conf_residences = entry[CONF_RESIDENCES]
    conf_devices = entry[CONF_DEVICES]
    coordinator = entry[DATA_COORDINATOR]
    entities: list[LevitonImageEntity] = []

    for residence in coordinator.data:
        if residence.id in conf_residences:
            for device in residence.devices:
                for description in IMAGE_DESCRIPTIONS:
                    if all(
                        [
                            device.id in conf_devices,
                            hasattr(device, description.key),
                            description.is_supported(device),
                        ]
                    ):
                        entities.append(
                            LevitonImageEntity(
                                coordinator=coordinator,
                                residence_id=residence.id,
                                device_id=device.id,
                                entity_description=description,
                                hass=hass,
                            )
                        )

    async_add_entities(entities)


class LevitonImageEntity(LevitonEntity, ImageEntity):
    """Representation of a Leviton image entity."""

    _attr_content_type = "image/png"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        residence_id: int,
        device_id: int,
        entity_description: LevitonImageEntityDescription,
        hass: HomeAssistant,
    ) -> None:
        """Initialize device."""
        super().__init__(
            coordinator=coordinator,
            residence_id=residence_id,
            device_id=device_id,
            entity_description=entity_description,
        )
        ImageEntity.__init__(self, hass)
        self._current_image: bytes | None = None

    @property
    def image_last_updated(self) -> datetime | None:
        """The time when the image was last updated."""
        if self._current_image != getattr(self.device, self.entity_description.key):
            self._attr_image_last_updated = dt_util.utcnow()
        return self._attr_image_last_updated

    async def async_added_to_hass(self) -> None:
        """Fetch and set initial data and state."""
        await super().async_added_to_hass()
        self._current_image = getattr(self.device, self.entity_description.key)
        self._attr_image_last_updated = dt_util.utcnow()

    def image(self) -> bytes | None:
        """Return bytes of image."""
        self._current_image = getattr(self.device, self.entity_description.key)
        return self._current_image

    @property
    def state(self) -> str | None:
        """Return the state."""
        if self.entity_description.state:
            return getattr(self.device, self.entity_description.state)
        return super().state
