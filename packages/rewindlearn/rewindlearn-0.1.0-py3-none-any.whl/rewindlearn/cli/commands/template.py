"""Template management commands."""

from pathlib import Path

import typer
from rich.console import Console

from rewindlearn.core.config import get_settings
from rewindlearn.templates.loader import TemplateLoader

app = typer.Typer(help="Template management")
console = Console()


@app.command("list")
def list_templates() -> None:
    """List available templates."""
    settings = get_settings()
    loader = TemplateLoader(settings.templates_dir)
    templates = loader.list_templates()

    if not templates:
        console.print("[yellow]No templates found[/yellow]")
        console.print(f"Templates directory: {settings.templates_dir}")
        return

    console.print("[bold]Available Templates:[/bold]")
    for t in templates:
        console.print(f"  - {t}")


@app.command("validate")
def validate(
    path: Path = typer.Argument(..., help="Template YAML file to validate", exists=True)
) -> None:
    """Validate a template file."""
    settings = get_settings()
    loader = TemplateLoader(settings.templates_dir)

    valid, errors = loader.validate(path)

    if valid:
        console.print(f"[green]Template is valid:[/green] {path}")
    else:
        console.print("[red]Template has errors:[/red]")
        for err in errors:
            console.print(f"  - {err}")
        raise typer.Exit(1)


@app.command("show")
def show(
    template_id: str = typer.Argument(..., help="Template ID to show")
) -> None:
    """Show template details."""
    settings = get_settings()
    loader = TemplateLoader(settings.templates_dir)

    try:
        tmpl = loader.load(template_id)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    console.print(f"[bold]{tmpl.name}[/bold] (v{tmpl.version})")
    console.print(f"ID: {tmpl.template_id}")
    if tmpl.description:
        console.print(f"\n{tmpl.description}")

    console.print("\n[bold]Inputs:[/bold]")
    console.print(f"  Required: {', '.join(tmpl.inputs.required)}")
    console.print(f"  Optional: {', '.join(tmpl.inputs.optional) or 'none'}")

    console.print("\n[bold]Tasks:[/bold]")
    for task in tmpl.get_tasks():
        deps = f" (depends on: {', '.join(task.dependencies)})" if task.dependencies else ""
        console.print(f"  - {task.name}{deps}")

    console.print("\n[bold]Outputs:[/bold]")
    console.print(f"  Deliverables: {', '.join(tmpl.outputs.deliverables)}")
    console.print(f"  Formats: {', '.join(tmpl.outputs.formats)}")
