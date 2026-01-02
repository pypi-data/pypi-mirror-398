"""Tests for configuration management."""

import os
import tempfile
from pathlib import Path

import pytest

from vmux.config import VmuxConfig, load_config, save_config


def test_tup_config_defaults():
    """Test default config values."""
    config = VmuxConfig()
    assert config.api_url == "https://vmux-api.surya.workers.dev"  # Default production URL
    assert config.auth_token is None
    assert config.env == {}


def test_load_config_from_env(monkeypatch):
    """Test loading config from environment variables."""
    monkeypatch.setenv("TUP_API_URL", "https://test.workers.dev")
    monkeypatch.setenv("TUP_AUTH_TOKEN", "test-token")
    monkeypatch.setenv("TUP_CONFIG_PATH", "/nonexistent/path")

    config = load_config()
    assert config.api_url == "https://test.workers.dev"
    assert config.auth_token == "test-token"


def test_save_and_load_config():
    """Test saving and loading config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.toml"
        os.environ["TUP_CONFIG_PATH"] = str(config_path)

        try:
            # Save config
            config = VmuxConfig(
                api_url="https://example.workers.dev",
                auth_token="secret",
                env={"WANDB_KEY": "abc123"},
            )
            save_config(config)

            # Load config
            loaded = load_config()
            assert loaded.api_url == "https://example.workers.dev"
            assert loaded.auth_token == "secret"
            assert loaded.env["WANDB_KEY"] == "abc123"
        finally:
            del os.environ["TUP_CONFIG_PATH"]


def test_env_vars_override_file(monkeypatch):
    """Test that environment variables override file config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.toml"
        monkeypatch.setenv("TUP_CONFIG_PATH", str(config_path))

        # Write config file
        config_path.write_text("""
[default]
api_url = "https://file.workers.dev"
auth_token = "file-token"
""")

        # Set env var to override
        monkeypatch.setenv("TUP_API_URL", "https://env.workers.dev")

        config = load_config()
        # API URL should come from env
        assert config.api_url == "https://env.workers.dev"
        # Auth token should come from file
        assert config.auth_token == "file-token"
