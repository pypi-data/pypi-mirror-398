"""LLM provider abstraction layer supporting multiple providers."""

import json
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import anthropic


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, system_prompt: str, user_message: str) -> str:
        """Generate a response from the LLM.

        Args:
            system_prompt: System prompt/instruction
            user_message: User message

        Returns:
            Generated text response
        """
        pass


class ClaudeProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929"):
        """Initialize Claude provider.

        Args:
            api_key: Anthropic API key
            model: Claude model to use (default: Claude Sonnet 4.5)
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def generate(self, system_prompt: str, user_message: str) -> str:
        """Generate response using Claude."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: OpenAI model to use (gpt-4, gpt-4-turbo, gpt-3.5-turbo, etc.)
        """
        try:
            import openai
        except ImportError:
            raise ImportError(
                "OpenAI support requires the 'openai' package. "
                "Install it with: pip install openai"
            )

        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    def generate(self, system_prompt: str, user_message: str) -> str:
        """Generate response using OpenAI."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            max_tokens=4096,
        )
        return response.choices[0].message.content


class GeminiProvider(LLMProvider):
    """Google Gemini provider."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp"):
        """Initialize Gemini provider.

        Args:
            api_key: Google API key
            model: Gemini model to use (default: Gemini 2.0 Flash)
        """
        try:
            from google import genai
        except ImportError:
            raise ImportError(
                "Gemini support requires the 'google-genai' package. "
                "Install it with: pip install google-genai"
            )

        self.client = genai.Client(api_key=api_key)
        self.model = model

    def generate(self, system_prompt: str, user_message: str) -> str:
        """Generate response using Gemini."""
        # Gemini 2.0 supports system instructions
        response = self.client.models.generate_content(
            model=self.model,
            contents=user_message,
            config={
                "system_instruction": system_prompt,
                "max_output_tokens": 4096,
            }
        )
        return response.text


def get_provider(
    provider_name: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> LLMProvider:
    """Factory function to get the appropriate LLM provider.

    Args:
        provider_name: Name of provider ('claude', 'openai', 'gemini')
        api_key: API key for the provider (reads from env if not provided)
        model: Model name (uses default if not provided)

    Returns:
        LLMProvider instance

    Raises:
        ValueError: If provider is unknown or API key is missing
    """
    provider_name = provider_name.lower()

    # Get API key from environment if not provided
    if api_key is None:
        env_vars = {
            "claude": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "gemini": "GOOGLE_API_KEY",
        }
        env_var = env_vars.get(provider_name)
        if env_var:
            api_key = os.getenv(env_var)

    if not api_key:
        raise ValueError(
            f"API key required for {provider_name}. "
            f"Set it via config or environment variable."
        )

    # Create provider
    providers = {
        "claude": ClaudeProvider,
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
    }

    provider_class = providers.get(provider_name)
    if not provider_class:
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            f"Available: {', '.join(providers.keys())}"
        )

    # Create instance with or without model
    if model:
        return provider_class(api_key=api_key, model=model)
    else:
        return provider_class(api_key=api_key)


# Model recommendations by provider
RECOMMENDED_MODELS = {
    "claude": [
        "claude-sonnet-4-5-20250929",  # Latest Sonnet 4.5 (Best for most tasks)
        "claude-opus-4-5",  # Most capable (Best for coding, agents)
        "claude-haiku-4-5",  # Fastest and cheapest
        "claude-3-5-sonnet-20241022",  # Legacy Sonnet 3.5
    ],
    "openai": [
        "gpt-4o",  # Latest and best
        "gpt-4-turbo",  # Fast and capable
        "gpt-4",  # Most reliable
        "gpt-3.5-turbo",  # Cheapest
    ],
    "gemini": [
        "gemini-2.0-flash-exp",  # Latest Gemini 2.0 (Experimental)
        "gemini-1.5-pro",  # Best quality (Stable)
        "gemini-1.5-flash",  # Faster and cheaper
    ],
}
