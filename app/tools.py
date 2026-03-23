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
    "climate": [SET_TEMPERATURE]
}

SET_TIMER = {
    "type": "function",
    "function": {
        "name": "set_timer",
        "description": "Set a timer or reminder",
        "parameters": {
            "type": "object",
            "properties": {
                "duration_seconds": {
                    "type": "integer",
                    "description": "Duration of the timer in seconds"
                },
                "confirmation": {
                    "type": "string",
                    "description": "Confirmation to speak immediately, matching the user's phrasing. E.g. if the user said 'remind me', say 'I will remind you in 10 minutes to take out the pizza!'. If the user said 'set a timer', say 'Timer set for 10 minutes!'"
                },
                "completion_message": {
                    "type": "string",
                    "description": "Message to speak when the timer finishes, e.g. 'Time to take out the pizza!' or 'Time to leave!'"
                }
            },
            "required": ["duration_seconds", "confirmation", "completion_message"]
        }
    }
}