"""Configuration commands."""

import typer
from rich.console import Console

from rewindlearn.core.config import get_settings

app = typer.Typer(help="Configuration management")
console = Console()


@app.command("show")
def show() -> None:
    """Show current configuration."""
    settings = get_settings()

    console.print("[bold]Current Configuration:[/bold]")
    console.print(f"  Default Provider: {settings.default_provider}")
    console.print(f"  Default Model: {settings.default_model}")
    console.print(f"  Templates Dir: {settings.templates_dir}")
    console.print(f"  Output Dir: {settings.output_dir}")
    console.print(f"  LangSmith Tracing: {settings.langsmith_tracing}")

    console.print("\n[bold]API Keys:[/bold]")
    console.print(
        f"  Anthropic: {'Set' if settings.anthropic_api_key else 'Not set'}"
    )
    console.print(
        f"  OpenAI: {'Set' if settings.openai_api_key else 'Not set'}"
    )
    console.print(
        f"  LangSmith: {'Set' if settings.langsmith_api_key else 'Not set'}"
    )


@app.command("check")
def check() -> None:
    """Check configuration validity."""
    settings = get_settings()

    issues = []

    if not settings.anthropic_api_key and not settings.openai_api_key:
        issues.append("No LLM API key configured")

    if not settings.templates_dir.exists():
        issues.append(f"Templates directory not found: {settings.templates_dir}")

    if issues:
        console.print("[red]Configuration issues found:[/red]")
        for issue in issues:
            console.print(f"  - {issue}")
        raise typer.Exit(1)
    else:
        console.print("[green]Configuration is valid[/green]")
