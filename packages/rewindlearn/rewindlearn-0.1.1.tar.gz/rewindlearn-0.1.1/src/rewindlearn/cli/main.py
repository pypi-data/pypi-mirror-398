"""Main CLI application."""

import typer
from rich.console import Console

from rewindlearn import __version__
from rewindlearn.cli.commands import config, process, template

app = typer.Typer(
    name="rewindlearn",
    help="Transform session artifacts into structured knowledge.",
    no_args_is_help=True,
)

console = Console()

# Register command groups
app.add_typer(process.app, name="process")
app.add_typer(template.app, name="template")
app.add_typer(config.app, name="config")


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(False, "--version", "-v", help="Show version")
) -> None:
    """Rewind.Learn - Session Processing Framework"""
    if version:
        console.print(f"rewindlearn {__version__}")
        raise typer.Exit()


if __name__ == "__main__":
    app()
