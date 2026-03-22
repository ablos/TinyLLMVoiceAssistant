"""Config flow for Conversation Forwarder."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries

from .const import CONF_URL, DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_URL, default="http://ha-voice-agent:8000/conversation"): str,
})


class ConversationForwarderConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Conversation Forwarder."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title="Conversation Forwarder", data=user_input)

        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return OptionsFlow(config_entry)


class OptionsFlow(config_entries.OptionsFlow):
    """Handle options for Conversation Forwarder."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self.hass.config_entries.async_update_entry(self.config_entry, data=user_input)
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_URL, default=self.config_entry.data.get(CONF_URL, "")): str,
        })

        return self.async_show_form(step_id="init", data_schema=schema)
