"""Pydantic models for template definitions."""

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class LLMConfig(BaseModel):
    """LLM configuration for a task."""

    model: str = "claude-sonnet-4-20250514"
    temperature: float = Field(default=0.3, ge=0.0, le=1.0)
    max_tokens: int = Field(default=4000, gt=0)
    fallback_model: Optional[str] = None


class TaskDefinition(BaseModel):
    """Definition of a single processing task."""

    name: str = Field(description="Unique task identifier")
    prompt_template: str = Field(description="Prompt template with {placeholders}")
    llm_config: LLMConfig = Field(default_factory=LLMConfig)
    dependencies: list[str] = Field(default_factory=list)
    output_format: Literal["markdown", "csv", "json"] = "markdown"


class InputSchema(BaseModel):
    """Schema for template inputs."""

    required: list[str] = Field(description="Required input fields")
    optional: list[str] = Field(default_factory=list)


class OutputSchema(BaseModel):
    """Schema for template outputs."""

    deliverables: list[str] = Field(description="List of output deliverables")
    formats: list[Literal["markdown", "pdf", "html", "csv"]] = Field(default=["markdown"])
    languages: list[str] = Field(default=["en"])
    naming_pattern: str = Field(default="{template_id}-{deliverable}.{format}")


class Template(BaseModel):
    """Complete template definition."""

    template_id: str = Field(description="Unique template identifier")
    name: str = Field(description="Human-readable name")
    version: str = Field(description="Template version")
    description: Optional[str] = None
    inputs: InputSchema
    processing: dict = Field(description="Contains 'tasks' list")
    outputs: OutputSchema

    @field_validator("processing")
    @classmethod
    def validate_processing(cls, v: dict) -> dict:
        """Ensure processing contains tasks."""
        if "tasks" not in v:
            raise ValueError("processing must contain 'tasks' list")
        if not isinstance(v["tasks"], list):
            raise ValueError("processing.tasks must be a list")
        return v

    def get_tasks(self) -> list[TaskDefinition]:
        """Get task definitions from processing config."""
        return [TaskDefinition(**t) for t in self.processing["tasks"]]

    def build_dependency_graph(self) -> dict[str, list[str]]:
        """Build task dependency graph for execution ordering."""
        tasks = self.get_tasks()
        return {t.name: t.dependencies for t in tasks}

    def validate_dependencies(self) -> list[str]:
        """Validate all dependencies exist and no cycles."""
        errors = []
        tasks = self.get_tasks()
        task_names = {t.name for t in tasks}

        for task in tasks:
            for dep in task.dependencies:
                if dep not in task_names:
                    errors.append(f"Task '{task.name}' depends on unknown task '{dep}'")

        # Check for cycles using DFS
        if self._has_circular_deps():
            errors.append("Circular dependencies detected in task graph")

        return errors

    def _has_circular_deps(self) -> bool:
        """Detect circular dependencies using DFS."""
        graph = self.build_dependency_graph()
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            for dep in graph.get(node, []):
                if dep not in visited:
                    if dfs(dep):
                        return True
                elif dep in rec_stack:
                    return True
            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                if dfs(node):
                    return True
        return False
