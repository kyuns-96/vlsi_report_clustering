import json
from pathlib import Path
from typing import Any


def load_config(config_file: Path | None) -> dict[str, Any]:
    if config_file is None:
        return {}

    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")

    with open(config_file, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON config file: {config_file}. {e}") from e

    if not isinstance(data, dict):
        raise ValueError("Config file must contain a JSON object")

    return data


def get_openai_base_url(config: dict[str, Any]) -> str | None:
    openai_config = _get_openai_config(config)

    base_url = openai_config.get("base_url")
    if base_url is None:
        return None
    if not isinstance(base_url, str):
        raise ValueError("Config key 'openai.base_url' must be a string")

    normalized = base_url.strip()
    if not normalized:
        return None
    return normalized


def get_openai_api_key(config: dict[str, Any]) -> str | None:
    openai_config = _get_openai_config(config)

    api_key = openai_config.get("api_key")
    if api_key is None:
        return None
    if not isinstance(api_key, str):
        raise ValueError("Config key 'openai.api_key' must be a string")

    normalized = api_key.strip()
    if not normalized:
        return None
    return normalized


def _get_openai_config(config: dict[str, Any]) -> dict[str, Any]:
    if not config:
        return {}
    openai_config = config.get("openai")
    if openai_config is None:
        return {}
    if not isinstance(openai_config, dict):
        raise ValueError("Config key 'openai' must be an object")
    return openai_config
