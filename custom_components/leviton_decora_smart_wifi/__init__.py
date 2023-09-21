"""The Leviton Decora Smart Wi-Fi integration."""
from __future__ import annotations

import async_timeout
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_ID,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    CONF_TOKEN,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import LevitonAPI, LevitonException
from .api.activity import Activity as LevitonActivity
from .api.button import Button as LevitonButton
from .api.device import Device as LevitonDevice
from .api.residence import Residence as LevitonResidence
from .api.room import Room as LevitonRoom
from .api.scene import Scene as LevitonScene
from .api.schedule import Schedule as LevitonSchedule
from .const import (
    CONF_DEVICES,
    CONF_RESIDENCES,
    CONF_SAVE_RESPONSES,
    CONF_TIMEOUT,
    CONFIGURATION_URL,
    DATA_COORDINATOR,
    DEFAULT_SAVE_LOCATION,
    DEFAULT_SAVE_RESPONSES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    UNDO_UPDATE_LISTENER,
)

PLATFORMS = (
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.FAN,
    Platform.LIGHT,
    Platform.NUMBER,
    Platform.SCENE,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.UPDATE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    data = config_entry.data
    options = config_entry.options

    conf_residences = options.get(CONF_RESIDENCES, data.get(CONF_RESIDENCES, []))
    conf_devices = options.get(CONF_DEVICES, data.get(CONF_DEVICES, []))
    conf_identifiers = [(DOMAIN, conf_id) for conf_id in conf_residences + conf_devices]

    device_registry = dr.async_get(hass)
    device_entries = hass.helpers.device_registry.async_entries_for_config_entry(
        registry=device_registry,
        config_entry_id=config_entry.entry_id,
    )
    for device_entry in device_entries:
        orphan_identifiers: list[bool] = []
        for device_identifier in device_entry.identifiers:
            orphan_identifiers.append(bool(device_identifier not in conf_identifiers))
        if all(orphan_identifiers):
            device_registry.async_remove_device(device_entry.id)

    conf_save_responses = options.get(CONF_SAVE_RESPONSES, DEFAULT_SAVE_RESPONSES)
    conf_scan_interval = options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    conf_timeout = options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)

    conf_save_location = DEFAULT_SAVE_LOCATION if conf_save_responses else None

    api = LevitonAPI(
        save_location=conf_save_location,
        user_id=data[CONF_ID],
        authorization=data[CONF_TOKEN],
    )

    async def async_update_data():
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            async with async_timeout.timeout(conf_timeout):
                return await hass.async_add_executor_job(api.update, conf_residences)
        except LevitonException as exception:
            raise UpdateFailed("Error communicating with API, Status: {}, Error Name: {}, Error Message: {}").format(
                exception.status_code,
                exception.name,
                exception.message,
            )

    coordinator = DataUpdateCoordinator(
        hass=hass,
        logger=_LOGGER,
        name=f"Leviton Decora Smart Wi-Fi ({data[CONF_NAME]})",
        update_method=async_update_data,
        update_interval=timedelta(seconds=conf_scan_interval),
    )
    await coordinator.async_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = {
        CONF_RESIDENCES: conf_residences,
        CONF_DEVICES: conf_devices,
        DATA_COORDINATOR: coordinator,
        UNDO_UPDATE_LISTENER: config_entry.add_update_listener(async_update_listener),
    }

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry=config_entry,
        platforms=PLATFORMS,
    )
    if unload_ok:
        hass.data[DOMAIN][config_entry.entry_id][UNDO_UPDATE_LISTENER]()
        hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok


async def async_update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


class LevitonEntity(CoordinatorEntity):
    """Representation of a Leviton entity."""

    def __init__(
            self,
            coordinator: DataUpdateCoordinator,
            residence_id: int,
            activity_id: int = None,
            schedule_id: int = None,
            room_id: int = None,
            scene_id: int = None,
            device_id: int = None,
            button_id: int = None,
            entity_description: EntityDescription = None,
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
        self.entity_description = entity_description

    @property
    def residence(self) -> LevitonResidence | None:
        """Return a LevitonResidence object."""
        residences = {residence.id: residence for residence in self.coordinator.data}
        return residences.get(self.residence_id)

    @property
    def activity(self) -> LevitonActivity | None:
        """Return a LevitonActivity object."""
        activities = {activity.id: activity for activity in self.residence.activities}
        return activities.get(self.activity_id)

    @property
    def schedule(self) -> LevitonSchedule | None:
        """Return a LevitonSchedule object."""
        schedules = {schedule.id: schedule for schedule in self.residence.schedules}
        return schedules.get(self.schedule_id)

    @property
    def room(self) -> LevitonRoom | None:
        """Return a LevitonRoom object."""
        rooms = {room.id: room for room in self.residence.rooms}
        return rooms.get(self.room_id)

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
        devices = {device.id: device for device in self.residence.devices}
        return devices.get(self.device_id)

    @property
    def button(self) -> LevitonButton | None:
        """Return a LevitonButton object."""
        if self.device:
            buttons = {button.id: button for button in self.device.buttons}
            return buttons.get(self.button_id)
        return None

    @property
    def target(self) -> LevitonResidence | LevitonActivity | LevitonSchedule | LevitonRoom | LevitonScene | LevitonDevice | LevitonButton | None:
        """Return the target object."""
        if self.button:
            return self.button
        elif self.device:
            return self.device
        elif self.scene:
            return self.scene
        elif self.room:
            return self.room
        elif self.schedule:
            return self.schedule
        elif self.activity:
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
    def device_info(self) -> dr.DeviceInfo:
        """Return device specific attributes.

        Implemented by platform classes.
        """
        if self.device:
            return dr.DeviceInfo(
                configuration_url=CONFIGURATION_URL,
                hw_version=self.device.serial,
                identifiers={(DOMAIN, self.device.id)},
                manufacturer=self.device.manufacturer,
                model=self.device.model,
                name=self.device.name,
                suggested_area=self.device.room_name,
                sw_version=self.device.version,
                via_device=(DOMAIN, self.residence.id),
            )
        return dr.DeviceInfo(
            configuration_url=CONFIGURATION_URL,
            identifiers={(DOMAIN, self.residence.id)},
            manufacturer="Leviton Manufacturing Co., Inc.",
            model="Residence",
            name=self.residence.name,
        )

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        name = self.residence.name
        if self.device:
            name = self.device.name
        if self.activity:
            return f"{name} {self.activity.name} Activity"
        elif self.schedule:
            return f"{name} {self.schedule.name} Schedule"
        elif self.scene:
            return f"{name} {self.scene.name} Scene"
        elif self.button:
            return f"{name} {self.button.text}"
        elif description := self.entity_description.name:
            return f"{name} {description}"
        return name

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        unique_id = self.residence.id
        if self.device:
            unique_id = self.device.mac
        if self.activity:
            return f"{unique_id}-{self.activity.id}"
        elif self.schedule:
            return f"{unique_id}-{self.schedule.id}"
        elif self.scene:
            return f"{unique_id}-{self.room.id}-{self.scene.id}"
        elif self.button:
            return f"{unique_id}-{self.button.id}"
        elif key := self.entity_description.key:
            return f"{unique_id}-{key}"
        return unique_id

