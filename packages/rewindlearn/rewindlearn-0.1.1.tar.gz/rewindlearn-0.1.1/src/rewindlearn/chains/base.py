"""Base chain class for LLM processing tasks."""

from typing import Any

from langchain_core.prompts import PromptTemplate
from langsmith import traceable

from rewindlearn.llm.router import LLMRouter
from rewindlearn.templates.models import TaskDefinition


class BaseChain:
    """Base class for processing chains."""

    def __init__(self, task: TaskDefinition, router: LLMRouter):
        self.task = task
        self.router = router
        self.prompt = PromptTemplate.from_template(task.prompt_template)

    @traceable
    async def run(self, inputs: dict[str, Any]) -> str:
        """Execute the chain with given inputs."""
        # Fill in missing optional inputs with empty strings
        template_vars = self.prompt.input_variables
        safe_inputs = {k: inputs.get(k, "") for k in template_vars}

        formatted_prompt = self.prompt.format(**safe_inputs)

        result = await self.router.invoke(
            formatted_prompt,
            self.task.llm_config,
            task_name=self.task.name
        )

        return self.post_process(result)

    def post_process(self, result: str) -> str:
        """Override for custom post-processing."""
        return result.strip()
