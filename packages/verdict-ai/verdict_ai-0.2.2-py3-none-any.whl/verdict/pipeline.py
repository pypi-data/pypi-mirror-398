"""Sequential agent pipeline with validation and retry logic."""

import time
from typing import Any, Dict, Optional, Tuple

from jsonschema import ValidationError
from rich.console import Console

from verdict.agents import ExecutionAgent, VerdictAgent
from verdict.llm_providers import get_provider
from verdict.validator import SchemaValidator

console = Console()


class PipelineError(Exception):
    """Raised when pipeline fails after all retries."""

    pass


class DecisionPipeline:
    """Sequential pipeline: VerdictAgent → validate → ExecutionAgent → validate."""

    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds

    def __init__(
        self,
        provider: str = "claude",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """Initialize pipeline with agents and validator.

        Args:
            provider: LLM provider name ('claude', 'openai', 'gemini')
            api_key: API key for the provider (reads from env if not provided)
            model: Model name (uses default if not provided)
        """
        # Create LLM provider
        llm_provider = get_provider(provider, api_key, model)

        # Initialize agents with provider
        self.verdict_agent = VerdictAgent(llm_provider)
        self.execution_agent = ExecutionAgent(llm_provider)
        self.validator = SchemaValidator()

    def run(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        verbose: bool = True,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Run complete decision pipeline.

        Args:
            user_input: User's idea or question
            context: Optional user context
            verbose: Whether to print progress messages

        Returns:
            Tuple of (verdict, execution_plan)

        Raises:
            PipelineError: If pipeline fails after all retries
        """
        # Step 1: Get verdict from Verdict Agent
        if verbose:
            console.print("\n[cyan]→ Verdict Agent analyzing...[/cyan]")

        verdict = self._run_with_retry(
            func=lambda: self.verdict_agent.decide(user_input, context),
            validator=self.validator.validate_verdict,
            step_name="Verdict Agent",
            verbose=verbose,
        )

        if verbose:
            console.print(
                f"[green]✓[/green] Verdict: [bold]{verdict['decision'].upper()}[/bold]"
            )
            console.print(f"  {verdict['verdict_summary']}\n")

        # Step 2: Get execution plan from Execution Agent
        if verbose:
            console.print("[cyan]→ Execution Agent planning...[/cyan]")

        execution_plan = self._run_with_retry(
            func=lambda: self.execution_agent.plan(verdict),
            validator=self.validator.validate_execution,
            step_name="Execution Agent",
            verbose=verbose,
        )

        if verbose:
            console.print(
                f"[green]✓[/green] Plan: {len(execution_plan['phases'])} phases, "
                f"{execution_plan['total_estimated_effort']}\n"
            )

        return verdict, execution_plan

    def _run_with_retry(
        self,
        func,
        validator,
        step_name: str,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """Run a function with retry logic and validation.

        Args:
            func: Function to call (agent method)
            validator: Validation function for output
            step_name: Name of step for error messages
            verbose: Whether to print retry messages

        Returns:
            Validated output from function

        Raises:
            PipelineError: If all retries fail
        """
        last_error = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                # Call agent
                result = func()

                # Validate output
                validator(result)

                # Success!
                if attempt > 1 and verbose:
                    console.print(
                        f"[green]✓[/green] {step_name} succeeded on attempt {attempt}"
                    )

                return result

            except ValidationError as e:
                last_error = e
                if verbose:
                    console.print(
                        f"[yellow]⚠[/yellow] {step_name} validation failed "
                        f"(attempt {attempt}/{self.MAX_RETRIES}): {e.message}"
                    )

                # Retry after delay (except on last attempt)
                if attempt < self.MAX_RETRIES:
                    if verbose:
                        console.print(
                            f"  Retrying in {self.RETRY_DELAY}s...\n"
                        )
                    time.sleep(self.RETRY_DELAY)

            except ValueError as e:
                # JSON parse error
                last_error = e
                if verbose:
                    console.print(
                        f"[yellow]⚠[/yellow] {step_name} returned invalid JSON "
                        f"(attempt {attempt}/{self.MAX_RETRIES})"
                    )

                # Retry after delay (except on last attempt)
                if attempt < self.MAX_RETRIES:
                    if verbose:
                        console.print(
                            f"  Retrying in {self.RETRY_DELAY}s...\n"
                        )
                    time.sleep(self.RETRY_DELAY)

            except Exception as e:
                # API or other error
                last_error = e
                if verbose:
                    console.print(
                        f"[red]✗[/red] {step_name} error "
                        f"(attempt {attempt}/{self.MAX_RETRIES}): {e}"
                    )

                # Retry after delay (except on last attempt)
                if attempt < self.MAX_RETRIES:
                    if verbose:
                        console.print(
                            f"  Retrying in {self.RETRY_DELAY}s...\n"
                        )
                    time.sleep(self.RETRY_DELAY)

        # All retries failed
        raise PipelineError(
            f"{step_name} failed after {self.MAX_RETRIES} attempts.\n"
            f"Last error: {last_error}"
        )
