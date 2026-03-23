import asyncio
import logging
import httpx
import json
import websockets
from app.config import config

logger = logging.getLogger(__name__)

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

async def refresh_entities():
    results = await _ws_fetch(
        "config/device_registry/list",
        "config/entity_registry/list",
    )
    
    devices = results[1]
    entity_registry = results[2]
    
    async with httpx.AsyncClient() as client:
        states_resp = await client.get(
            f"{config.ha.url}/api/states",
            headers=_headers()
        )
        states_resp.raise_for_status()
        states = { s["entity_id"]: s for s in states_resp.json() }
        
    new_device_labels = { d["id"]: d.get("labels", []) for d in devices }
    new_entities_by_label: dict[str, list[dict]] = {}
    
    for entry in entity_registry:
        entity_id = entry["entity_id"]
        
        if entity_id not in states:
            continue
        
        for label in entry.get("labels", []):
            state = states[entity_id]
            new_entities_by_label.setdefault(label, []).append({
                "entity_id": entity_id,
                "friendly_name": state["attributes"].get("friendly_name", entity_id),
                "state": state["state"],
            })
            
    global entities_by_label, device_labels
    entities_by_label = new_entities_by_label
    device_labels = new_device_labels
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