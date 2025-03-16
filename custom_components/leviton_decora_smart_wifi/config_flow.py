"""Adds config flow for Leviton Decora Smart Wi-Fi integration."""
import logging
import voluptuous as vol
from typing import Any

from homeassistant import config_entries
from homeassistant.const import (
    UnitOfTime,
    CONF_CODE,
    CONF_EMAIL,
    CONF_ID,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_TOKEN,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

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
    MAX_SCAN_INTERVAL,
    MAX_TIMEOUT,
    MIN_SCAN_INTERVAL,
    MIN_TIMEOUT,
    STEP_SCAN_INTERVAL,
    STEP_TIMEOUT,
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

    @property
    def config_title(self) -> str:
        """Return the config title."""
        return self.user_input[CONF_NAME]

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
                    vol.Required(CONF_EMAIL): TextSelector(
                        TextSelectorConfig(
                            type=TextSelectorType.EMAIL,
                        )
                    ),
                    vol.Required(CONF_PASSWORD): TextSelector(
                        TextSelectorConfig(
                            type=TextSelectorType.PASSWORD,
                        )
                    ),
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
                    vol.Required(CONF_CODE): TextSelector(
                        TextSelectorConfig(
                            type=TextSelectorType.TEXT,
                        )
                    ),
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

        residence_names = [residence.name_location for residence in self.response]

        if not residence_names:
            return await self.async_step_devices()

        return self.async_show_form(
            step_id="residences",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_RESIDENCES, default=residence_names): SelectSelector(
                        SelectSelectorConfig(
                            options=residence_names,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            sort=True,
                        )
                    ),
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
            if self.show_advanced_options:
                return await self.async_step_advanced()
            return self.async_create_entry(title=self.config_title, data=self.user_input)

        for residence in self.response:
            if residence.id == self.user_input[CONF_RESIDENCES][self.index]:
                device_names = [device.name for device in residence.devices if device.is_supported]

                if not device_names:
                    self.index += 1
                    return await self.async_step_devices()

                return self.async_show_form(
                    step_id="devices",
                    data_schema=vol.Schema(
                        {
                            vol.Optional(CONF_DEVICES, default=device_names): SelectSelector(
                                SelectSelectorConfig(
                                    options=device_names,
                                    multiple=True,
                                    mode=SelectSelectorMode.DROPDOWN,
                                    sort=True,
                                )
                            ),
                        }
                    ),
                    description_placeholders={"residence_name": residence.name_location},
                    errors=errors,
                )

    async def async_step_advanced(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.user_input[CONF_SAVE_RESPONSES] = user_input[CONF_SAVE_RESPONSES]
            self.user_input[CONF_SCAN_INTERVAL] = user_input[CONF_SCAN_INTERVAL]
            self.user_input[CONF_TIMEOUT] = user_input[CONF_TIMEOUT]
            return self.async_create_entry(title=self.config_title, data=self.user_input)

        return self.async_show_form(
            step_id="advanced",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_SAVE_RESPONSES, default=DEFAULT_SAVE_RESPONSES): BooleanSelector(),
                    vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_SCAN_INTERVAL,
                            max=MAX_SCAN_INTERVAL,
                            step=STEP_SCAN_INTERVAL,
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_TIMEOUT,
                            max=MAX_TIMEOUT,
                            step=STEP_TIMEOUT,
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Leviton Decora Smart Wi-Fi options callback."""
        return LevitonOptionsFlowHandler()


class LevitonOptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options for Leviton Decora Smart Wi-Fi."""

    def __init__(self):
        """Initialize Leviton Decora Smart Wi-Fi options flow."""
        self.coordinator = None
        self.index = 0
        self.user_input = {}

    @property
    def data(self) -> dict[str, Any]:
        """Return the data from a config entry."""
        return self.config_entry.data

    @property
    def options(self) -> dict[str, Any]:
        """Return the options from a config entry."""
        return self.config_entry.options

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        self.coordinator = self.hass.data[DOMAIN][self.config_entry.entry_id][DATA_COORDINATOR]
        return await self.async_step_residences()

    async def async_step_residences(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.user_input[CONF_RESIDENCES] = [residence.id for residence in self.coordinator.data if residence.name_location in user_input[CONF_RESIDENCES]]
            return await self.async_step_devices()

        conf_residences = [residence.name_location for residence in self.coordinator.data if residence.id in self.options.get(CONF_RESIDENCES, self.data[CONF_RESIDENCES])]
        residence_names = [residence.name_location for residence in self.coordinator.data]

        return self.async_show_form(
            step_id="residences",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_RESIDENCES, default=conf_residences): SelectSelector(
                        SelectSelectorConfig(
                            options=residence_names,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            sort=True,
                        )
                    ),
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
                conf_devices = [device.name for device in residence.devices if device.id in self.options.get(CONF_DEVICES, self.data[CONF_DEVICES])]
                device_names = [device.name for device in residence.devices if device.is_supported]

                return self.async_show_form(
                    step_id="devices",
                    data_schema=vol.Schema(
                        {
                            vol.Optional(CONF_DEVICES, default=conf_devices): SelectSelector(
                                SelectSelectorConfig(
                                    options=device_names,
                                    multiple=True,
                                    mode=SelectSelectorMode.DROPDOWN,
                                    sort=True,
                                )
                            ),
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

        conf_save_responses = self.options.get(CONF_SAVE_RESPONSES, self.data.get(CONF_SAVE_RESPONSES, DEFAULT_SAVE_RESPONSES))
        conf_scan_interval = self.options.get(CONF_SCAN_INTERVAL, self.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        conf_timeout = self.options.get(CONF_TIMEOUT, self.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT))

        return self.async_show_form(
            step_id="advanced",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_SAVE_RESPONSES, default=conf_save_responses): BooleanSelector(),
                    vol.Optional(CONF_SCAN_INTERVAL, default=conf_scan_interval): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_SCAN_INTERVAL,
                            max=MAX_SCAN_INTERVAL,
                            step=STEP_SCAN_INTERVAL,
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                    vol.Optional(CONF_TIMEOUT, default=conf_timeout): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_TIMEOUT,
                            max=MAX_TIMEOUT,
                            step=STEP_TIMEOUT,
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                }
            ),
        )
