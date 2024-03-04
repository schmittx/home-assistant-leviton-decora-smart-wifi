"""Adds config flow for Leviton Decora Smart Wi-Fi integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_CODE,
    CONF_EMAIL,
    CONF_ID,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_TOKEN,
)
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .api import LOGIN_CODE_REQUIRED, LOGIN_SUCCESS, LevitonAPI, LevitonException
from .const import (
    CONF_DEVICES,
    CONF_RESIDENCES,
    CONF_SAVE_RESPONSES,
    CONF_TIMEOUT,
    DATA_COORDINATOR,
    DEFAULT_SAVE_RESPONSES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    VALUES_SCAN_INTERVAL,
    VALUES_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class LevitonConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Leviton Decora Smart Wi-Fi integration."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self.api = None
        self.index = 0
        self.response = None
        self.user_input = {}

    async def async_finish_login(self, errors):
        await self.async_set_unique_id(self.api.user_id)
        self._abort_if_unique_id_configured()

        try:
            self.response = await self.hass.async_add_executor_job(self.api.update)
        except LevitonException as exception:
            errors["base"] = "update_failed"

        self.user_input[CONF_ID] = self.api.user_id
        self.user_input[CONF_NAME] = self.api.user_name
        self.user_input[CONF_TOKEN] = self.api.authorization

        return await self.async_step_residences()

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:

            self.user_input[CONF_EMAIL] = user_input[CONF_EMAIL]
            self.user_input[CONF_PASSWORD] = user_input[CONF_PASSWORD]
            self.api = LevitonAPI()

            result = await self.hass.async_add_executor_job(
                self.api.login,
                self.user_input[CONF_EMAIL],
                self.user_input[CONF_PASSWORD],
            )

            if result == LOGIN_CODE_REQUIRED:
                _LOGGER.debug(f"Two factor authentication is required for the account")
                return await self.async_step_authenticate()
            elif result == LOGIN_SUCCESS:
                _LOGGER.debug(f"Login successful")
                return await self.async_finish_login(errors)
            errors["base"] = result

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): cv.string,
                    vol.Required(CONF_PASSWORD): cv.string,
                }
            ),
            errors=errors,
        )

    async def async_step_authenticate(self, user_input=None):
        errors = {}

        if user_input is not None:

            self.user_input[CONF_CODE] = user_input[CONF_CODE]
            self.api = LevitonAPI()

            result = await self.hass.async_add_executor_job(
                self.api.login,
                self.user_input[CONF_EMAIL],
                self.user_input[CONF_PASSWORD],
                self.user_input[CONF_CODE],
            )

            if result == LOGIN_SUCCESS:
                _LOGGER.debug(f"Login successful")
                return await self.async_finish_login(errors)
            errors["base"] = result

        return self.async_show_form(
            step_id="authenticate",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CODE): cv.string,
                }
            ),
            description_placeholders={"email": self.user_input[CONF_EMAIL]},
            errors=errors,
        )

    async def async_step_residences(self, user_input=None):
        errors = {}

        if user_input is not None:

            self.user_input[CONF_RESIDENCES] = []

            for residence in self.response:
                if residence.name_location in user_input[CONF_RESIDENCES]:
                    self.user_input[CONF_RESIDENCES].append(residence.id)

            return await self.async_step_devices()

        residence_names = sorted([residence.name_location for residence in self.response])

        if not residence_names:
            return await self.async_step_devices()

        return self.async_show_form(
            step_id="residences",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_RESIDENCES, default=residence_names): cv.multi_select(residence_names),
                }
            ),
            errors=errors,
        )

    async def async_step_devices(self, user_input=None):
        errors = {}

        if user_input is not None:

            if not self.user_input.get(CONF_DEVICES):
                self.user_input[CONF_DEVICES] = []

            for residence in self.response:
                if residence.id == self.user_input[CONF_RESIDENCES][self.index]:
                    for device in residence.devices:
                        if device.name in user_input[CONF_DEVICES]:
                            self.user_input[CONF_DEVICES].append(device.id)
                    self.index += 1

        if self.index == len(self.user_input[CONF_RESIDENCES]):
            self.index = 0
            return self.async_create_entry(title=self.user_input[CONF_NAME], data=self.user_input)

        for residence in self.response:
            if residence.id == self.user_input[CONF_RESIDENCES][self.index]:
                device_names = sorted(device.name for device in residence.devices)

                if not device_names:
                    self.index += 1
                    return await self.async_step_devices()

                return self.async_show_form(
                    step_id="devices",
                    data_schema=vol.Schema(
                        {
                            vol.Required(CONF_DEVICES, default=device_names): cv.multi_select(device_names),
                        }
                    ),
                    description_placeholders={"residence_name": residence.name_location},
                    errors=errors,
                )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Leviton Decora Smart Wi-Fi options callback."""
        return LevitonOptionsFlowHandler(config_entry)


class LevitonOptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options for Leviton Decora Smart Wi-Fi."""

    def __init__(self, config_entry):
        """Initialize Leviton Decora Smart Wi-Fi options flow."""
        self.coordinator = None
        self.config_entry = config_entry
        self.data = config_entry.data
        self.index = 0
        self.options = config_entry.options
        self.user_input = {}

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        self.coordinator = self.hass.data[DOMAIN][self.config_entry.entry_id][DATA_COORDINATOR]
        return await self.async_step_residences()

    async def async_step_residences(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.user_input[CONF_RESIDENCES] = [residence.id for residence in self.coordinator.data if residence.name_location in user_input[CONF_RESIDENCES]]
            return await self.async_step_devices()

        conf_residences = sorted([residence.name_location for residence in self.coordinator.data if residence.id in self.options.get(CONF_RESIDENCES, self.data[CONF_RESIDENCES])])
        residence_names = sorted([residence.name_location for residence in self.coordinator.data])

        return self.async_show_form(
            step_id="residences",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_RESIDENCES, default=conf_residences): cv.multi_select(residence_names),
                }
            ),
        )

    async def async_step_devices(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            for residence in self.coordinator.data:
                if residence.id == self.user_input[CONF_RESIDENCES][self.index]:
                    self.user_input[CONF_DEVICES].extend([device.id for device in residence.devices if device.name in user_input[CONF_DEVICES]])
                    self.index += 1

        if self.index == len(self.user_input[CONF_RESIDENCES]):
            if self.show_advanced_options:
                return await self.async_step_advanced()
            return self.async_create_entry(title="", data=self.user_input)
        elif self.index == 0:
            self.user_input[CONF_DEVICES] = []

        for residence in self.coordinator.data:
            if residence.id == self.user_input[CONF_RESIDENCES][self.index]:
                conf_devices = sorted([device.name for device in residence.devices if device.id in self.options.get(CONF_DEVICES, self.data[CONF_DEVICES])])
                device_names = sorted(device.name for device in residence.devices)

                return self.async_show_form(
                    step_id="devices",
                    data_schema=vol.Schema(
                        {
                            vol.Required(CONF_DEVICES, default=conf_devices): cv.multi_select(device_names),
                        }
                    ),
                    description_placeholders={"residence_name": residence.name_location},
                )

    async def async_step_advanced(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.user_input[CONF_SAVE_RESPONSES] = user_input[CONF_SAVE_RESPONSES]
            self.user_input[CONF_SCAN_INTERVAL] = user_input[CONF_SCAN_INTERVAL]
            self.user_input[CONF_TIMEOUT] = user_input[CONF_TIMEOUT]
            return self.async_create_entry(title="", data=self.user_input)

        default_save_responses = self.options.get(CONF_SAVE_RESPONSES, DEFAULT_SAVE_RESPONSES)
        default_scan_interval = self.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        default_timeout = self.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)

        return self.async_show_form(
            step_id="advanced",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SAVE_RESPONSES, default=default_save_responses): cv.boolean,
                    vol.Required(CONF_SCAN_INTERVAL, default=default_scan_interval): vol.In(VALUES_SCAN_INTERVAL),
                    vol.Required(CONF_TIMEOUT, default=default_timeout): vol.In(VALUES_TIMEOUT),
                }
            ),
        )
