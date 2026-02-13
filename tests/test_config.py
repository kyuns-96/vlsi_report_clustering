import json

import pytest

from vlsi_report_cluster.config import get_openai_base_url, load_config


def test_load_config_none_returns_empty_dict():
    assert load_config(None) == {}


def test_load_config_reads_json_file(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps({"openai": {"base_url": "http://localhost:8080/v1"}}),
        encoding="utf-8",
    )
    result = load_config(config_file)
    assert result["openai"]["base_url"] == "http://localhost:8080/v1"


def test_load_config_raises_for_invalid_json(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text("{invalid", encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(config_file)


def test_get_openai_base_url_returns_value():
    config = {"openai": {"base_url": "http://localhost:8080/v1"}}
    assert get_openai_base_url(config) == "http://localhost:8080/v1"


def test_get_openai_base_url_missing_returns_none():
    assert get_openai_base_url({}) is None


def test_get_openai_base_url_wrong_type_raises():
    with pytest.raises(ValueError):
        get_openai_base_url({"openai": {"base_url": 123}})
