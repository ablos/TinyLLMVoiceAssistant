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
    
@dataclass
class SearXNGConfig:
    url: str
    
@dataclass
class Config:
    ha: HAConfig
    ollama: OllamaConfig
    searxng: SearXNGConfig
    
def load_config(path: str = "config.yaml") -> Config:
    with open(path) as f:
        raw = yaml.safe_load(f)
        
    return Config(
        ha=HAConfig(
            url=os.getenv("HA_URL", raw["ha"]["url"]),
            token=os.getenv("HA_TOKEN", raw["ha"]["token"]),
        ),
        ollama = OllamaConfig(
            url=os.getenv("OLLAMA_URL", raw["ollama"]["url"]),
            main_model=os.getenv("OLLAMA_MAIN_MODEL", raw["ollama"]["main_model"]),
            router_model=os.getenv("OLLAMA_ROUTER_MODEL", raw["ollama"]["router_model"]),
        ),
        searxng=SearXNGConfig(
            url=os.getenv("SEARXNG_URL", raw["searxng"]["url"]),
        )
    )
    
config = load_config()