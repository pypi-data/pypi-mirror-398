"""User context management for personalized decisions."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class ContextManager:
    """Manages user context across decision sessions."""

    def __init__(self, context_path: Optional[Path] = None):
        """Initialize context manager.

        Args:
            context_path: Path to context.yaml (defaults to ~/.verdict/context.yaml)
        """
        if context_path is None:
            context_path = Path.home() / ".verdict" / "context.yaml"

        self.context_path = Path(context_path)
        self._context: Optional[Dict[str, Any]] = None

    def _get_default_context(self) -> Dict[str, Any]:
        """Get default empty context structure.

        Returns:
            Default context dictionary
        """
        return {
            "goals": [],
            "past_decisions": [],
            "constraints": {},
            "preferences": {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

    def load(self) -> Dict[str, Any]:
        """Load context from file.

        Returns:
            Context dictionary (creates default if file doesn't exist)
        """
        if self._context is not None:
            return self._context

        # Create parent directory if needed
        self.context_path.parent.mkdir(parents=True, exist_ok=True)

        # Load from file or create default
        if self.context_path.exists():
            with open(self.context_path, "r", encoding="utf-8") as f:
                self._context = yaml.safe_load(f) or self._get_default_context()
        else:
            self._context = self._get_default_context()

        return self._context

    def save(self, context: Optional[Dict[str, Any]] = None) -> None:
        """Save context to file.

        Args:
            context: Context to save (uses cached context if None)
        """
        if context is not None:
            self._context = context

        if self._context is None:
            return

        # Update timestamp
        self._context["updated_at"] = datetime.now().isoformat()

        # Ensure parent directory exists
        self.context_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        with open(self.context_path, "w", encoding="utf-8") as f:
            yaml.dump(
                self._context,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

    def add_decision(
        self,
        decision_id: str,
        decision: str,
        summary: str,
        outcome: str = "planned",
        learning: Optional[str] = None,
    ) -> None:
        """Add a decision to the context history.

        Args:
            decision_id: Unique decision ID
            decision: The decision made (proceed/reject/alternative)
            summary: Summary of the decision
            outcome: Current outcome status (planned/in_progress/completed/abandoned)
            learning: Optional learning or insight from this decision
        """
        context = self.load()

        decision_entry = {
            "decision_id": decision_id,
            "decision": decision,
            "summary": summary,
            "outcome": outcome,
            "timestamp": datetime.now().isoformat(),
        }

        if learning:
            decision_entry["learning"] = learning

        context["past_decisions"].append(decision_entry)
        self.save(context)

    def add_goal(self, goal: str) -> None:
        """Add a goal to the user's context.

        Args:
            goal: Goal description
        """
        context = self.load()

        if goal not in context["goals"]:
            context["goals"].append(goal)
            self.save(context)

    def remove_goal(self, goal: str) -> bool:
        """Remove a goal from the user's context.

        Args:
            goal: Goal to remove

        Returns:
            True if goal was removed, False if not found
        """
        context = self.load()

        if goal in context["goals"]:
            context["goals"].remove(goal)
            self.save(context)
            return True

        return False

    def set_constraint(self, key: str, value: Any) -> None:
        """Set a constraint in the user's context.

        Args:
            key: Constraint key (e.g., 'time_budget', 'skill_level')
            value: Constraint value
        """
        context = self.load()
        context["constraints"][key] = value
        self.save(context)

    def set_preference(self, key: str, value: Any) -> None:
        """Set a preference in the user's context.

        Args:
            key: Preference key (e.g., 'risk_tolerance', 'innovation_vs_proven')
            value: Preference value
        """
        context = self.load()
        context["preferences"][key] = value
        self.save(context)

    def get_context_for_prompt(self) -> Optional[Dict[str, Any]]:
        """Get context formatted for agent prompts.

        Returns:
            Context dictionary with relevant fields for decision-making,
            or None if context is empty/default
        """
        context = self.load()

        # Check if context has any meaningful data
        has_data = (
            len(context.get("goals", [])) > 0
            or len(context.get("past_decisions", [])) > 0
            or len(context.get("constraints", {})) > 0
            or len(context.get("preferences", {})) > 0
        )

        if not has_data:
            return None

        # Format for prompt (exclude metadata)
        prompt_context = {}

        if context.get("goals"):
            prompt_context["goals"] = context["goals"]

        if context.get("constraints"):
            prompt_context["constraints"] = context["constraints"]

        if context.get("preferences"):
            prompt_context["preferences"] = context["preferences"]

        # Include recent decisions (last 5)
        if context.get("past_decisions"):
            recent_decisions = context["past_decisions"][-5:]
            prompt_context["recent_decisions"] = [
                {
                    "summary": d.get("summary"),
                    "outcome": d.get("outcome"),
                    "learning": d.get("learning"),
                }
                for d in recent_decisions
                if d.get("summary")  # Only include if summary exists
            ]

        return prompt_context if prompt_context else None

    def clear(self) -> None:
        """Clear all context data (reset to default)."""
        self._context = self._get_default_context()
        self.save()
