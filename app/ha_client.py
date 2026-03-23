import asyncio
import logging
import httpx
import json
import websockets
import pytz
from datetime import datetime
from app.config import config

logger = logging.getLogger(__name__)

def get_context_info() -> str:
    if ha_timezone:
        tz = pytz.timezone(ha_timezone)
        now = datetime.now(tz)
    else:
        now = datetime.now()
        
    time_str = now.strftime("%A, %B, %d %Y, %H:%M")
    location_str = f", Location: {ha_location}" if ha_location else ""
    return f"Time: {time_str}{location_str}"

def _headers() -> dict:
    return { "Authorization": f"Bearer {config.ha.token}" }

async def _ws_fetch(*commands: str) -> dict[int, any]:
    uri = config.ha.url.replace("http://", "ws://").replace("https://", "wss://") + "/api/websocket"
    
    async with websockets.connect(uri) as ws:
        await ws.recv()
        await ws.send(json.dumps({ "type": "auth", "access_token": config.ha.token }))
        await ws.recv()
        
        for i, command in enumerate(commands, start=1):
            await ws.send(json.dumps({ "id": i, "type": command }))
            
        results = {}
        
        for _ in commands:
            msg = json.loads(await ws.recv())
            results[msg["id"]] = msg["result"]
            
    return results

entities_by_label: dict[str, list[dict]] = {}
device_labels: dict[str, list[str]] = {}
device_media_players: dict[str, str] = {}

ha_location: str = ""
ha_timezone: str = ""
ha_tts_engine: str = ""

async def refresh_entities():
    # Fetch entities and devices
    results = await _ws_fetch(
        "config/device_registry/list",
        "config/entity_registry/list",
        "assist_pipeline/pipeline/list",
    )
    
    devices = results[1]
    entity_registry = results[2]
    pipelines = results[3]
    
    preferred = next((p for p in pipelines if p.get("is_preferred")), pipelines[0] if pipelines else None)
    
    async with httpx.AsyncClient() as client:
        # Fetch states
        states_resp = await client.get(
            f"{config.ha.url}/api/states",
            headers=_headers()
        )
        states_resp.raise_for_status()
        states = { s["entity_id"]: s for s in states_resp.json() }
        
        # Fetch location and time data
        config_resp = await client.get(
            f"{config.ha.url}/api/config",
            headers=_headers(),
        )
        config_resp.raise_for_status()
        ha_config = config_resp.json()
        
    new_device_labels = { d["id"]: d.get("labels", []) for d in devices }
    new_entities_by_label: dict[str, list[dict]] = {}
    new_device_media_players: dict[str, str] = {}
    
    for entry in entity_registry:
        entity_id = entry["entity_id"]
        
        if entry["entity_id"].startswith("media_player.") and entry.get("device_id"):
            new_device_media_players[entry["device_id"]] = entry["entity_id"]
        
        if entity_id not in states:
            continue
        
        for label in entry.get("labels", []):
            state = states[entity_id]
            new_entities_by_label.setdefault(label, []).append({
                "entity_id": entity_id,
                "friendly_name": state["attributes"].get("friendly_name", entity_id),
                "state": state["state"],
            })
            
    global entities_by_label, device_labels, device_media_players, ha_location, ha_timezone, ha_tts_engine
    entities_by_label = new_entities_by_label
    device_labels = new_device_labels
    device_media_players = new_device_media_players
    ha_location = ha_config.get("location_name", "")
    ha_timezone = ha_config.get("time_zone", "")
    ha_tts_engine = preferred["tts_engine"] if preferred else ""
    logger.info("Entity cache refreshed: %d labels, %d labeled entities", len(entities_by_label), sum(len(v) for v in entities_by_label.values()))
        
async def start_entity_refresh():
    await refresh_entities()
    
    while True:
        await asyncio.sleep(300)
        await refresh_entities()
        
def get_entities_for_device(device_id: str) -> list[dict]:
    labels = device_labels.get(device_id, [])
    seen = set()
    result = []
    
    for label in labels:
        for entity in entities_by_label.get(label, []):
            if entity["entity_id"] not in seen:
                seen.add(entity["entity_id"])
                result.append(entity)
                
    return result

async def get_live_states(entities: list[dict]) -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{config.ha.url}/api/states", headers=_headers())
        resp.raise_for_status()
        states = { s["entity_id"]: s["state"] for s in resp.json() }
        
    return [
        {**e, "state": states.get(e["entity_id"], e["state"])}
        for e in entities
    ]
    
def get_media_player(device_id: str) -> str:
    return device_media_players.get(device_id, "")

def get_tts_engine() -> str:
    return ha_tts_engine