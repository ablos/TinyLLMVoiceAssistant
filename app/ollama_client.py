import ollama
from app.config import config

async def chat(model: str, messages: list[dict], tools: list[dict] | None = None) -> ollama.Message:
    kwargs = {
        "model": model,
        "messages": messages,
        "tools": tools or [],
    }
    if config.ollama.keep_alive:
        kwargs["keep_alive"] = config.ollama.keep_alive
    if config.ollama.num_ctx:
        kwargs["options"] = {"num_ctx": config.ollama.num_ctx}

    response = await ollama.AsyncClient(host=config.ollama.url).chat(**kwargs)
    return response.message
