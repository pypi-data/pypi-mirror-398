"""Processing chains for session analysis."""

from rewindlearn.chains.base import BaseChain
from rewindlearn.chains.summary import SummaryChain
from rewindlearn.chains.timeline import TimelineChain
from rewindlearn.chains.friction import FrictionChain
from rewindlearn.chains.coverage import CoverageChain
from rewindlearn.chains.resources import ResourcesChain
from rewindlearn.chains.actions import ActionsChain
from rewindlearn.chains.chunks import ChunksChain

from rewindlearn.llm.router import LLMRouter
from rewindlearn.templates.models import TaskDefinition


# Chain registry
CHAIN_CLASSES: dict[str, type[BaseChain]] = {
    "session_summary": SummaryChain,
    "concept_timeline": TimelineChain,
    "friction_analysis": FrictionChain,
    "coverage_gaps": CoverageChain,
    "learning_resources": ResourcesChain,
    "action_items": ActionsChain,
    "concept_chunks": ChunksChain,
}


def create_chain(task: TaskDefinition, router: LLMRouter) -> BaseChain:
    """Create a chain instance for the given task."""
    chain_class = CHAIN_CLASSES.get(task.name, BaseChain)
    return chain_class(task, router)


__all__ = [
    "BaseChain",
    "create_chain",
    "SummaryChain",
    "TimelineChain",
    "FrictionChain",
    "CoverageChain",
    "ResourcesChain",
    "ActionsChain",
    "ChunksChain",
]
