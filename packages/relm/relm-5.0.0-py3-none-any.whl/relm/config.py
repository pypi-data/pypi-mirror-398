from pathlib import Path
from typing import Dict, Any
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

def load_config(path: Path) -> Dict[str, Any]:
    """
    Loads configuration from .relm.toml in the given path.
    Returns an empty dict if the file does not exist.
    """
    config_path = path / ".relm.toml"
    if not config_path.exists():
        return {}

    with open(config_path, "rb") as f:
        return tomllib.load(f)
