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
    keep_alive: str = "-1"
    
@dataclass
class SearXNGConfig:
    url: str
    
@dataclass
class Config:
    ha: HAConfig
    ollama: OllamaConfig
    searxng: SearXNGConfig
    
def load_config(path: str = "config.yaml") -> Config:
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
            keep_alive=os.getenv("OLLAMA_KEEP_ALIVE", raw.get("ollama", {}).get("keep_alive", "-1")),
        ),
        searxng=SearXNGConfig(
            url=os.getenv("SEARXNG_URL", raw.get("searxng", {}).get("url", "")),
        )
    )
    
config = load_config()