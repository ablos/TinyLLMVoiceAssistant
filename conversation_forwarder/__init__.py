"""Conversation Forwarder integration."""
from __future__ import annotations

import json
import logging
from typing import Literal

import aiohttp

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, intent

from .const import CONF_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Conversation Forwarder from a config entry."""
    conversation.async_set_agent(hass, entry, CFAgent(hass, entry, entry.data[CONF_URL]))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    conversation.async_unset_agent(hass, entry)
    return True


class CFAgent(conversation.AbstractConversationAgent):
    """Conversation Forwarder agent."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, url: str) -> None:
        self.hass = hass
        self.entry = entry
        self.url = url

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        return MATCH_ALL

    async def _post(self, data: dict) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, json=data) as response:
                return await response.text()

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Forward the request to the external service and return the response."""
        payload = {
            "text": user_input.text,
            "conversation_id": user_input.conversation_id,
            "device_id": user_input.device_id,
            "language": user_input.language,
            "agent_id": user_input.agent_id,
        }

        _LOGGER.debug("Sending payload to %s: %s", self.url, payload)

        raw = ""
        try:
            raw = await self._post(payload)
            result = json.loads(raw)
        except aiohttp.ClientError:
            _LOGGER.warning("Unable to connect to %s", self.url)
            result = {"finish_reason": "error", "message": "Sorry, unable to connect. Check your settings."}
        except json.JSONDecodeError as e:
            _LOGGER.warning("Invalid JSON response: %s — raw: %s", e, raw)
            result = {"finish_reason": "error", "message": "Sorry, I received an invalid response. Check the logs."}

        _LOGGER.debug("Received result: %s", result)

        intent_response = intent.IntentResponse(language=user_input.language)
        intent_response.async_set_speech(result["message"])

        continue_conversation = result.get("continue_conversation", False) if result["finish_reason"] != "error" else False

        return conversation.ConversationResult(
            response=intent_response,
            conversation_id=user_input.conversation_id,
            continue_conversation=continue_conversation,
        )
