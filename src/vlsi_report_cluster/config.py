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
    if not config:
        return None

    openai_config = config.get("openai")
    if openai_config is None:
        return None
    if not isinstance(openai_config, dict):
        raise ValueError("Config key 'openai' must be an object")

    base_url = openai_config.get("base_url")
    if base_url is None:
        return None
    if not isinstance(base_url, str):
        raise ValueError("Config key 'openai.base_url' must be a string")

    normalized = base_url.strip()
    if not normalized:
        return None
    return normalized
