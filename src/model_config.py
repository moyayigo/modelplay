import json
import os
from typing import Optional, Dict, Any


CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
CONFIG_FILE = os.path.join(CONFIG_DIR, "models.json")


DEFAULT_CONFIG = {
    "active_provider": "local",
    "providers": {
        "local": {
            "name": "本地模型 (Ollama)",
            "model": "LFM2.5-VL-1.6B-Q8_0.gguf",
            "api_url": "http://localhost:8080/v1",
            "api_key": "",
            "max_tokens": 8192,
            "timeout": 420,
        },
    },
}


def load_config() -> Dict[str, Any]:
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)

    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config
    except (json.JSONDecodeError, IOError):
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> None:
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def get_active_provider() -> Optional[Dict[str, Any]]:
    config = load_config()
    active_name = config.get("active_provider", "local")
    providers = config.get("providers", {})
    return providers.get(active_name)


def get_provider(name: str) -> Optional[Dict[str, Any]]:
    config = load_config()
    providers = config.get("providers", {})
    return providers.get(name)


def has_api_key(provider: Dict[str, Any]) -> bool:
    key = provider.get("api_key", "")
    return bool(key and key.strip())


def is_local_mode(provider: Dict[str, Any]) -> bool:
    return not has_api_key(provider)
