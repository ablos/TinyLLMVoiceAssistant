import ollama
from app.config import config

async def chat(model: str, messages: list[dict], tools: list[dict] | None = None) -> ollama.Message:
    response = await ollama.AsyncClient(host=config.ollama.url).chat(
        model=model,
        messages=messages,
        tools=tools or [],
    )
    
    return response.message