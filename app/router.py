from app.config import config
from app.ollama_client import chat

CLASSIFY_PROMPT = """
    You are an intent classifier for a Home Assistant voice assistant.
    Classify the user's message into exactly one of these intents:
    
    - ha_control: The user wants to control a Home Assistant device (lights, thermostat, scenes, switches, etc.)
    - search: The user wants to look something up on the internet or requires time sensitive knowledge
    - general: Anything else (questions, conversation, calculations, etc.)
    
    Respond with only the intent label, nothing else. No explanation, no punctuation.
"""


async def classify(text: str) -> str:
    messages = [
        { "role": "system", "content": CLASSIFY_PROMPT },
        { "role": "user", "content": text }
    ]
    
    response = await chat(config.ollama.router_model, messages)
    result = (response.content or "").strip().lower()
    
    if result not in ("ha_control", "search", "general"):
        return "general"
    
    return result