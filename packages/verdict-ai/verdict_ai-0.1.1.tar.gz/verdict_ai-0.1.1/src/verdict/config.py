"""Configuration management for Verdict."""

import os
from pathlib import Path
from typing import Optional

import yaml


class Config:
    """Manages Verdict configuration and API keys."""

    DEFAULT_CONFIG_PATH = Path.home() / ".verdict" / "config.yaml"

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager.

        Args:
            config_path: Optional custom config file path. Defaults to ~/.verdict/config.yaml
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self._config = self._load_config()

    def _load_config(self) -> dict:
        """Load configuration from file if it exists."""
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f) or {}
        return {}

    def get_api_key(self) -> str:
        """Get Anthropic API key from environment or config.

        Returns:
            API key string

        Raises:
            ValueError: If API key is not found or invalid
        """
        # Try environment variable first
        api_key = os.getenv("ANTHROPIC_API_KEY")

        # Fall back to config file
        if not api_key:
            api_key = self._config.get("anthropic_api_key")

        if not api_key:
            raise ValueError(
                "Anthropic API key not found!\n\n"
                "Please set it in one of these ways:\n"
                "1. Environment variable: export ANTHROPIC_API_KEY='your-key-here'\n"
                "2. Config file: verdict config\n\n"
                "Get your API key from: https://console.anthropic.com/account/keys"
            )

        # Basic validation
        if not api_key.startswith("sk-ant-"):
            raise ValueError(
                f"Invalid API key format. Anthropic keys should start with 'sk-ant-'\n"
                f"Got: {api_key[:10]}..."
            )

        return api_key

    def save_api_key(self, api_key: str) -> None:
        """Save API key to config file.

        Args:
            api_key: The Anthropic API key to save
        """
        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Update config
        self._config["anthropic_api_key"] = api_key

        # Save to file
        with open(self.config_path, "w") as f:
            yaml.dump(self._config, f, default_flow_style=False)

    def get(self, key: str, default=None):
        """Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)

    def set(self, key: str, value) -> None:
        """Set a configuration value and save.

        Args:
            key: Configuration key
            value: Value to set
        """
        self._config[key] = value

        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Save to file
        with open(self.config_path, "w") as f:
            yaml.dump(self._config, f, default_flow_style=False)
