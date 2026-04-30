"""Event entities for Leviton Decora Smart Wi-Fi controller buttons.

Surfaces real-time button presses delivered over the MyLeviton cloud
websocket. Each controller button becomes an `event` entity that fires
when the cloud pushes a notification for it.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.event import EventDeviceClass, EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LevitonEntity
from .const import CONF_DEVICES, CONF_RESIDENCES, DATA_COORDINATOR, DOMAIN, SIGNAL_NOTIFICATION

_LOGGER = logging.getLogger(__name__)

EVENT_TYPE_PRESS = "press"

EVENT_TYPES = [EVENT_TYPE_PRESS]


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
        if residence.id not in conf_residences:
            continue
        for device in residence.devices:
            if device.id not in conf_devices:
                continue
            if not getattr(device, "is_controller", False):
                continue
            for button in getattr(device, "buttons", []) or []:
                entities.append(
                    LevitonButtonEvent(
                        coordinator=coordinator,
                        residence_id=residence.id,
                        device_id=device.id,
                        button_id=button.id,
                        config_entry_id=config_entry.entry_id,
                    )
                )

    async_add_entities(entities)


class LevitonButtonEvent(LevitonEntity, EventEntity):
    """Event entity that fires when a controller button is pressed."""

    _attr_device_class = EventDeviceClass.BUTTON
    _attr_event_types = EVENT_TYPES
    _attr_has_entity_name = True
    _attr_translation_key = "button_press"

    def __init__(
        self,
        coordinator,
        residence_id: int,
        device_id: int,
        button_id: int,
        config_entry_id: str,
    ) -> None:
        super().__init__(
            coordinator=coordinator,
            residence_id=residence_id,
            device_id=device_id,
            button_id=button_id,
        )
        self._config_entry_id = config_entry_id

    @property
    def name(self) -> str | None:
        if self.button:
            return f"{self.button.text} press"
        return None

    @property
    def unique_id(self) -> str | None:
        if self.device and self.button:
            return f"{self.device.mac}-{self.button.id}-event"
        return None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        signal = f"{SIGNAL_NOTIFICATION}_{self._config_entry_id}"
        self.async_on_remove(
            async_dispatcher_connect(self.hass, signal, self._handle_notification)
        )

    @callback
    def _handle_notification(self, notification: dict[str, Any]) -> None:
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
        if not isinstance(notification, dict):
            return
        if notification.get("modelName") != "IotSwitch":
            return
        if notification.get("modelId") != self.device_id:
            return

        data = notification.get("data") or {}
        presses = data.get("btnPress") if isinstance(data, dict) else None
        if not isinstance(presses, list):
            return

        button_number = self.button.number if self.button else None
        if button_number is None:
            return

        for press in presses:
            if not isinstance(press, dict):
                continue
            if press.get("button") != button_number:
                continue
            self._trigger_event(
                EVENT_TYPE_PRESS,
                {
                    "trigger": press.get("trigger"),
                    "button": press.get("button"),
                    "lastUpdated": data.get("lastUpdated"),
                    "rssi": data.get("rssi"),
                },
            )
            self.async_write_ha_state()
