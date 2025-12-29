"""Configuration management for ORQ CLI."""

import os
from pathlib import Path
from typing import Optional

import yaml

CONFIG_DIR = Path.home() / ".orq"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

DEFAULT_CONFIG = {
    "api_key": None,
    "environment": "production",
    "output_format": "table",
}


def ensure_config_dir() -> None:
    """Ensure config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """Load configuration from file."""
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()

    with open(CONFIG_FILE) as f:
        config = yaml.safe_load(f) or {}

    result = DEFAULT_CONFIG.copy()
    result.update(config)
    return result


def save_config(config: dict) -> None:
    """Save configuration to file."""
    ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def get_api_key(override: Optional[str] = None) -> Optional[str]:
    """Get API key from override, env var, or config file."""
    if override:
        return override

    env_key = os.environ.get("ORQ_API_KEY")
    if env_key:
        return env_key

    config = load_config()
    return config.get("api_key")


def get_environment(override: Optional[str] = None) -> str:
    """Get environment from override, env var, or config file."""
    if override:
        return override

    env_val = os.environ.get("ORQ_ENVIRONMENT")
    if env_val:
        return env_val

    config = load_config()
    return config.get("environment", "production")


def get_output_format(override: Optional[str] = None) -> str:
    """Get output format from override or config file."""
    if override:
        return override

    config = load_config()
    return config.get("output_format", "table")
