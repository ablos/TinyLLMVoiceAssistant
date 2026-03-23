import os
import yaml
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

@dataclass
class HAConfig:
    url: str
    token: str
    
@dataclass
class OllamaConfig:
    url: str
    main_model: str
    router_model: str
    keep_alive: str = ""
    num_ctx: int = 0
    
@dataclass
class SearXNGConfig:
    url: str
    
@dataclass
class AppConfig:
    max_message_history: int = 8
    max_search_results: int = 5
    
@dataclass
class Config:
    ha: HAConfig
    ollama: OllamaConfig
    searxng: SearXNGConfig
    app: AppConfig
    devices: dict[str, dict] = field(default_factory=dict)
    
def load_config(path: str = "data/config.yaml") -> Config:
    try:
        with open(path) as f:
            raw = yaml.safe_load(f) or {}
    except FileNotFoundError:
        raw = {}

    return Config(
        ha=HAConfig(
            url=os.getenv("HA_URL", raw.get("ha", {}).get("url", "")),
            token=os.getenv("HA_TOKEN", raw.get("ha", {}).get("token", "")),
        ),
        ollama=OllamaConfig(
            url=os.getenv("OLLAMA_URL", raw.get("ollama", {}).get("url", "")),
            main_model=os.getenv("OLLAMA_MAIN_MODEL", raw.get("ollama", {}).get("main_model", "")),
            router_model=os.getenv("OLLAMA_ROUTER_MODEL", raw.get("ollama", {}).get("router_model", "")),
            keep_alive=os.getenv("OLLAMA_KEEP_ALIVE", raw.get("ollama", {}).get("keep_alive", "")),
            num_ctx=int(os.getenv("OLLAMA_NUM_CTX", raw.get("ollama", {}).get("num_ctx", 0))),
        ),
        searxng=SearXNGConfig(
            url=os.getenv("SEARXNG_URL", raw.get("searxng", {}).get("url", "")),
        ),
        app=AppConfig(
            max_message_history=int(os.getenv("MAX_MESSAGE_HISTORY", raw.get("app", {}).get("max_message_history", 8))),
            max_search_results=int(os.getenv("MAX_SEARCH_RESULTS", raw.get("app", {}).get("max_search_results", 5))),
        ),
        devices=raw.get("devices", {})
    )
    
config = load_config()