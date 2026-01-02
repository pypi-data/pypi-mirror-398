"""LangGraph workflow construction."""

from typing import Any, Callable

from langgraph.graph import END, StateGraph

from rewindlearn.chains import create_chain
from rewindlearn.llm.router import LLMRouter
from rewindlearn.templates.models import Template
from rewindlearn.workflow.state import SessionState


class WorkflowBuilder:
    """Build LangGraph workflows from templates."""

    def __init__(self, template: Template, router: LLMRouter):
        self.template = template
        self.router = router

    def build(self) -> StateGraph:
        """Build and compile the workflow graph."""
        graph = StateGraph(SessionState)
        tasks = self.template.get_tasks()
        dep_graph = self.template.build_dependency_graph()

        # Add nodes for each task
        for task in tasks:
            chain = create_chain(task, self.router)
            graph.add_node(task.name, self._make_node(chain, task.name))

        # Add edges based on dependencies
        for task in tasks:
            if not dep_graph[task.name]:
                # No dependencies - start from __start__
                graph.add_edge("__start__", task.name)
            else:
                # Add edge from each dependency
                for dep in dep_graph[task.name]:
                    graph.add_edge(dep, task.name)

        # All leaf nodes go to END
        leaf_tasks = self._find_leaf_tasks(tasks, dep_graph)
        for leaf in leaf_tasks:
            graph.add_edge(leaf, END)

        return graph.compile()

    def _make_node(self, chain: Any, task_name: str) -> Callable:
        """Create a node function for the graph."""

        async def node(state: SessionState) -> dict[str, Any]:
            try:
                result = await chain.run(dict(state))
                return {
                    task_name: result,
                    "completed_tasks": [task_name]
                }
            except Exception as e:
                return {
                    "errors": [f"{task_name}: {str(e)}"]
                }

        return node

    def _find_leaf_tasks(
        self,
        tasks: list,
        dep_graph: dict[str, list[str]]
    ) -> list[str]:
        """Find tasks that no other task depends on."""
        all_deps: set[str] = set()
        for deps in dep_graph.values():
            all_deps.update(deps)

        return [t.name for t in tasks if t.name not in all_deps]
