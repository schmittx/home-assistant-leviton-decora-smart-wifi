"""Support for Leviton Decora Smart Wi-Fi update entities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.update import (
    UpdateDeviceClass,
    UpdateEntity,
    UpdateEntityDescription,
    UpdateEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LevitonEntity
from .const import CONF_DEVICES, CONF_RESIDENCES, DATA_COORDINATOR, DOMAIN, RELEASE_URL


@dataclass(frozen=True)
class LevitonUpdateEntityDescription(UpdateEntityDescription):
    """Class to describe a Leviton Decora Smart Wi-Fi update entity."""

    device_class: UpdateDeviceClass | None = UpdateDeviceClass.FIRMWARE
    entity_category: EntityCategory | None = EntityCategory.CONFIG


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up an Leviton Decora Smart Wi-Fi update entity based on a config entry."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    conf_residences = entry[CONF_RESIDENCES]
    conf_devices = entry[CONF_DEVICES]
    coordinator = entry[DATA_COORDINATOR]
    entities: list[LevitonUpdateEntity] = []

    for residence in coordinator.data.residences:
        if residence.id in conf_residences:
            entities.extend(
                LevitonUpdateEntity(
                    coordinator=coordinator,
                    residence_id=residence.id,
                    device_id=device.id,
                    entity_description=LevitonUpdateEntityDescription(
                        key="update",
                        name="Firmware",
                    ),
                )
                for device in residence.devices
                if device.id in conf_devices
            )

    async_add_entities(entities)


class LevitonUpdateEntity(UpdateEntity, LevitonEntity):
    """Representation of an Leviton Decora Smart Wi-Fi update entity."""

    entity_description: LevitonUpdateEntityDescription

    @property
    def installed_version(self) -> str | None:
        """Version installed and in use."""
        if self.device is not None:
            return self.device.version
        return None

    @property
    def latest_version(self) -> str | None:
        """Latest version available for install."""
        if self.device is not None:
            return self.device.update_version
        return None

    @property
    def release_summary(self) -> str | None:
        """Summary of the release notes or changelog.

        This is not suitable for long changelogs, but merely suitable
        for a short excerpt update description of max 255 characters.
        """
        if self.firmware is not None and self.latest_version == self.firmware.version:
            return (
                self.firmware.notes.replace("~", "-") if self.firmware.notes else None
            )
        return None

    def release_notes(self) -> str | None:
        """Return full release notes.

        This is suitable for a long changelog that does not fit in the release_summary property.
        The returned string can contain markdown.
        """
        return self.release_summary

    @property
    def release_url(self) -> str | None:
        """URL to the full release notes of the latest version available."""
        if self.device is not None and self.device.is_generation_two:
            return RELEASE_URL
        return None

    @property
    def supported_features(self) -> UpdateEntityFeature:
        """Flag supported features."""
        return UpdateEntityFeature.INSTALL

    def install(self, version: str | None, backup: bool, **kwargs: Any) -> None:
        """Install an update.

        Version can be specified to install a specific version. When `None`, the
        latest version needs to be installed.

        The backup parameter indicates a backup should be taken before
        installing the update.
        """
        if self.device is not None:
            self.device.apply_update()
