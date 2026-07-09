"""Config flow for Fineme GPS Tracker integration."""

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .api import FinemeAPI, FinemeAPIError
from .const import (
    CONF_DEVICE_ID,
    CONF_DEVICE_NAME,
    CONF_KEY2018,
    CONF_MODEL,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_TIME_ZONE,
    CONF_USERNAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=10, max=300)
        ),
    }
)


class FinemeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Fineme GPS Tracker."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step - user credentials."""
        errors = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]
            scan_interval = user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

            try:
                api = FinemeAPI()
                result = await api.login(username, password)
                await api.close()
            except FinemeAPIError as err:
                _LOGGER.error("Login failed: %s", err)
                errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.exception("Unexpected error during login: %s", err)
                errors["base"] = "unknown"
            else:
                state = result.get("state")
                if str(state) != "0":
                    errors["base"] = "invalid_auth"
                else:
                    login_type = result.get("loginType")
                    if str(login_type) == "1":
                        # Device login
                        info = result.get("deviceInfo", {})
                    else:
                        # User login - get first device
                        info = result.get("deviceUser", {})

                    device_id = info.get("deviceID")
                    device_name = info.get("deviceName", "Fineme Device")
                    model = info.get("model", 513)
                    key2018 = info.get("key2018", "")
                    time_zone = info.get("timeZone", "8:00")

                    if not device_id:
                        errors["base"] = "no_device"
                    else:
                        # Check if already configured
                        await self.async_set_unique_id(str(device_id))
                        self._abort_if_unique_id_configured()

                        return self.async_create_entry(
                            title=f"{device_name} ({device_id})",
                            data={
                                CONF_USERNAME: username,
                                CONF_PASSWORD: password,
                                CONF_DEVICE_ID: int(device_id),
                                CONF_DEVICE_NAME: device_name,
                                CONF_MODEL: int(model),
                                CONF_KEY2018: key2018,
                                CONF_TIME_ZONE: time_zone,
                                CONF_SCAN_INTERVAL: scan_interval,
                            },
                        )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return FinemeOptionsFlow(config_entry)


class FinemeOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Fineme."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.data.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
                }
            ),
        )
