"""Support for Leviton Decora Smart Wi-Fi sensor entities."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import SIGNAL_STRENGTH_DECIBELS_MILLIWATT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import LevitonEntity
from .api.const import GFCI_STATUS_OPTIONS
from .const import CONF_DEVICES, CONF_RESIDENCES, DATA_COORDINATOR, DOMAIN


@dataclass
class LevitonSensorEntityDescription(SensorEntityDescription):
    """Class to describe a Leviton Decora Smart Wi-Fi sensor entity."""

    entity_category: str[EntityCategory] | None = EntityCategory.DIAGNOSTIC
    is_supported: Callable[[Any], bool] = lambda device: True
    translation_key: str | None = "all"


SENSOR_DESCRIPTIONS: list[LevitonSensorEntityDescription] = [
    LevitonSensorEntityDescription(
        key="fault_status",
        name="Fault Status",
        device_class=SensorDeviceClass.ENUM,
        options=GFCI_STATUS_OPTIONS,
        icon="mdi:lightning-bolt-circle",
        is_supported=lambda device: device.is_gfci,
    ),
    LevitonSensorEntityDescription(
        key="local_ip",
        name="IP Address",
        icon="mdi:ip",
    ),
    LevitonSensorEntityDescription(
        key="signal_strength",
        name="Signal Strength",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        icon="mdi:wifi",
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
            entities.extend(
                LevitonSensorEntity(
                    coordinator=coordinator,
                    residence_id=residence.id,
                    entity_description=description,
                )
                for description in SENSOR_DESCRIPTIONS
                if hasattr(residence, description.key)
            )

            for device in residence.devices:
                if device.id in conf_devices:
                    entities.extend(
                        LevitonSensorEntity(
                            coordinator=coordinator,
                            residence_id=residence.id,
                            device_id=device.id,
                            entity_description=description,
                        )
                        for description in SENSOR_DESCRIPTIONS
                        if all(
                            [
                                hasattr(device, description.key),
                                description.is_supported(device),
                            ]
                        )
                    )

    async_add_entities(entities)


class LevitonSensorEntity(SensorEntity, LevitonEntity):
    """Representation of a Leviton Decora Smart Wi-Fi sensor entity."""

    entity_description: LevitonSensorEntityDescription

    @property
    def native_value(self) -> StateType | date | datetime:
        """Return the value reported by the sensor."""
        return getattr(self.target, self.entity_description.key)
