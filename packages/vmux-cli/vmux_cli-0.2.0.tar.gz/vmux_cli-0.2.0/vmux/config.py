"""Configuration management for vmux."""

import os
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

from pydantic import BaseModel

# Default production API URL - users can override via env var or config file
DEFAULT_API_URL = "https://tup-prod.experimental.sdan.io"


class VmuxConfig(BaseModel):
    """vmux configuration."""

    api_url: str = DEFAULT_API_URL
    auth_token: str | None = None
    env: dict[str, str] = {}


def get_config_path() -> Path:
    """Get the path to the vmux config file."""
    # Check for VMUX_CONFIG_PATH env var
    if config_path := os.environ.get("VMUX_CONFIG_PATH"):
        return Path(config_path)

    # Default to ~/.vmux/config.toml
    return Path.home() / ".vmux" / "config.toml"


def load_config() -> VmuxConfig:
    """Load vmux configuration from file and environment.

    Priority (highest to lowest):
    1. Environment variables (VMUX_API_URL, VMUX_AUTH_TOKEN)
    2. Config file (~/.vmux/config.toml)
    3. Defaults
    """
    config_data: dict[str, Any] = {"env": {}}

    # Load from config file if it exists
    config_path = get_config_path()
    if config_path.exists():
        with open(config_path, "rb") as f:
            file_config = tomllib.load(f)

        # Get default section
        if "default" in file_config:
            default = file_config["default"]
            if "api_url" in default:
                config_data["api_url"] = default["api_url"]
            if "auth_token" in default:
                config_data["auth_token"] = default["auth_token"]

        # Get env section (environment variables to inject into containers)
        if "env" in file_config:
            config_data["env"] = file_config["env"]

    # Override with environment variables
    if api_url := os.environ.get("VMUX_API_URL"):
        config_data["api_url"] = api_url
    if auth_token := os.environ.get("VMUX_AUTH_TOKEN"):
        config_data["auth_token"] = auth_token

    return VmuxConfig(**config_data)


def ensure_config_dir() -> Path:
    """Ensure the config directory exists and return its path."""
    config_dir = Path.home() / ".vmux"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def save_config(config: VmuxConfig) -> None:
    """Save configuration to file."""
    config_dir = ensure_config_dir()
    config_path = config_dir / "config.toml"

    lines = ["[default]"]
    if config.api_url:
        lines.append(f'api_url = "{config.api_url}"')
    if config.auth_token:
        lines.append(f'auth_token = "{config.auth_token}"')

    if config.env:
        lines.append("")
        lines.append("[env]")
        for key, value in config.env.items():
            lines.append(f'{key} = "{value}"')

    config_path.write_text("\n".join(lines) + "\n")
