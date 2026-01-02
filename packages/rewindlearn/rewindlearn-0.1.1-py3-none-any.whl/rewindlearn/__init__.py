"""Rewind.Learn - Transform session artifacts into structured knowledge."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("rewindlearn")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"

# Public API exports
from rewindlearn.workflow.executor import process_session
from rewindlearn.templates.loader import TemplateLoader
from rewindlearn.core.config import Settings

__all__ = [
    "__version__",
    "process_session",
    "TemplateLoader",
    "Settings",
]
