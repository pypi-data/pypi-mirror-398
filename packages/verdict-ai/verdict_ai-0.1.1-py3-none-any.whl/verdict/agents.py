"""Agent implementations for Verdict system."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import anthropic
from jinja2 import Environment, FileSystemLoader


class Agent:
    """Base class for Verdict agents."""

    def __init__(self, api_key: str, template_name: str):
        """Initialize agent.

        Args:
            api_key: Anthropic API key
            template_name: Name of Jinja2 template file for this agent
        """
        self.client = anthropic.Anthropic(api_key=api_key)
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
        """Call Claude API with prompt.

        Args:
            system_prompt: System prompt for the agent
            user_message: User message to process
            max_tokens: Maximum tokens in response

        Returns:
            Agent's response text

        Raises:
            anthropic.APIError: If API call fails
        """
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        return response.content[0].text


class VerdictAgent(Agent):
    """Agent that makes singular decisions on user ideas."""

    def __init__(self, api_key: str):
        """Initialize Verdict Agent.

        Args:
            api_key: Anthropic API key
        """
        super().__init__(api_key, "verdict_agent.j2")

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

        # Parse JSON response
        try:
            verdict = json.loads(response_text)
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

    def __init__(self, api_key: str):
        """Initialize Execution Agent.

        Args:
            api_key: Anthropic API key
        """
        super().__init__(api_key, "execution_agent.j2")

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

        # Parse JSON response
        try:
            plan = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Agent returned invalid JSON: {e}\n\nResponse: {response_text}"
            )

        return plan
