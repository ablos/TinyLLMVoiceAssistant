import logging
from app.config import config
from app.ollama_client import chat
from app.ha_client import get_context_info

CLASSIFY_PROMPT = """
    You are an intent classifier for a Home Assistant voice assistant.
    Classify the user's message into exactly one of these intents:
    
    - ha_control: The user wants to control a Home Assistant device (lights, thermostat, scenes, switches, etc.)
    - search: The user wants to look something up on the internet or requires time sensitive knowledge
    - timer: The user wants to set a timer or reminder (e.g. "set a timer for 10 minutes", "remind me in 5 minutes to take out the pizza")
    - general: Anything else (questions, conversation, calculations, etc.) including questions about current time or date, since that information is already provided.
    
    Respond with only the intent label. Exception: if the intent is "search", respond with "search|<optimized search query>".
    No explanation, no punctuation.
"""

logger = logging.getLogger(__name__)

async def classify(text: str) -> tuple[str, str]:
    messages = [
        { "role": "system", "content": f"{CLASSIFY_PROMPT}\n{get_context_info()}" },
        { "role": "user", "content": text }
    ]
    
    response = await chat(config.ollama.router_model, messages)
    result = (response.content or "").strip().lower()
    
    logger.info("Router output: " + result)
    
    if result.startswith("search|"):
        _, query = result.split("|", 1)
        return "search", query.strip()
    
    if result not in ("ha_control", "search", "timer", "general"):
        return "general", text
    
    return result, text