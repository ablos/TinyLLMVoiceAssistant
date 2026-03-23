TURN_ON = {
    "type": "function",
    "function": {
        "name": "turn_on",
        "description": "Turn on a device or light",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The entity_id of the device to turn on"
                }
            },
            "required": ["entity_id"]
        }
    }
}

TURN_OFF = {
    "type": "function",
    "function": {
        "name": "turn_off",
        "description": "Turn off a device or light",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The entity_id of the device to turn off"
                }
            },
            "required": ["entity_id"]
        }
    }
}

ACTIVATE_SCENE = {
    "type": "function",
    "function": {
        "name": "activate_scene",
        "description": "Activates a scene",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The entity_id of the scene to activate"
                }
            },
            "required": ["entity_id"]
        }
    }
}

SET_LIGHT = {
    "type": "function",
    "function": {
        "name": "set_light",
        "description": "Set brightness, color temperature, or RGB color of a light",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The entity_id of the light"
                },
                "brightness": {
                    "type": "integer",
                    "description": "Brightness level (0-255)"
                },
                "color_temp": {
                    "type": "integer",
                    "description": "Color temperature in mireds"
                },
                "color": {
                    "type": "object",
                    "description": "RGB Color",
                    "properties": {
                        "r": {"type": "integer"},
                        "g": {"type": "integer"},
                        "b": {"type": "integer"}
                    }
                }
            },
            "required": ["entity_id"]
        }
    }
}

SET_TEMPERATURE = {
    "type": "function",
    "function": {
        "name": "set_temperature",
        "description": "Set the temperature in C",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The entity_id of the thermostat"  
                },
                "temperature": {
                    "type": "integer",
                    "description": "Temperature between 10 and 30 C"
                }
            },
            "required": ["entity_id", "temperature"]
        }
    }
}

HA_TOOLS: dict[str, list[dict]] = {
    "light": [TURN_ON, TURN_OFF, SET_LIGHT],
    "switch": [TURN_ON, TURN_OFF],
    "media_player": [TURN_ON, TURN_OFF],
    "input_boolean": [TURN_ON, TURN_OFF],
    "scene": [ACTIVATE_SCENE],
    "climate": [SET_TEMPERATURE],
}

SEARCH = {
    "type": "function",
    "function": {
        "name": "search",
        "description": "Search the internet for current information",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "categories": {
                    "type": "string",
                    "description": "Comma-separated search categories, e.g. 'general', 'news', 'science'",
                }
            },
            "required": ["query"]
        }
    }
}

SEARCH_TOOLS = []