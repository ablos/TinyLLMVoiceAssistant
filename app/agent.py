import os
import logging
import httpx
import asyncio
from typing import Mapping, Any
from mutagen import File
from app.config import config
from app.ollama_client import chat
from app.ha_client import get_entities_for_device, get_context_info, get_live_states, get_media_player, get_tts_engine
from app.session import get_session, add_to_session
from app.tools import HA_TOOLS, SET_TIMER
from app.search import search
from app.confirmations import get_confirmation

logger = logging.getLogger(__name__)

_timer_sound_path = "sounds/timer.wav"
_timer_sound_duration: float = File(_timer_sound_path).info.length if os.path.exists(_timer_sound_path) else 1.0

async def _call_ha_service(domain: str, service: str, data: dict) -> None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(
            f"{config.ha.url}/api/services/{domain}/{service}",
            headers={"Authorization": f"Bearer {config.ha.token}"},
            json=data,
        )
        
async def _execute_tool(tool_name: str, args: Mapping[str, Any]) -> None:
    if tool_name == "turn_on":
        await _call_ha_service("homeassistant", "turn_on", { "entity_id": args["entity_id"] })
    
    elif tool_name == "turn_off":
        await _call_ha_service("homeassistant", "turn_off", { "entity_id": args["entity_id"] })
        
    elif tool_name == "activate_scene":
        await _call_ha_service("scene", "turn_on", { "entity_id": args["entity_id"], "transition": 3 })
        
    elif tool_name == "set_light":
        data = { "entity_id": args["entity_id"] }
        
        if "brightness" in args:
            data["brightness"] = args["brightness"]
        if "color_temp" in args:
            data["color_temp"] = args["color_temp"]
        if "color" in args:
            data["rgb_color"] = [ args["color"]["r"], args["color"]["g"], args["color"]["b"] ]
            
        await _call_ha_service("light", "turn_on", data)
        
    elif tool_name == "set_temperature":
        await _call_ha_service("climate", "set_temperature", {
            "entity_id": args["entity_id"],
            "temperature": args["temperature"],
        })
        
def _tools_for_entities(entities: list[dict]) -> list[dict]:
    seen = set()
    tools = []
    
    for e in entities:
        domain = e["entity_id"].split(".")[0]
        
        for tool in HA_TOOLS.get(domain, []):
            name = tool["function"]["name"]
            
            if name not in seen:
                seen.add(name)
                tools.append(tool)
                
    return tools

async def _speak(device_id: str, message: str) -> None:
    media_player = get_media_player(device_id)
    
    if not media_player:
        logger.warning("No media player found for device %s", device_id)
        return
    
    await _call_ha_service("tts", "speak", {
        "entity_id": get_tts_engine(),
        "media_player_entity_id": media_player,
        "message": message,
    })
    
async def _run_timer(device_id: str, duration_seconds: int, completion_message: str) -> None:
    await asyncio.sleep(duration_seconds)
    logger.info("Timer finished for device %s: %s", device_id, completion_message)
    media_player = get_media_player(device_id)
    
    if media_player:
        await _call_ha_service("media_player", "play_media", {
            "entity_id": media_player,
            "media_content_id": f"{config.app.server_url}/{_timer_sound_path}",
            "media_content_type": "music",
        })
        await asyncio.sleep(_timer_sound_duration + 0.2)
    
    await _speak(device_id, completion_message)
        
async def run(text: str, device_id: str, intent: str, query: str = "") -> str:
    entities = get_entities_for_device(device_id)
    session = get_session(device_id, intent)
    
    # Build system prompt
    if intent == "ha_control":
        entities = await get_live_states(entities)
        
        entity_list = "\n".join(
            f"- {e['entity_id']} ({e['friendly_name']}, area: {e['area'] or 'unknown'}, state: {e['state']})"
            for e in entities
        )
        
        system_prompt = f"""
            You are a Home Assistant voice assistant. Control devices using the provided tools.
            Available entities:
            {entity_list}
            
            Use the exact entity_id when calling tools. Be brief in your responses.
            When the intent is ambiguous (e.g. "lights on", "light's on"), treat it as a command, not a status query.
        """
        
        tools = _tools_for_entities(entities)
        logger.info("Tools: %s", [t["function"]["name"] for t in tools])
        
    elif intent == "search":
        search_results = await search(query or text)
        
        system_prompt = f"""
            [{get_context_info()}]
        
            You are a helpful voice assistant.
            Answer the user's question based on the following search results.
            Be concise, one or two sentences, suitable for voice.
            
            Search results:
            {search_results}
        """
        
        tools = []
        
    elif intent == "timer":
        system_prompt = """
            You are a helpful voice assistant. The user want to set a timer or reminder.
            Call the set_timer tool with the correct duration, a short confirmation, and a natural completion message for voice.
        """
        
        tools = [SET_TIMER]
        
    else:
        system_prompt = f"""
            [{get_context_info()}]
        
            You are a helpful voice assistant. Answer consisely.
        """
        tools = []
    
    # Add custom instructions from config.yaml
    custom_instructions = config.devices.get(device_id, {}).get(intent, "")
    if custom_instructions:
        system_prompt += f"\n\n{custom_instructions}"
        logger.info("Custom instructions applied for %s", device_id)
    
    # Build messages - no history for ha_control, it causes confusion
    messages = [{ "role": "system", "content": system_prompt }]
    if intent not in ("ha_control", "timer"):
        messages.extend(session.messages)
    messages.append({ "role": "user", "content": text })

    logger.info("Context: %d entities, %d history messages", len(entities), len(session.messages))
    logger.debug("Entities: %s", [e['friendly_name'] for e in entities])

    # Call LLM
    response = await chat(config.ollama.main_model, messages, tools)
    
    # Execute tool calls if any
    if response.tool_calls:
        reply = response.content or get_confirmation()
        tasks = []
        
        for tool_call in response.tool_calls:
            logger.info("Tool call: %s(%s)", tool_call.function.name, dict(tool_call.function.arguments))
            
            if tool_call.function.name == "set_timer":
                args = tool_call.function.arguments
                asyncio.create_task(_run_timer(device_id, args["duration_seconds"], args["completion_message"]))
                reply = args["confirmation"]
            else:
                tasks.append(_execute_tool(tool_call.function.name, tool_call.function.arguments))
                
        for task in tasks:
            asyncio.create_task(task)

    else:
        reply = response.content or "I'm not sure how to help with that."
        
    if intent not in ("ha_control", "timer"):
        add_to_session(device_id, text, reply, intent)
        
    return reply
        