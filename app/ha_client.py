import asyncio
import httpx
import json
import websockets
from app.config import config

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

entities_by_area: dict[str, list[dict]] = {}    # Area ID -> Entities
floor_to_areas: dict[str, list[str]] = {}       # Floor ID -> Areas
area_name_to_id: dict[str, str] = {}
floor_name_to_id: dict[str, str] = {}
device_id_to_area: dict[str, str] = {}
global_entities: list[dict] = []

async def refresh_entities():
    # Fetch registry data via WebSocket
    results = await _ws_fetch(
        "config/device_registry/list",
        "config/entity_registry/list",
        "config/area_registry/list",
        "config/floor_registry/list",
        "homeassistant/expose_entity/list",
    )
    
    devices = results[1]
    entity_registry = results[2]
    areas = results[3]
    floors = results[4]
    exposed = results[5]["exposed_entities"]
    
    # Fetch current states via REST API
    async with httpx.AsyncClient() as client:
        states_resp = await client.get(
            f"{config.ha.url}/api/states",
            headers=_headers(),
        )
        
        states_resp.raise_for_status()
        states = { s["entity_id"]: s for s in states_resp.json() }
        
    # Build lookup maps
    new_floor_name_to_id = { f["name"]: f["floor_id"] for f in floors }
    new_area_name_to_id = { a["name"]: a["area_id"] for a in areas }
    new_floor_to_areas: dict[str, list[str]] = {}
    
    for area in areas:
        fid = area.get("floor_id")
        if fid:
            new_floor_to_areas.setdefault(fid, []).append(area["area_id"])
            
    new_device_id_to_area = {
        d["id"]: d["area_id"]
        for d in devices
        if d.get("area_id")
    }
    
    # Build entities by area (Only exposed ones)
    new_entities: dict[str, list[dict]] = {}
    
    for entry in entity_registry:
        entity_id = entry["entity_id"]
        
        # Check if exposed to Assist
        if not exposed.get(entity_id, {}).get("conversation"):
            continue
        
        # Area from entity directly, or fall back to device area
        area_id = entry.get("area_id")
        if not area_id:
            device_id = entry.get("device_id")
            area_id = new_device_id_to_area.get(device_id) if device_id else None
            
        if not area_id or entity_id not in states:
            continue
        
        state = states[entity_id]
        new_entities.setdefault(area_id, []).append({
            "entity_id": entity_id,
            "friendly_name": state["attributes"].get("friendly_name", entity_id),
            "state": state["state"]
        })
        
    # Collect exposed entities with no area into global bucket
    registered_ids = { e["entity_id"] for entries in new_entities.values() for e in entries }
    new_global_entities = []
    
    for entity_id, exposure in exposed.items():
        if not exposure.get("conversation"):
            continue
        if entity_id in registered_ids:
            continue
        if entity_id not in states:
            continue
        
        state = states[entity_id]
        new_global_entities.append({
            "entity_id": entity_id,
            "friendly_name": state["attributes"].get("friendly_name", entity_id),
            "state": state["state"],
        })
        
    global entities_by_area, floor_to_areas, area_name_to_id, floor_name_to_id, device_id_to_area, global_entities
    entities_by_area = new_entities
    floor_to_areas = new_floor_to_areas
    area_name_to_id = new_area_name_to_id
    floor_name_to_id = new_floor_name_to_id
    device_id_to_area = new_device_id_to_area
    global_entities = new_global_entities
        
async def start_entity_refresh():
    await refresh_entities()
    
    while True:
        await asyncio.sleep(300)
        await refresh_entities()
        
def get_entities_for(name: str) -> list[dict]:
    # Check if name is a floor
    floor_id = floor_name_to_id.get(name)
    
    if floor_id:
        area_ids = floor_to_areas.get(floor_id, [])
        result = []
        
        for area_id in area_ids:
            result.extend(entities_by_area.get(area_id, []))
            
        return result
    
    # Check if name is an area
    area_id = area_name_to_id.get(name)
    
    if area_id:
        return entities_by_area.get(area_id, [])
    
    return []

def get_entities_for_device(device_id: str) -> list[dict]:
    area_id = device_id_to_area.get(device_id)
    
    if not area_id:
        return list(global_entities)
    
    for name, aid in area_name_to_id.items():
        if aid == area_id:
            return get_entities_for(name) + global_entities
        
    return list(global_entities)
