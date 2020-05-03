import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_HOST
from homeassistant.core import callback, HomeAssistant

from . import DOMAIN, individual_config_schema, GoldairTuyaDevice
from .const import CONF_DEVICE_ID, CONF_LOCAL_KEY


class ConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
            self._abort_if_unique_id_configured()

            connect_success = await async_test_connection(user_input, self.hass)
            if connect_success:
                title = user_input[CONF_NAME]
                del user_input[CONF_NAME]
                return self.async_create_entry(title=title, data=user_input)
            else:
                errors["base"] = "connection"

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(individual_config_schema(user_input or {})), errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input=None):
        """Manage the options."""
        errors = {}
        config = {**self.config_entry.data, **self.config_entry.options}

        if user_input is not None:
            config = {**config, **user_input}
            connect_success = await async_test_connection(config, self.hass)
            if connect_success:
                return self.async_create_entry(title="", data=user_input)
            else:
                errors["base"] = "connection"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                individual_config_schema(defaults=config, options_only=True)
            ),
            errors=errors
        )

async def async_test_connection(config: dict, hass: HomeAssistant):
    device = GoldairTuyaDevice("Test", config[CONF_DEVICE_ID], config[CONF_HOST], config[CONF_LOCAL_KEY], hass)
    await device.async_refresh()
    return device.get_property("1") is not None
