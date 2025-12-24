"""JSON schema validation for agent outputs."""

import json
from pathlib import Path
from typing import Any, Dict

from jsonschema import ValidationError, validate


class SchemaValidator:
    """Validates agent outputs against JSON schemas."""

    def __init__(self):
        """Initialize validator with schemas from schemas/ directory."""
        schemas_dir = Path(__file__).parent.parent.parent / "schemas"

        # Load schemas
        with open(schemas_dir / "verdict.json") as f:
            self.verdict_schema = json.load(f)

        with open(schemas_dir / "execution.json") as f:
            self.execution_schema = json.load(f)

    def validate_verdict(self, verdict: Dict[str, Any]) -> None:
        """Validate verdict against verdict schema.

        Args:
            verdict: Verdict dictionary to validate

        Raises:
            ValidationError: If verdict doesn't match schema
        """
        try:
            validate(instance=verdict, schema=self.verdict_schema)
        except ValidationError as e:
            # Provide helpful error message
            raise ValidationError(
                f"Verdict validation failed:\n"
                f"  Error: {e.message}\n"
                f"  Path: {' -> '.join(str(p) for p in e.path)}\n"
                f"  Schema requirement: {e.schema}"
            )

    def validate_execution(self, execution: Dict[str, Any]) -> None:
        """Validate execution plan against execution schema.

        Args:
            execution: Execution plan dictionary to validate

        Raises:
            ValidationError: If execution plan doesn't match schema
        """
        try:
            validate(instance=execution, schema=self.execution_schema)
        except ValidationError as e:
            # Provide helpful error message
            raise ValidationError(
                f"Execution plan validation failed:\n"
                f"  Error: {e.message}\n"
                f"  Path: {' -> '.join(str(p) for p in e.path)}\n"
                f"  Schema requirement: {e.schema}"
            )
