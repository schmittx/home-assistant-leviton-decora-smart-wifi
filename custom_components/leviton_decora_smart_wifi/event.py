"""Support for Leviton Decora Smart Wi-Fi event entities."""

from dataclasses import dataclass
from typing import Any

from homeassistant.components.event import (
    EventDeviceClass,
    EventEntity,
    EventEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_DEVICES, CONF_RESIDENCES, DATA_COORDINATOR, DOMAIN
from .entity import LevitonEntity

EVENT_TYPE_PRESS = "press"


@dataclass(frozen=True)
class LevitonEventEntityDescription(EventEntityDescription):
    """Class to describe a Leviton Decora Smart Wi-Fi event entity."""


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up event entities for each configured controller button."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = entry_data[DATA_COORDINATOR]
    conf_residences = entry_data[CONF_RESIDENCES]
    conf_devices = entry_data[CONF_DEVICES]

    entities: list[LevitonButtonEvent] = []
    if coordinator.data is None:
        async_add_entities(entities)
        return

    for residence in coordinator.data.residences:
        if residence.id in conf_residences:
            for device in residence.devices:
                if device.id in conf_devices:
                    entities.extend(
                        LevitonButtonEvent(
                            coordinator=coordinator,
                            residence_id=residence.id,
                            device_id=device.id,
                            button_id=button.id,
                            entity_description=LevitonEventEntityDescription(
                                key="event",
                                name=None,
                                device_class=EventDeviceClass.BUTTON,
                                event_types=[EVENT_TYPE_PRESS],
                            ),
                        )
                        for button in device.buttons
                        if device.is_controller
                    )

    async_add_entities(entities)


class LevitonButtonEvent(LevitonEntity, EventEntity):
    """Event entity that fires when a controller button is pressed."""

    entity_description: LevitonEventEntityDescription

    @callback
    def handle_notification(self, notification: dict[str, Any]) -> None:
        """Fire ``press`` when the cloud reports our button was pressed.

        Empirical wire format on the parent IotSwitch::

            {
              "modelName": "IotSwitch", "modelId": <device_id>,
              "data": {"btnPress": [{"button": N, "trigger": T}], ...}
            }

        Where ``button`` is the 1-indexed button number on the controller
        (matches ``Button.number``) and ``trigger`` is the press kind
        (``1`` is the only value seen so far; the attribute is preserved
        verbatim so users can branch on it once more values are observed).
        """
        if (
            self.device
            and self.device.id
            and notification.get("modelId") == self.device.id
        ):
            data = notification.get("data", {})
            for button_press in data.get("btnPress", []):
                if (
                    self.button
                    and self.button.number
                    and button_press.get("button") == self.button.number
                ):
                    self._trigger_event(
                        EVENT_TYPE_PRESS,
                        {
                            "button": button_press.get("button"),
                            "trigger": button_press.get("trigger"),
                        },
                    )
            self.async_write_ha_state()
