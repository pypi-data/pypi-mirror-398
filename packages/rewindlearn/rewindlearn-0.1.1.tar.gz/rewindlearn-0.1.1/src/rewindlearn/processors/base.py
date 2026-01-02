"""Base processor class for file processing."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ProcessedContent(BaseModel):
    """Result of processing a file."""

    raw_text: str = Field(description="Full text content")
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamps: list[dict[str, str]] = Field(
        default_factory=list,
        description="List of {text, start, end} timestamp entries"
    )


class BaseProcessor(ABC):
    """Abstract base class for file processors."""

    supported_extensions: list[str] = []

    @abstractmethod
    def process(self, path: Path) -> ProcessedContent:
        """Process a file and return structured content."""
        pass

    @classmethod
    def can_handle(cls, path: Path) -> bool:
        """Check if this processor can handle the given file."""
        return path.suffix.lower() in cls.supported_extensions
