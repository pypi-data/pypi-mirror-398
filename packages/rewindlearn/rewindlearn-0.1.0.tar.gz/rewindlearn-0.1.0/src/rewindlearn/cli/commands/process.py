"""Process command for session processing."""

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from rewindlearn.core.config import get_settings
from rewindlearn.core.logging import setup_logging
from rewindlearn.output.builder import OutputBuilder
from rewindlearn.templates.loader import TemplateLoader
from rewindlearn.workflow.executor import WorkflowExecutor

app = typer.Typer(help="Process session files")
console = Console()


@app.command("run")
def run(
    template: str = typer.Option(
        ..., "--template", "-t",
        help="Template ID or path to template YAML"
    ),
    transcript: Path = typer.Option(
        ..., "--transcript",
        help="Path to transcript file (.txt, .vtt, .srt)",
        exists=True
    ),
    chat: Path = typer.Option(
        None, "--chat",
        help="Path to chat log file",
        exists=True
    ),
    output: Path = typer.Option(
        Path("output"), "--output", "-o",
        help="Output directory"
    ),
    course: str = typer.Option(
        "Unknown Course", "--course", "-c",
        help="Course name"
    ),
    session: int = typer.Option(
        1, "--session", "-s",
        help="Session number"
    ),
    verbose: bool = typer.Option(
        False, "--verbose",
        help="Enable verbose output"
    ),
) -> None:
    """Process a session with the specified template."""
    setup_logging(verbose=verbose)
    settings = get_settings()

    # Validate API keys
    try:
        settings.validate_api_keys()
    except ValueError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        raise typer.Exit(1)

    console.print(Panel.fit(
        f"[bold blue]Rewind.Learn[/bold blue]\n"
        f"Template: {template}\n"
        f"Transcript: {transcript.name}\n"
        f"Output: {output}"
    ))

    # Load template for output building
    loader = TemplateLoader(settings.templates_dir)
    try:
        tmpl = loader.load(template)
    except Exception as e:
        console.print(f"[red]Template error:[/red] {e}")
        raise typer.Exit(1)

    # Execute workflow
    try:
        executor = WorkflowExecutor(template, settings=settings, console=console)
        state = asyncio.run(executor.execute(
            transcript_path=transcript,
            chat_path=chat,
            course_name=course,
            session_number=session,
        ))
    except Exception as e:
        console.print(f"[red]Processing error:[/red] {e}")
        raise typer.Exit(1)

    # Generate outputs
    builder = OutputBuilder(tmpl, output)
    files = builder.generate(state, course, session)

    # Summary
    table = Table(title="Generated Files")
    table.add_column("File", style="green")
    table.add_column("Size")

    for f in files:
        table.add_row(f.name, f"{f.stat().st_size:,} bytes")

    console.print(table)

    # Show errors if any
    if state.get("errors"):
        console.print("\n[yellow]Warnings:[/yellow]")
        for err in state["errors"]:
            console.print(f"  - {err}")

    # Show completed tasks
    completed = state.get("completed_tasks", [])
    console.print(f"\n[green]Completed {len(completed)} tasks[/green]")
