"""Workflow execution engine."""

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from rewindlearn.core.config import Settings, get_settings
from rewindlearn.core.logging import console
from rewindlearn.llm.providers import LLMProvider
from rewindlearn.llm.router import LLMRouter
from rewindlearn.processors import process_input
from rewindlearn.templates.loader import TemplateLoader
from rewindlearn.workflow.graph import WorkflowBuilder
from rewindlearn.workflow.state import SessionState


class WorkflowExecutor:
    """Execute processing workflows."""

    def __init__(
        self,
        template_id: str,
        settings: Optional[Settings] = None,
        console: Optional[Console] = None
    ):
        self.settings = settings or get_settings()
        self.console = console or Console(force_terminal=True, legacy_windows=False)

        # Load template
        loader = TemplateLoader(self.settings.templates_dir)
        self.template = loader.load(template_id)

        # Set up LLM
        provider = LLMProvider(self.settings)
        self.router = LLMRouter(provider)

    async def execute(
        self,
        transcript_path: Path,
        chat_path: Optional[Path] = None,
        slides_path: Optional[Path] = None,
        course_name: str = "Unknown Course",
        session_number: int = 1,
    ) -> SessionState:
        """Execute the workflow with the given inputs."""

        # Process input files
        transcript = process_input("transcript", transcript_path)
        chat_log = ""
        if chat_path and chat_path.exists():
            chat_log = process_input("chat_log", chat_path).raw_text

        # Build initial state
        initial_state: SessionState = {
            "transcript": transcript.raw_text,
            "chat_log": chat_log,
            "slides": None,
            "course_name": course_name,
            "session_number": session_number,
            "session_summary": None,
            "concept_timeline": None,
            "friction_analysis": None,
            "coverage_gaps": None,
            "learning_resources": None,
            "action_items": None,
            "concept_chunks": None,
            "completed_tasks": [],
            "errors": [],
        }

        # Build and run workflow
        builder = WorkflowBuilder(self.template, self.router)
        graph = builder.build()

        with Progress(
            SpinnerColumn(spinner_name="line"),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Processing session...", total=None)

            final_state = await graph.ainvoke(initial_state)

            progress.update(task, description="Complete!")

        return final_state


async def process_session(
    template: str,
    transcript_path: str | Path,
    chat_path: Optional[str | Path] = None,
    slides_path: Optional[str | Path] = None,
    course_name: str = "Unknown Course",
    session_number: int = 1,
    settings: Optional[Settings] = None,
) -> SessionState:
    """
    High-level API to process a session.

    This is the main public API for programmatic usage.

    Example:
        >>> results = await process_session(
        ...     template="online-course",
        ...     transcript_path="lecture.vtt",
        ...     course_name="AI Engineering",
        ...     session_number=5
        ... )
        >>> print(results["session_summary"])
    """
    executor = WorkflowExecutor(template, settings=settings)
    return await executor.execute(
        transcript_path=Path(transcript_path),
        chat_path=Path(chat_path) if chat_path else None,
        slides_path=Path(slides_path) if slides_path else None,
        course_name=course_name,
        session_number=session_number,
    )
