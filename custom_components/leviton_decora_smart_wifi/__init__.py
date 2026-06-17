"""The Leviton Decora Smart Wi-Fi integration."""

from asyncio import timeout
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
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import LevitonAPI, LevitonData, LevitonException
from .api.websocket import LevitonWebSocket
from .config_flow import LevitonConfigFlow
from .const import (
    CONF_DEVICES,
    CONF_LOGIN_RESPONSE,
    CONF_RESIDENCES,
    CONF_SAVE_RESPONSES,
    CONF_TIMEOUT,
    CONFIGURATION_URL,
    DATA_API,
    DATA_COORDINATOR,
    DATA_WEBSOCKET,
    DEFAULT_SAVE_LOCATION,
    DEFAULT_SAVE_RESPONSES,
    DEVICE_INFO_MANUFACTURER,
    DEVICE_INFO_MODEL_RESIDENCE,
    DOMAIN,
    EVENT_NOTIFICATION,
    UNDO_UPDATE_LISTENER,
    UPDATE_NOTIFICATION,
    ScanInterval,
    Timeout,
)

PLATFORMS = (
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.EVENT,
    Platform.FAN,
    Platform.IMAGE,
    Platform.LIGHT,
    Platform.NUMBER,
    Platform.SCENE,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.UPDATE,
)

_LOGGER = logging.getLogger(__name__)


class LevitonDataUpdateCoordinator(DataUpdateCoordinator[LevitonData]):
    """Class to manage fetching data from single endpoint."""

    async def _async_update_data(self) -> LevitonData:
        """Fetch the latest data from the source."""
        if self.update_method is None:
            raise NotImplementedError("Update method not implemented")
        return await self.update_method()


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    if config_entry.version > LevitonConfigFlow.VERSION:
        return False

    if config_entry.version < LevitonConfigFlow.VERSION:
        _LOGGER.info("Migrating configuration from version: %s", config_entry.version)

        data = dict(config_entry.data)
        options = dict(config_entry.options)
        _LOGGER.debug("Initial data:\n%s", data)
        _LOGGER.debug("Initial options:\n%s", options)

        if config_entry.version <= 1:
            data[CONF_SCAN_INTERVAL] = ScanInterval.DEFAULT
            options[CONF_SCAN_INTERVAL] = ScanInterval.DEFAULT

        _LOGGER.debug("Migrated data:\n%s", data)
        _LOGGER.debug("Migrated options:\n%s", options)

        hass.config_entries.async_update_entry(
            entry=config_entry,
            data=data,
            options=options,
            version=LevitonConfigFlow.VERSION,
        )
        _LOGGER.info(
            "Successfully migrated configuration to version: %s", config_entry.version
        )

    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    data = config_entry.data
    options = config_entry.options

    conf_residences = options.get(CONF_RESIDENCES, data.get(CONF_RESIDENCES, []))
    conf_devices = options.get(CONF_DEVICES, data.get(CONF_DEVICES, []))
    conf_identifiers = [(DOMAIN, conf_id) for conf_id in conf_residences + conf_devices]

    device_registry = dr.async_get(hass)
    device_entries = dr.async_entries_for_config_entry(
        registry=device_registry,
        config_entry_id=config_entry.entry_id,
    )
    for device_entry in device_entries:
        orphan_identifiers = [
            bool(device_identifier not in conf_identifiers)
            for device_identifier in device_entry.identifiers
        ]
        if all(orphan_identifiers):
            _LOGGER.debug(
                "Removing device entry: %s (%s)", device_entry.id, device_entry.name
            )
            device_registry.async_remove_device(device_entry.id)

    conf_save_responses = options.get(
        CONF_SAVE_RESPONSES, data.get(CONF_SAVE_RESPONSES, DEFAULT_SAVE_RESPONSES)
    )
    conf_scan_interval = options.get(
        CONF_SCAN_INTERVAL, data.get(CONF_SCAN_INTERVAL, ScanInterval.DEFAULT)
    )
    conf_timeout = options.get(CONF_TIMEOUT, data.get(CONF_TIMEOUT, Timeout.DEFAULT))

    conf_save_location = DEFAULT_SAVE_LOCATION if conf_save_responses else None

    api = LevitonAPI(
        save_location=conf_save_location,
        user_id=data[CONF_ID],
        authorization=data[CONF_TOKEN],
    )

    async def async_update_data() -> LevitonData:
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            async with timeout(conf_timeout):
                return await hass.async_add_executor_job(api.update, conf_residences)
        except LevitonException as exception:
            raise UpdateFailed(
                f"Error communicating with API, Status: {exception.status_code}, Error Name: {exception.name}, Error Message: {exception.message}"
            ) from exception

    coordinator = LevitonDataUpdateCoordinator(
        hass=hass,
        logger=_LOGGER,
        config_entry=config_entry,
        name=f"Leviton Decora Smart Wi-Fi ({data[CONF_NAME]})",
        update_interval=timedelta(minutes=conf_scan_interval),
        update_method=async_update_data,
    )
    await coordinator.async_refresh()

    for residence in coordinator.data.residences:
        if residence.id in conf_residences:
            device_registry.async_get_or_create(
                config_entry_id=config_entry.entry_id,
                configuration_url=CONFIGURATION_URL,
                entry_type=dr.DeviceEntryType.SERVICE,
                identifiers={(DOMAIN, str(residence.id))},
                manufacturer=DEVICE_INFO_MANUFACTURER,
                model=DEVICE_INFO_MODEL_RESIDENCE,
                name=residence.name,
            )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = {
        CONF_RESIDENCES: conf_residences,
        CONF_DEVICES: conf_devices,
        DATA_API: api,
        DATA_COORDINATOR: coordinator,
        UNDO_UPDATE_LISTENER: config_entry.add_update_listener(async_update_listener),
    }

    websocket = await _async_start_websocket(
        hass,
        config_entry,
        coordinator,
        conf_residences,
        conf_devices,
    )
    if websocket is not None:
        hass.data[DOMAIN][config_entry.entry_id][DATA_WEBSOCKET] = websocket

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def _async_start_websocket(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    coordinator: LevitonDataUpdateCoordinator,
    conf_residences: list[int],
    conf_devices: list[int],
) -> LevitonWebSocket | None:
    """Open the MyLeviton WebSocket using the bearer already in config.

    We deliberately do NOT call ``LevitonAPI.login`` from this path:
    each re-login attempt counts toward Leviton's "too many failed
    attempts" lockout, and a flapping WebSocket will burn through them.
    Instead we synthesize the token payload from the bearer + user id
    already persisted in the config entry. If that auth fails the WebSocket
    client backs off ``AUTH_FAILURE_COOLDOWN`` (1h) before any retry.
    """
    bearer = config_entry.data.get(CONF_TOKEN)
    user_id = config_entry.data.get(CONF_ID)
    if not bearer or not user_id:
        _LOGGER.warning("Leviton WebSocket disabled: bearer/user id missing")
        return None

    @callback
    def token_provider() -> dict | None:
        # Re-read from config_entry on every reconnect so a re-auth via
        # the options flow propagates without an HA restart. Prefer the
        # full login response object captured at config-flow time — the
        # cloud's WebSocket auth historically needs the entire response, not
        # just the bearer + user id.
        full = config_entry.data.get(CONF_LOGIN_RESPONSE)
        if isinstance(full, dict) and full.get("id"):
            return full
        current = config_entry.data.get(CONF_TOKEN)
        uid = config_entry.data.get(CONF_ID)
        if not current or not uid:
            return None
        return {"id": current, "userId": uid}

    @callback
    def on_notification(notification: dict) -> None:
        if model_id := notification.get("modelId"):
            for residence in coordinator.data.residences:
                if residence.id in conf_residences:
                    for device in residence.devices:
                        if device.id in conf_devices and device.id == model_id:
                            data = notification.get("data", {})
                            device.data.update(
                                {
                                    key: value
                                    for key, value in data.items()
                                    if key in device.data
                                }
                            )
            hass.bus.async_fire(EVENT_NOTIFICATION, notification)
            async_dispatcher_send(
                hass, f"{UPDATE_NOTIFICATION}_{model_id}", notification
            )

    subs = _collect_subscriptions(coordinator, conf_residences, conf_devices)
    _LOGGER.debug(
        "Leviton WebSocket: starting client with %d subscription(s)", len(subs)
    )
    websocket = LevitonWebSocket(
        session=async_get_clientsession(hass),
        token_provider=token_provider,
        on_notification=on_notification,
    )
    websocket.set_subscriptions(subs)
    websocket.start()
    return websocket


def _collect_subscriptions(
    coordinator: LevitonDataUpdateCoordinator,
    conf_residences: list[int],
    conf_devices: list[int],
) -> list[tuple[str, int]]:
    """Build the list of (modelName, modelId) the WebSocket should subscribe to.

    Empirically the cloud delivers physical button presses on the parent
    IotSwitch as ``data.btnPress: [{button: N, trigger: T}]`` — there is
    no separate IotButton push channel, so we don't subscribe to one.
    """
    subscriptions: list[tuple[str, int]] = []
    data: LevitonData | None = coordinator.data
    if data is None:
        return subscriptions
    for residence in data.residences:
        if residence.id in conf_residences:
            subscriptions.extend(
                ("IotSwitch", device.id)
                for device in residence.devices
                if device.id in conf_devices
            )

    return subscriptions


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry=config_entry,
        platforms=PLATFORMS,
    )
    if unload_ok:
        entry_data = hass.data[DOMAIN][config_entry.entry_id]
        entry_data[UNDO_UPDATE_LISTENER]()
        if websocket := entry_data.get(DATA_WEBSOCKET):
            await websocket.stop()
        hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok


async def async_update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)
