"""LangGraph state definitions."""

from typing import Annotated, Optional
from operator import add

from typing_extensions import TypedDict


class SessionState(TypedDict):
    """State for session processing workflow."""

    # Inputs
    transcript: str
    chat_log: str
    slides: Optional[str]
    course_name: str
    session_number: int

    # Task outputs (populated as chains complete)
    session_summary: Optional[str]
    concept_timeline: Optional[str]
    friction_analysis: Optional[str]
    coverage_gaps: Optional[str]
    learning_resources: Optional[str]
    action_items: Optional[str]
    concept_chunks: Optional[str]

    # Metadata
    completed_tasks: Annotated[list[str], add]
    errors: Annotated[list[str], add]
