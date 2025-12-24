"""Agent implementations for Verdict system."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader

from verdict.llm_providers import LLMProvider


def clean_json_response(text: str) -> str:
    """Clean markdown code blocks and extra whitespace from JSON response.

    Args:
        text: Raw response text that may contain markdown code blocks

    Returns:
        Cleaned JSON string
    """
    # Remove markdown code blocks (```json ... ``` or ``` ... ```)
    text = re.sub(r'^```(?:json)?\s*\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n```\s*$', '', text, flags=re.MULTILINE)

    # Strip extra whitespace
    return text.strip()


class Agent:
    """Base class for Verdict agents."""

    def __init__(self, llm_provider: LLMProvider, template_name: str):
        """Initialize agent.

        Args:
            llm_provider: LLM provider instance (Claude, OpenAI, Gemini, etc.)
            template_name: Name of Jinja2 template file for this agent
        """
        self.llm_provider = llm_provider
        self.template_name = template_name

        # Setup Jinja2 template environment
        templates_dir = Path(__file__).parent / "templates"
        self.jinja_env = Environment(loader=FileSystemLoader(templates_dir))

    def render_prompt(self, **kwargs) -> str:
        """Render agent's system prompt with variables.

        Args:
            **kwargs: Variables to pass to template

        Returns:
            Rendered prompt string
        """
        template = self.jinja_env.get_template(self.template_name)
        return template.render(**kwargs)

    def call_api(
        self, system_prompt: str, user_message: str, max_tokens: int = 4096
    ) -> str:
        """Call LLM API with prompt.

        Args:
            system_prompt: System prompt for the agent
            user_message: User message to process
            max_tokens: Maximum tokens in response (not used by all providers)

        Returns:
            Agent's response text

        Raises:
            Exception: If API call fails
        """
        return self.llm_provider.generate(system_prompt, user_message)


class VerdictAgent(Agent):
    """Agent that makes singular decisions on user ideas."""

    def __init__(self, llm_provider: LLMProvider):
        """Initialize Verdict Agent.

        Args:
            llm_provider: LLM provider instance (Claude, OpenAI, Gemini, etc.)
        """
        super().__init__(llm_provider, "verdict_agent.j2")

    def decide(
        self, user_input: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a decision on user's idea.

        Args:
            user_input: User's idea or question
            context: Optional user context (goals, constraints, past decisions)

        Returns:
            Verdict as dictionary matching verdict schema

        Raises:
            ValueError: If response is not valid JSON
            anthropic.APIError: If API call fails
        """
        # Render system prompt with context
        system_prompt = self.render_prompt(
            user_input=user_input, context=context or {}
        )

        # Call API - user_input is already in the system prompt
        # So we just send a simple message to trigger the response
        response_text = self.call_api(
            system_prompt=system_prompt,
            user_message="Provide your verdict as JSON.",
        )

        # Clean and parse JSON response
        try:
            cleaned_text = clean_json_response(response_text)
            verdict = json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Agent returned invalid JSON: {e}\n\nResponse: {response_text}"
            )

        # Add timestamp if not present
        if "timestamp" not in verdict:
            verdict["timestamp"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        return verdict


class ExecutionAgent(Agent):
    """Agent that creates execution plans from verdicts."""

    def __init__(self, llm_provider: LLMProvider):
        """Initialize Execution Agent.

        Args:
            llm_provider: LLM provider instance (Claude, OpenAI, Gemini, etc.)
        """
        super().__init__(llm_provider, "execution_agent.j2")

    def plan(self, verdict: Dict[str, Any]) -> Dict[str, Any]:
        """Create execution plan from verdict.

        Args:
            verdict: Verdict from VerdictAgent (must match verdict schema)

        Returns:
            Execution plan as dictionary matching execution schema

        Raises:
            ValueError: If response is not valid JSON
            anthropic.APIError: If API call fails
        """
        # Render system prompt with verdict
        system_prompt = self.render_prompt(verdict=verdict)

        # Call API
        response_text = self.call_api(
            system_prompt=system_prompt,
            user_message="Provide your execution plan as JSON.",
        )

        # Clean and parse JSON response
        try:
            cleaned_text = clean_json_response(response_text)
            plan = json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Agent returned invalid JSON: {e}\n\nResponse: {response_text}"
            )

        return plan
