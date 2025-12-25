from functools import lru_cache
from pathlib import Path

import yaml

DEFAULT_CONFIG = {
    "local_learning": True,
    "project_paths": [],
    "preferred_architecture": None,
    "include_analysis_options": True,
    "max_learn_files": 500,
    "embedding_model": "text-embedding-004",
    "api_key": None,
    "chat_model": "gemini-2.0-flash",
    "image_model": "gemini-2.0-flash",
}

CONFIG_PATH = Path.home() / ".multimodal_agent" / "config.yaml"


def ensure_config_file():
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        with open(CONFIG_PATH, "w") as f:
            yaml.dump(DEFAULT_CONFIG, f)


@lru_cache
def get_config():
    ensure_config_file()
    try:
        with open(CONFIG_PATH, "r") as f:
            user_config = yaml.safe_load(f) or {}
    except Exception:
        user_config = {}

    merged = DEFAULT_CONFIG.copy()
    merged.update(user_config)
    merged["api_key"] = _normalize(merged.get("api_key"))
    if merged.keys() != DEFAULT_CONFIG.keys():
        save_config(merged)

    return merged


def _normalize(value):
    """
    Convert YAML null, "null", "None", "", etc. to real None.
    """
    if value is None:
        return None
    if isinstance(value, str) and value.strip().lower() in (
        "null",
        "none",
        "",
    ):
        return None
    return value


def save_config(new_cfg: dict):
    """Write config to file and clear cache."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(new_cfg, f)
    get_config.cache_clear()


def set_config_field(field: str, value):
    if field not in DEFAULT_CONFIG:
        raise ValueError(f"Unknown config field: {field}")
    config = get_config().copy()
    config[field] = value
    save_config(config)
