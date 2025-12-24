"""CLI interface for Verdict - the meta-decision system."""

import click
from rich.console import Console, Group
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

from verdict.artifacts import ArtifactGenerator
from verdict.config import Config
from verdict.context import ContextManager
from verdict.pipeline import DecisionPipeline, PipelineError
from verdict.storage import StorageManager

console = Console()


@click.group()
@click.version_option(version="0.2.3", prog_name="verdict")
def cli():
    """Verdict - AI-powered meta-decision system.

    Make singular, decisive judgments on your ideas.
    No hedging, no alternatives, just clear verdicts.
    """
    pass


@cli.command()
@click.argument("idea", required=True)
@click.option(
    "--context",
    "-c",
    help="Additional context for the decision",
    default=None,
)
@click.option(
    "--provider",
    "-p",
    type=click.Choice(["claude", "openai", "gemini"], case_sensitive=False),
    default="claude",
    help="LLM provider to use (default: claude)",
)
@click.option(
    "--model",
    "-m",
    help="Specific model to use (e.g., gpt-4o, gemini-1.5-pro)",
    default=None,
)
def decide(idea: str, context: str, provider: str, model: str):
    """Make a decision on an idea.

    \b
    Examples:
        verdict decide "I want to build a personal blog"
        verdict decide "Should I learn Rust or Go?" -c "I'm a Python developer"
    """
    # Validate input
    if not idea or len(idea.strip()) < 5:
        console.print(
            "[red]Error:[/red] Idea must be at least 5 characters long.",
            style="bold",
        )
        raise click.Abort()

    if len(idea) > 500:
        console.print(
            "[yellow]Warning:[/yellow] Idea is very long. Consider being more concise.",
            style="bold",
        )

    # Load configuration
    try:
        config = Config()
        api_key = config.get_api_key(provider)
    except ValueError as e:
        console.print(f"[red]Configuration Error:[/red]\n{e}", style="bold")
        console.print(
            f"\n[dim]To configure {provider}:[/dim]\n"
            f"[cyan]verdict config --provider {provider}[/cyan]"
        )
        raise click.Abort()

    # Display what we're processing
    console.print()
    console.print(
        Panel(
            Text(idea, style="bold cyan"),
            title="[bold]Your Idea[/bold]",
            border_style="cyan",
        )
    )

    # Run decision pipeline
    try:
        # Load user context
        context_manager = ContextManager()
        user_context = context_manager.get_context_for_prompt()

        # Add additional context from CLI argument if provided
        if context:
            if user_context is None:
                user_context = {}
            user_context["additional_context"] = context

        pipeline = DecisionPipeline(provider=provider, api_key=api_key, model=model)

        # Run pipeline with spinner
        console.print()
        with console.status(
            "[bold cyan]Making decision...[/bold cyan]", spinner="dots"
        ):
            verdict, execution_plan = pipeline.run(idea, user_context, verbose=False)

        # Display results with enhanced formatting
        console.print()

        # Decision header with appropriate color
        decision_color = "green" if verdict["decision"] == "proceed" else "red" if verdict["decision"] == "reject" else "yellow"

        # Create verdict table
        verdict_table = Table(show_header=False, box=None, padding=(0, 1))
        verdict_table.add_column("Field", style="bold")
        verdict_table.add_column("Value")

        verdict_table.add_row(
            "Decision",
            f"[bold {decision_color}]{verdict['decision'].upper()}[/bold {decision_color}]"
        )
        verdict_table.add_row("Summary", verdict['verdict_summary'])
        verdict_table.add_row("Confidence", f"{verdict['confidence']:.0%}")
        verdict_table.add_row(
            "Included",
            ", ".join(f"[cyan]{item}[/cyan]" for item in verdict['scope']['included'])
        )
        verdict_table.add_row(
            "Excluded",
            ", ".join(verdict['scope']['excluded']) if verdict['scope']['excluded'] else "[dim]None[/dim]"
        )

        console.print(
            Panel(
                verdict_table,
                title="[bold]Verdict[/bold]",
                border_style=decision_color,
                expand=False,
            )
        )

        # Display reasoning separately
        console.print()
        console.print(
            Panel(
                verdict['reasoning'],
                title="[bold]Reasoning[/bold]",
                border_style="blue",
            )
        )

        # Display execution plan with table
        console.print()

        plan_table = Table(show_header=True, header_style="bold cyan")
        plan_table.add_column("#", style="dim", width=3)
        plan_table.add_column("Phase", style="cyan")
        plan_table.add_column("Goal")
        plan_table.add_column("Effort", justify="right", style="yellow")

        for i, phase in enumerate(execution_plan["phases"], 1):
            plan_table.add_row(
                str(i),
                phase["name"],
                phase["goal"],
                phase.get("estimated_effort", "N/A")
            )

        console.print(
            Panel(
                Group(
                    f"[bold]MVP Boundary:[/bold]\n{execution_plan['mvp_boundary']}\n\n"
                    f"[bold]Total Effort:[/bold] {execution_plan['total_estimated_effort']}\n",
                    plan_table
                ),
                title="[bold blue]Execution Plan[/bold blue]",
                border_style="blue",
            )
        )

        # Generate and save artifacts with progress
        console.print()
        with console.status("[bold cyan]Generating artifacts...[/bold cyan]", spinner="dots"):
            generator = ArtifactGenerator()
            artifacts = generator.compile(idea, verdict, execution_plan)

        console.print("[green]✓[/green] Artifacts generated")

        with console.status("[bold cyan]Saving to disk...[/bold cyan]", spinner="dots"):
            storage = StorageManager()
            saved_paths = storage.save_artifacts(
                artifacts["decision_id"], artifacts
            )

            # Save decision to context
            context_manager.add_decision(
                decision_id=artifacts["decision_id"],
                decision=verdict["decision"],
                summary=verdict["verdict_summary"],
                outcome="planned",
            )

        console.print("[green]✓[/green] Saved to disk\n")

        # Display saved files in a table
        files_table = Table(show_header=True, header_style="bold yellow")
        files_table.add_column("Type", style="bold")
        files_table.add_column("Path", style="cyan")

        files_table.add_row("Decision", str(saved_paths['decision']))
        files_table.add_row("Plan", str(saved_paths['plan']))
        files_table.add_row("State", str(saved_paths['state']))

        console.print(
            Panel(
                Group(
                    f"[bold]Decision ID:[/bold] [cyan]{artifacts['decision_id']}[/cyan]\n",
                    files_table,
                    "\n[dim italic]Next steps:[/dim italic]\n"
                    f"[dim]• View your plan: [cyan]cat {saved_paths['plan']}[/cyan][/dim]\n"
                    f"[dim]• Check context: [cyan]verdict context show[/cyan][/dim]"
                ),
                title="[bold green]✓ Complete[/bold green]",
                border_style="green",
            )
        )

    except PipelineError as e:
        console.print()
        console.print(
            Panel(
                f"[bold red]Pipeline Error[/bold red]\n\n"
                f"{e}\n\n"
                "[bold]Possible solutions:[/bold]\n"
                "• Check your internet connection\n"
                "• Verify your API key: [cyan]verdict config[/cyan]\n"
                "• Try again in a moment\n"
                "• Check Anthropic API status: https://status.anthropic.com",
                title="[bold red]Error[/bold red]",
                border_style="red",
            )
        )
        raise click.Abort()
    except Exception as e:
        console.print()
        console.print(
            Panel(
                f"[bold red]Unexpected Error[/bold red]\n\n"
                f"{type(e).__name__}: {e}\n\n"
                "[bold]What to try:[/bold]\n"
                "• Check the error message above for details\n"
                "• Verify your configuration: [cyan]verdict config[/cyan]\n"
                "• Report this issue: [cyan]https://github.com/1psychoQAQ/verdict/issues[/cyan]",
                title="[bold red]Error[/bold red]",
                border_style="red",
            )
        )
        raise click.Abort()


@cli.command()
@click.option(
    "--provider",
    "-p",
    type=click.Choice(["claude", "openai", "gemini"], case_sensitive=False),
    default="claude",
    help="LLM provider to configure",
)
@click.option(
    "--api-key",
    prompt=True,
    hide_input=True,
    help="Your API key",
)
def config(provider: str, api_key: str):
    """Configure Verdict with your API key.

    Your API key will be saved to ~/.verdict/config.yaml

    \b
    Get your key from:
    - Claude: https://console.anthropic.com/account/keys
    - OpenAI: https://platform.openai.com/api-keys
    - Gemini: https://makersuite.google.com/app/apikey
    """
    console.print()
    console.print(
        Panel(
            "[bold cyan]Welcome to Verdict![/bold cyan]\n\n"
            "Let's set up your configuration.\n\n"
            "[dim]Your API key will be stored securely at ~/.verdict/config.yaml[/dim]",
            border_style="cyan",
        )
    )
    console.print()

    # Validate API key format
    key_formats = {
        "claude": ("sk-ant-", "https://console.anthropic.com/account/keys"),
        "openai": ("sk-", "https://platform.openai.com/api-keys"),
        "gemini": ("AI", "https://makersuite.google.com/app/apikey"),
    }

    expected_prefix, key_url = key_formats[provider]
    if not api_key.startswith(expected_prefix):
        console.print(
            Panel(
                f"[bold red]Invalid API Key Format[/bold red]\n\n"
                f"{provider.capitalize()} API keys should start with [cyan]{expected_prefix}[/cyan]\n\n"
                f"[bold]How to get your API key:[/bold]\n"
                f"1. Visit [cyan]{key_url}[/cyan]\n"
                f"2. Create a new API key\n"
                f"3. Copy the key and run [cyan]verdict config --provider {provider}[/cyan] again",
                title="[bold red]Error[/bold red]",
                border_style="red",
            )
        )
        raise click.Abort()

    # Save configuration
    try:
        with console.status("[bold cyan]Saving configuration...[/bold cyan]", spinner="dots"):
            cfg = Config()
            cfg.save_api_key(api_key, provider)

        console.print()
        console.print(
            Panel(
                f"[green]✓[/green] API key saved to [cyan]{cfg.config_path}[/cyan]\n\n"
                "[bold]Quick Start:[/bold]\n"
                "• Make a decision: [cyan]verdict decide \"your idea\"[/cyan]\n"
                "• Add a goal: [cyan]verdict context add-goal \"your goal\"[/cyan]\n"
                "• View help: [cyan]verdict --help[/cyan]\n\n"
                "[dim]You're all set! Start making decisive judgments.[/dim]",
                title="[bold green]✓ Configuration Complete[/bold green]",
                border_style="green",
            )
        )
    except Exception as e:
        console.print()
        console.print(
            Panel(
                f"[bold red]Configuration Error[/bold red]\n\n"
                f"{type(e).__name__}: {e}\n\n"
                "[bold]What to try:[/bold]\n"
                "• Check file permissions for ~/.verdict/\n"
                "• Ensure you have write access to your home directory\n"
                "• Try running the command again",
                title="[bold red]Error[/bold red]",
                border_style="red",
            )
        )
        raise click.Abort()


@cli.command()
def version():
    """Show version information."""
    console.print()
    console.print(
        Panel(
            "[bold cyan]Verdict[/bold cyan] v0.2.3\n\n"
            "AI-powered meta-decision system\n"
            "Make singular, decisive judgments on your ideas.\n\n"
            "[bold]Supported Providers:[/bold] Claude, OpenAI, Gemini\n\n"
            "[dim]https://github.com/1psychoQAQ/verdict[/dim]",
            border_style="cyan",
        )
    )
    console.print()


@cli.group()
def context():
    """Manage your decision context (goals, preferences, constraints)."""
    pass


@context.command("show")
def context_show():
    """Display your current context."""
    context_manager = ContextManager()
    ctx = context_manager.load()

    console.print()
    console.print(
        Panel(
            f"[bold]Goals:[/bold]\n"
            + (
                "\n".join(f"  • {goal}" for goal in ctx.get("goals", []))
                if ctx.get("goals")
                else "  [dim]No goals set[/dim]"
            )
            + "\n\n"
            f"[bold]Constraints:[/bold]\n"
            + (
                "\n".join(
                    f"  • {key}: {value}"
                    for key, value in ctx.get("constraints", {}).items()
                )
                if ctx.get("constraints")
                else "  [dim]No constraints set[/dim]"
            )
            + "\n\n"
            f"[bold]Preferences:[/bold]\n"
            + (
                "\n".join(
                    f"  • {key}: {value}"
                    for key, value in ctx.get("preferences", {}).items()
                )
                if ctx.get("preferences")
                else "  [dim]No preferences set[/dim]"
            )
            + "\n\n"
            f"[bold]Past Decisions:[/bold] {len(ctx.get('past_decisions', []))} decisions made",
            title="[bold cyan]Your Context[/bold cyan]",
            border_style="cyan",
        )
    )
    console.print()


@context.command("add-goal")
@click.argument("goal")
def context_add_goal(goal: str):
    """Add a goal to your context."""
    context_manager = ContextManager()
    context_manager.add_goal(goal)
    console.print(f"[green]✓[/green] Goal added: {goal}")


@context.command("remove-goal")
@click.argument("goal")
def context_remove_goal(goal: str):
    """Remove a goal from your context."""
    context_manager = ContextManager()
    if context_manager.remove_goal(goal):
        console.print(f"[green]✓[/green] Goal removed: {goal}")
    else:
        console.print(f"[yellow]![/yellow] Goal not found: {goal}")


@context.command("set-constraint")
@click.argument("key")
@click.argument("value")
def context_set_constraint(key: str, value: str):
    """Set a constraint (e.g., time_budget, skill_level)."""
    context_manager = ContextManager()
    context_manager.set_constraint(key, value)
    console.print(f"[green]✓[/green] Constraint set: {key} = {value}")


@context.command("set-preference")
@click.argument("key")
@click.argument("value")
def context_set_preference(key: str, value: str):
    """Set a preference (e.g., risk_tolerance, innovation_vs_proven)."""
    context_manager = ContextManager()
    context_manager.set_preference(key, value)
    console.print(f"[green]✓[/green] Preference set: {key} = {value}")


@context.command("clear")
@click.confirmation_option(prompt="Are you sure you want to clear all context?")
def context_clear():
    """Clear all context data."""
    context_manager = ContextManager()
    context_manager.clear()
    console.print("[green]✓[/green] Context cleared")


if __name__ == "__main__":
    cli()
