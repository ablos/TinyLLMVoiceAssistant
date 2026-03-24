import re
import ollama
from app.config import config

_EMOJI_RE = re.compile(r'[\U00010000-\U0010FFFF\u2600-\u27BF\u2300-\u23FF\u2700-\u27BF\uFE00-\uFE0F]')

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
    msg = response.message
    
    # Strip off any emoji's
    if msg.content:
        msg.content = _EMOJI_RE.sub('', msg.content).strip()
    
    return msg
