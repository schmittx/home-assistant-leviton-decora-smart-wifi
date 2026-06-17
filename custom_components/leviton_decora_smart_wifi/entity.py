"""Base class for Leviton Decora Smart Wi-Fi entities."""

from typing import Any

from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import LevitonDataUpdateCoordinator
from .api.activity import Activity as LevitonActivity
from .api.button import Button as LevitonButton
from .api.device import Device as LevitonDevice
from .api.firmware import Firmware as LevitonFirmware
from .api.residence import Residence as LevitonResidence
from .api.room import Room as LevitonRoom
from .api.scene import Scene as LevitonScene
from .api.schedule import Schedule as LevitonSchedule
from .const import (
    CONFIGURATION_URL,
    DEVICE_INFO_MANUFACTURER,
    DEVICE_INFO_MODEL_RESIDENCE,
    DOMAIN,
    UPDATE_NOTIFICATION,
)


class LevitonEntity(CoordinatorEntity[LevitonDataUpdateCoordinator]):
    """Representation of a Leviton entity."""

    def __init__(
        self,
        coordinator: LevitonDataUpdateCoordinator,
        residence_id: int,
        activity_id: int | None = None,
        schedule_id: int | None = None,
        room_id: int | None = None,
        scene_id: int | None = None,
        device_id: int | None = None,
        button_id: int | None = None,
        entity_description: EntityDescription | None = None,
    ) -> None:
        """Initialize the device."""
        super().__init__(coordinator)
        self.residence_id = residence_id
        self.activity_id = activity_id
        self.schedule_id = schedule_id
        self.room_id = room_id
        self.scene_id = scene_id
        self.device_id = device_id
        self.button_id = button_id
        if entity_description:
            self.entity_description = entity_description

    @property
    def residence(self) -> LevitonResidence | None:
        """Return a LevitonResidence object."""
        residences = {
            residence.id: residence for residence in self.coordinator.data.residences
        }
        return residences.get(self.residence_id)

    @property
    def firmware(self) -> LevitonFirmware | None:
        """Return a LevitonFirmware object."""
        if self.device and self.device.model:
            return self.coordinator.data.firmware.get(self.device.model)
        return None

    @property
    def activity(self) -> LevitonActivity | None:
        """Return a LevitonActivity object."""
        if self.residence:
            activities = {
                activity.id: activity for activity in self.residence.activities
            }
            return activities.get(self.activity_id)
        return None

    @property
    def schedule(self) -> LevitonSchedule | None:
        """Return a LevitonSchedule object."""
        if self.residence:
            schedules = {schedule.id: schedule for schedule in self.residence.schedules}
            return schedules.get(self.schedule_id)
        return None

    @property
    def room(self) -> LevitonRoom | None:
        """Return a LevitonRoom object."""
        if self.residence:
            rooms = {room.id: room for room in self.residence.rooms}
            return rooms.get(self.room_id)
        return None

    @property
    def scene(self) -> LevitonScene | None:
        """Return a LevitonScene object."""
        if self.room:
            scenes = {scene.id: scene for scene in self.room.scenes}
            return scenes.get(self.scene_id)
        return None

    @property
    def device(self) -> LevitonDevice | None:
        """Return a LevitonDevice object."""
        if self.residence:
            devices = {device.id: device for device in self.residence.devices}
            return devices.get(self.device_id)
        return None

    @property
    def button(self) -> LevitonButton | None:
        """Return a LevitonButton object."""
        if self.device:
            buttons = {button.id: button for button in self.device.buttons}
            return buttons.get(self.button_id)
        return None

    @property
    def target(
        self,
    ) -> (
        LevitonResidence
        | LevitonActivity
        | LevitonSchedule
        | LevitonRoom
        | LevitonScene
        | LevitonDevice
        | LevitonButton
        | None
    ):
        """Return the target object."""
        if self.button:
            return self.button
        if self.device:
            return self.device
        if self.scene:
            return self.scene
        if self.room:
            return self.room
        if self.schedule:
            return self.schedule
        if self.activity:
            return self.activity
        return self.residence

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        available = super().available
        if self.device:
            return all(
                [
                    available,
                    self.device.is_connected,
                ]
            )
        return available

    @property
    def device_info(self) -> dr.DeviceInfo | None:
        """Return device specific attributes.

        Implemented by platform classes.
        """
        if self.residence and self.residence.id:
            if self.device and self.device.id:
                return dr.DeviceInfo(
                    configuration_url=CONFIGURATION_URL,
                    identifiers={(DOMAIN, str(self.device.id))},
                    manufacturer=self.device.manufacturer,
                    model=self.device.model,
                    name=self.device.name,
                    serial_number=self.device.serial,
                    suggested_area=self.device.room_name,
                    sw_version=self.device.version,
                    via_device=(DOMAIN, str(self.residence.id)),
                )
            return dr.DeviceInfo(
                configuration_url=CONFIGURATION_URL,
                entry_type=dr.DeviceEntryType.SERVICE,
                identifiers={(DOMAIN, str(self.residence.id))},
                manufacturer=DEVICE_INFO_MANUFACTURER,
                model=DEVICE_INFO_MODEL_RESIDENCE,
                name=self.residence.name,
            )
        return None

    @property
    def name(self) -> str | None:
        """Return the name of the entity."""
        name = self.residence.name if self.residence else None
        if self.device:
            name = self.device.name
        if self.activity:
            return f"{name} {self.activity.name} Activity"
        if self.schedule:
            return f"{name} {self.schedule.name} Schedule"
        if self.scene:
            return f"{name} {self.scene.name} Scene"
        if self.button:
            return f"{name} {self.button.text}"
        if description := self.entity_description.name:
            return f"{name} {description}"
        return name

    @property
    def unique_id(self) -> str | int | None:
        """Return a unique ID."""
        unique_id = self.residence.id if self.residence else None
        if self.device:
            unique_id = self.device.mac
        if self.activity:
            return f"{unique_id}-{self.activity.id}"
        if self.schedule:
            return f"{unique_id}-{self.schedule.id}"
        if self.scene and self.room:
            return f"{unique_id}-{self.room.id}-{self.scene.id}"
        if self.button:
            return f"{unique_id}-{self.button.id}"
        if key := self.entity_description.key:
            return f"{unique_id}-{key}"
        return unique_id

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass.

        To be extended by integrations.
        """
        await super().async_added_to_hass()
        if self.device and self.device.id:
            self.async_on_remove(
                async_dispatcher_connect(
                    self.hass,
                    f"{UPDATE_NOTIFICATION}_{self.device.id}",
                    self.handle_notification,
                )
            )

    @callback
    def handle_notification(self, notification: dict[str, Any]) -> None:
        """Handle notification."""
        self.async_write_ha_state()
