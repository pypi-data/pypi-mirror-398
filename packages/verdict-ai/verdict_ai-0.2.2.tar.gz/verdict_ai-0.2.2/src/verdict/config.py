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

    def get_api_key(self, provider: str = "claude") -> str:
        """Get API key from environment or config for the specified provider.

        Args:
            provider: LLM provider name ('claude', 'openai', 'gemini')

        Returns:
            API key string

        Raises:
            ValueError: If API key is not found or invalid
        """
        provider = provider.lower()

        # Map provider to environment variable and config key
        env_vars = {
            "claude": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "gemini": "GOOGLE_API_KEY",
        }
        config_keys = {
            "claude": "anthropic_api_key",
            "openai": "openai_api_key",
            "gemini": "google_api_key",
        }
        urls = {
            "claude": "https://console.anthropic.com/account/keys",
            "openai": "https://platform.openai.com/api-keys",
            "gemini": "https://makersuite.google.com/app/apikey",
        }

        env_var = env_vars.get(provider)
        config_key = config_keys.get(provider)
        url = urls.get(provider)

        if not env_var or not config_key:
            raise ValueError(f"Unknown provider: {provider}")

        # Try environment variable first
        api_key = os.getenv(env_var)

        # Fall back to config file
        if not api_key:
            api_key = self._config.get(config_key)

        if not api_key:
            raise ValueError(
                f"{provider.capitalize()} API key not found!\n\n"
                f"Please set it in one of these ways:\n"
                f"1. Environment variable: export {env_var}='your-key-here'\n"
                f"2. Config file: verdict config --provider {provider}\n\n"
                f"Get your API key from: {url}"
            )

        return api_key

    def save_api_key(self, api_key: str, provider: str = "claude") -> None:
        """Save API key to config file.

        Args:
            api_key: The API key to save
            provider: LLM provider name ('claude', 'openai', 'gemini')
        """
        provider = provider.lower()

        # Map provider to config key
        config_keys = {
            "claude": "anthropic_api_key",
            "openai": "openai_api_key",
            "gemini": "google_api_key",
        }

        config_key = config_keys.get(provider)
        if not config_key:
            raise ValueError(f"Unknown provider: {provider}")

        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Update config
        self._config[config_key] = api_key

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
