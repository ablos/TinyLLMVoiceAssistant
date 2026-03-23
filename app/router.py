from app.config import config
from app.ollama_client import chat
from app.ha_client import get_context_info

CLASSIFY_PROMPT = """
    You are an intent classifier for a Home Assistant voice assistant.
    Classify the user's message into exactly one of these intents:
    
    - ha_control: The user wants to control a Home Assistant device (lights, thermostat, scenes, switches, etc.)
    - search: The user wants to look something up on the internet or requires time sensitive knowledge
    - general: Anything else (questions, conversation, calculations, etc.)
    
    Respond with only the intent label. Exception: if the intent is "search", respond with "search|<optimized search query>".
    No explanation, no punctuation.
"""


async def classify(text: str) -> tuple[str, str]:
    messages = [
        { "role": "system", "content": f"{CLASSIFY_PROMPT}\n{get_context_info()}" },
        { "role": "user", "content": text }
    ]
    
    response = await chat(config.ollama.router_model, messages)
    result = (response.content or "").strip().lower()
    
    if result.startswith("search|"):
        _, query = result.split("|", 1)
        return "search", query.strip()
    
    if result not in ("ha_control", "search", "general"):
        return "general", text
    
    return result, text