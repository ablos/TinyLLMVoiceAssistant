import logging
import httpx
from typing import Mapping, Any
from app.config import config
from app.ollama_client import chat
from app.ha_client import get_entities_for_device
from app.session import get_session, add_to_session

logger = logging.getLogger(__name__)

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
        await _call_ha_service("scene", "turn_on", { "entity_id": args["entity_id"] })
        
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
    from app.tools import HA_DOMAIN_TOOLS
    seen = set()
    tools = []
    
    for e in entities:
        domain = e["entity_id"].split(".")[0]
        
        for tool in HA_DOMAIN_TOOLS.get(domain, []):
            name = tool["function"]["name"]
            
            if name not in seen:
                seen.add(name)
                tools.append(tool)
                
    return tools
        
async def run(text: str, device_id: str, intent: str) -> str:
    entities = get_entities_for_device(device_id)
    session = get_session(device_id)
    
    # Build system prompt
    if intent == "ha_control":
        entity_list = "\n".join(
            f"- {e['entity_id']} ({e['friendly_name']}, state: {e['state']})"
            for e in entities
        )
        
        system_prompt = f"""
            You are a Home Assistant voice assistant. Control devices using the provided tools.
            Available entities:
            {entity_list}
            
            Use the exact entity_id when calling tools. Be brief in your responses.
        """
        tools = _tools_for_entities(entities)
        logger.info("Tools: %s", [t["function"]["name"] for t in tools])
        
    elif intent == "search":
        system_prompt = """
            You are a helpful voice assistant. Answer based on search results provided.
        """
        
        tools = []
        
    else:
        system_prompt = """
            You are a helpful voice assistant. Answer consisely.
        """
        tools = []
    
    # Build messages - no history for ha_control, it causes confusion
    messages = [{ "role": "system", "content": system_prompt }]
    if intent != "ha_control":
        messages.extend(session.messages)
    messages.append({ "role": "user", "content": text })

    logger.info("Context: %d entities, %d history messages", len(entities), len(session.messages))
    logger.debug("Entities: %s", [e['friendly_name'] for e in entities])

    # Call LLM
    response = await chat(config.ollama.main_model, messages, tools)
    
    # Execute tool calls if any
    if response.tool_calls:
        for tool_call in response.tool_calls:
            logger.info("Tool call: %s(%s)", tool_call.function.name, dict(tool_call.function.arguments))
            await _execute_tool(tool_call.function.name, tool_call.function.arguments)
        reply = response.content or "Done."
    else:
        reply = response.content or "I'm not sure how to help with that."
        
    add_to_session(device_id, text, reply)
    return reply
        