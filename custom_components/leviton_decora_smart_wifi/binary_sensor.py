"""Support for Leviton Decora Smart Wi-Fi binary sensor entities."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
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
class LevitonBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Class to describe a Leviton Decora Smart Wi-Fi binary sensor entity."""

    is_supported: Callable[[Any], bool] = lambda device: device.has_motion_sensor

BINARY_SENSOR_DESCRIPTIONS: list[LevitonBinarySensorEntityDescription] = [
    LevitonBinarySensorEntityDescription(
        key="fault_detected",
        name="Fault Detected",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_supported=lambda device: device.is_gfci,
    ),
    LevitonBinarySensorEntityDescription(
        key="motion_occupied",
        name="Occupancy Detected",
        device_class=BinarySensorDeviceClass.OCCUPANCY,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a Leviton Decora Smart Wi-Fi binary sensor entity based on a config entry."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    conf_residences = entry[CONF_RESIDENCES]
    conf_devices = entry[CONF_DEVICES]
    coordinator = entry[DATA_COORDINATOR]
    entities: list[LevitonBinarySensorEntity] = []

    for residence in coordinator.data:
        if residence.id in conf_residences:
            for device in residence.devices:
                if device.id in conf_devices:
                    for description in BINARY_SENSOR_DESCRIPTIONS:
                        if all(
                            [
                                hasattr(device, description.key),
                                description.is_supported(device),
                            ]
                        ):
                            entities.append(
                                LevitonBinarySensorEntity(
                                    coordinator=coordinator,
                                    residence_id=residence.id,
                                    device_id=device.id,
                                    entity_description=description,
                                )
                            )

    async_add_entities(entities)


class LevitonBinarySensorEntity(BinarySensorEntity, LevitonEntity):
    """Representation of a Leviton Decora Smart Wi-Fi binary sensor entity."""

    entity_description: LevitonBinarySensorEntityDescription

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return getattr(self.device, self.entity_description.key)
