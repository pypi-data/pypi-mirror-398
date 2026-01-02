"""Structured logging with Rich."""

import logging
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

# Global console for CLI output
console = Console()


def setup_logging(level: str = "INFO", verbose: bool = False) -> None:
    """Configure logging with Rich handler."""
    log_level = logging.DEBUG if verbose else getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=console,
                rich_tracebacks=True,
                show_time=verbose,
                show_path=verbose,
            )
        ],
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name or "rewindlearn")
