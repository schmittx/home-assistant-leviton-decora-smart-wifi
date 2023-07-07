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
from homeassistant.helpers.entity import DeviceInfo, EntityDescription
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import LevitonAPI, LevitonException
from .api.button import Button as LevitonButton
from .api.device import Device as LevitonDevice
from .api.residence import Residence as LevitonResidence
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
    conf_identifiers = [(DOMAIN, device_serial) for device_serial in conf_devices]

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
                return await hass.async_add_executor_job(api.update)
        except LevitonException as exception:
            raise UpdateFailed(f"Error communicating with API, Status: {exception.status_code}, Error Name: {exception.name}, Error Message: {exception.message}")

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
            device_id: int,
            button_id: int=None,
            entity_description: EntityDescription=None,
        ) -> None:
        """Initialize the device."""
        super().__init__(coordinator)
        self.residence_id = residence_id
        self.device_id = device_id
        self.button_id = button_id
        self.entity_description = entity_description

    @property
    def residence(self) -> LevitonResidence | None:
        """Return a LevitonResidence object."""
        residences = {residence.id: residence for residence in self.coordinator.data}
        return residences.get(self.residence_id)

    @property
    def device(self) -> LevitonDevice | None:
        """Return a LevitonDevice object."""
        devices = {device.id: device for device in self.residence.devices}
        return devices.get(self.device_id)

    @property
    def button(self) -> LevitonButton | None:
        """Return a LevitonButton object."""
        buttons = {button.id: button for button in self.device.buttons}
        return buttons.get(self.button_id)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return all(
            [
                super().available,
                self.device.is_connected,
            ]
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device specific attributes.

        Implemented by platform classes.
        """
        return DeviceInfo(
            configuration_url=CONFIGURATION_URL,
            identifiers={(DOMAIN, self.device.mac)},
            manufacturer=self.device.manufacturer,
            model=self.device.model,
            name=self.device.name,
            suggested_area=self.device.room_name,
            sw_version=self.device.version,
            hw_version=self.device.serial,
        )

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        if description := self.entity_description.name:
            return f"{self.device.name} {description}"
        return None

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        unique_id = self.device.mac
        if key := self.entity_description.key:
            return f"{unique_id}-{key}"
        return unique_id

