"""File processors for session artifacts."""

from pathlib import Path
from typing import Optional

from rewindlearn.processors.base import BaseProcessor, ProcessedContent
from rewindlearn.processors.transcript import TranscriptProcessor
from rewindlearn.processors.chat import ChatProcessor

# Processor registry
PROCESSORS: dict[str, BaseProcessor] = {
    "transcript": TranscriptProcessor(),
    "chat_log": ChatProcessor(),
}


def process_input(input_type: str, path: Path) -> ProcessedContent:
    """Process an input file using the appropriate processor."""
    processor = PROCESSORS.get(input_type)
    if not processor:
        raise ValueError(f"Unknown input type: {input_type}")
    return processor.process(path)


def get_processor_for_file(path: Path) -> Optional[BaseProcessor]:
    """Get the appropriate processor for a file based on extension."""
    for processor in PROCESSORS.values():
        if processor.can_handle(path):
            return processor
    return None


__all__ = [
    "BaseProcessor",
    "ProcessedContent",
    "TranscriptProcessor",
    "ChatProcessor",
    "process_input",
    "get_processor_for_file",
]
