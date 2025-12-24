"""Artifact generation from agent outputs."""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, TemplateError


class ArtifactGenerator:
    """Generates artifact files from agent outputs using templates."""

    def __init__(self):
        """Initialize generator with Jinja2 environment."""
        templates_dir = Path(__file__).parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=False,  # We're generating JSON/Markdown, not HTML
        )

    def generate_decision_id(self, user_input: str, timestamp: str) -> str:
        """Generate unique ID for a decision.

        Args:
            user_input: User's original input
            timestamp: ISO timestamp of decision

        Returns:
            Unique decision ID (first 12 chars of hash)
        """
        # Create hash from input + timestamp
        content = f"{user_input}:{timestamp}"
        hash_obj = hashlib.sha256(content.encode())
        return hash_obj.hexdigest()[:12]

    def render_decision(
        self,
        verdict: Dict[str, Any],
        provider: str,
        model: str,
        version: str = "0.2.4",
    ) -> str:
        """Render verdict to decision.json format.

        Args:
            verdict: Verdict dictionary from VerdictAgent
            provider: LLM provider name (claude, openai, gemini)
            model: Model name used for generation
            version: Verdict version

        Returns:
            Rendered JSON string

        Raises:
            TemplateError: If template rendering fails
        """
        template = self.jinja_env.get_template("decision.json.j2")
        return template.render(
            verdict=verdict, provider=provider, model=model, version=version
        )

    def render_todo(
        self, verdict: Dict[str, Any], plan: Dict[str, Any]
    ) -> str:
        """Render execution plan to todo.md format.

        Args:
            verdict: Verdict dictionary (for context)
            plan: Execution plan dictionary from ExecutionAgent

        Returns:
            Rendered Markdown string

        Raises:
            TemplateError: If template rendering fails
        """
        template = self.jinja_env.get_template("todo.md.j2")
        return template.render(verdict=verdict, plan=plan)

    def render_state(
        self,
        decision_id: str,
        user_input: str,
        verdict: Dict[str, Any],
        plan: Dict[str, Any],
    ) -> str:
        """Render state snapshot to state.json format.

        Args:
            decision_id: Unique decision ID
            user_input: Original user input
            verdict: Verdict dictionary
            plan: Execution plan dictionary

        Returns:
            Rendered JSON string

        Raises:
            TemplateError: If template rendering fails
        """
        template = self.jinja_env.get_template("state.json.j2")
        return template.render(
            decision_id=decision_id,
            user_input=user_input,
            verdict=verdict,
            plan=plan,
        )

    def compile(
        self,
        user_input: str,
        verdict: Dict[str, Any],
        plan: Dict[str, Any],
        provider: str,
        model: str,
        version: str = "0.2.4",
    ) -> Dict[str, str]:
        """Compile all artifacts from agent outputs.

        Args:
            user_input: Original user input
            verdict: Verdict from VerdictAgent
            plan: Execution plan from ExecutionAgent
            provider: LLM provider name (claude, openai, gemini)
            model: Model name used for generation
            version: Verdict version

        Returns:
            Dictionary with keys: decision_json, todo_md, state_json, decision_id

        Raises:
            TemplateError: If any template rendering fails
        """
        # Generate decision ID
        decision_id = self.generate_decision_id(
            user_input, verdict["timestamp"]
        )

        # Render all templates
        try:
            decision_json = self.render_decision(verdict, provider, model, version)
            todo_md = self.render_todo(verdict, plan)
            state_json = self.render_state(
                decision_id, user_input, verdict, plan
            )

            return {
                "decision_id": decision_id,
                "decision_json": decision_json,
                "todo_md": todo_md,
                "state_json": state_json,
            }

        except TemplateError as e:
            raise TemplateError(
                f"Failed to render artifacts: {e}\n"
                f"Template: {e.name}\n"
                f"Line: {e.lineno}"
            )
