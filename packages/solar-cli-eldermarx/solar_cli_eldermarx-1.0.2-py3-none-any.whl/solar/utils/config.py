"""
SOLAR CLI - Configuration Utilities
"""

import os
import yaml
from typing import Dict, Any, Optional

CONFIG_DIR = os.path.expanduser('~/.solar')
CONFIG_PATH = os.path.join(CONFIG_DIR, 'config.yaml')


def ensure_config_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)


def get_config() -> Dict[str, Any]:
    ensure_config_dir()
    if not os.path.exists(CONFIG_PATH):
        return {'api_key': None, 'default_org': 'com.solarapp', 'theme': 'dark'}
    try:
        with open(CONFIG_PATH, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def set_config(key: str, value: Any):
    ensure_config_dir()
    config = get_config()
    config[key] = value
    with open(CONFIG_PATH, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)


def get_config_value(key: str) -> Optional[Any]:
    return get_config().get(key)
