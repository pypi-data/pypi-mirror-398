import yaml
from pathlib import Path
from typing import Dict, Any
import json
import os
from ..utils.string_utils import to_snake_case

def load_json(path):
    with open(path) as f:
        return json.load(f)

def load_env(prefix=""):
    prefix = to_snake_case(prefix)
    return {f"{k[len(prefix):]}".lower(): v for k, v in os.environ.items() if k.startswith(prefix.upper()) or k.startswith(prefix.lower())}

def load_config() -> Dict[str, Any]:
    """Load configuration from YAML file"""
    config_path = Path.cwd() / 'config' / 'config.yaml' or Path(__file__).parent.parent / 'config' / 'config.yaml'
    print(f"Path : {config_path}", flush=True)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    print(f"Loaded configuration from {config_path}", flush=True)

    return config


def get_config_value(key: str, default: Any = None) -> Any:
    """Get a specific configuration value"""
    config = load_config()

    keys = key.split('.')
    value = config

    for k in keys:
        if isinstance(value, dict):
            value = value.get(k, default)
        else:
            return default

    return value