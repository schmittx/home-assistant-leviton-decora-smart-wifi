"""Support for Leviton Decora Smart Wi-Fi sensor entities."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import LevitonEntity
from .const import (
    CONF_DEVICES,
    CONF_RESIDENCES,
    DATA_COORDINATOR,
    DOMAIN,
)

@dataclass
class LevitonSensorEntityDescription(SensorEntityDescription):
    """Class to describe a Leviton Decora Smart Wi-Fi sensor entity."""

    entity_category: str[EntityCategory] | None = EntityCategory.DIAGNOSTIC


SENSOR_DESCRIPTIONS: list[LevitonSensorEntityDescription] = [
    LevitonSensorEntityDescription(
        key="local_ip",
        name="IP Address",
        icon="mdi:ip",
    ),
]


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a Leviton Decora Smart Wi-Fi sensor entity based on a config entry."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    conf_residences = entry[CONF_RESIDENCES]
    conf_devices = entry[CONF_DEVICES]
    coordinator = entry[DATA_COORDINATOR]
    entities: list[LevitonSensorEntity] = []

    for residence in coordinator.data:
        if residence.id in conf_residences:
            for device in residence.devices:
                for description in SENSOR_DESCRIPTIONS:
                    if all(
                        [
                            device.serial in conf_devices,
                            hasattr(device, description.key),
                        ]
                    ):
                        entities.append(
                            LevitonSensorEntity(
                                coordinator=coordinator,
                                residence_id=residence.id,
                                device_id=device.id,
                                button_id=None,
                                entity_description=description,
                            )
                        )

    async_add_entities(entities)


class LevitonSensorEntity(SensorEntity, LevitonEntity):
    """Representation of a Leviton Decora Smart Wi-Fi sensor entity."""

    entity_description: LevitonSensorEntityDescription

    @property
    def native_value(self) -> StateType | date | datetime:
        """Return the value reported by the sensor."""
        return getattr(self.device, self.entity_description.key)
