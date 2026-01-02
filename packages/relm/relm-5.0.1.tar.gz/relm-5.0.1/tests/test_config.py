import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from relm.config import load_config

def test_load_config_defaults(tmp_path):
    # No config file
    config = load_config(tmp_path)
    assert config == {}

def test_load_config_valid(tmp_path):
    config_file = tmp_path / ".relm.toml"
    config_file.write_text('commit_template = "chore: release {version}"\n\n[git]\nremote = "origin"')

    config = load_config(tmp_path)
    assert config["commit_template"] == "chore: release {version}"
    assert config["git"]["remote"] == "origin"

def test_load_config_invalid_toml(tmp_path):
    config_file = tmp_path / ".relm.toml"
    config_file.write_text('invalid = "toml" = "syntax"')

    # Should probably log a warning and return empty, or raise error?
    # Let's assume it should behave safely and return empty or raise a specific error.
    # For now, let's say it raises exception or returns empty.
    # Usually better to fail fast on invalid config or warn.
    # Let's say we expect it to raise generic Exception or toml lib error
    with pytest.raises(Exception):
         load_config(tmp_path)
