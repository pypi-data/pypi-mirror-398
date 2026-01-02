"""LLM routing with fallback support."""

from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable

from rewindlearn.core.exceptions import LLMError
from rewindlearn.core.logging import get_logger
from rewindlearn.llm.providers import LLMProvider
from rewindlearn.templates.models import LLMConfig

logger = get_logger(__name__)


class LLMRouter:
    """Route LLM requests with fallback support."""

    def __init__(self, provider: LLMProvider):
        self.provider = provider

    @traceable(name="llm_invoke")
    async def invoke(
        self,
        prompt: str,
        config: LLMConfig,
        task_name: str = "unknown",
        system_prompt: Optional[str] = None,
    ) -> str:
        """Invoke LLM with the given prompt and config."""
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        try:
            client = self.provider.get_client(config.model)
            response = await client.ainvoke(
                messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )
            return str(response.content)

        except Exception as e:
            logger.warning(f"Primary model failed for {task_name}: {e}")

            # Try fallback if configured
            if config.fallback_model:
                try:
                    logger.info(f"Trying fallback model: {config.fallback_model}")
                    fallback_client = self.provider.get_client(config.fallback_model)
                    response = await fallback_client.ainvoke(
                        messages,
                        temperature=config.temperature,
                        max_tokens=config.max_tokens,
                    )
                    return str(response.content)
                except Exception as fallback_error:
                    raise LLMError(
                        f"Both primary ({config.model}) and fallback ({config.fallback_model}) "
                        f"failed for {task_name}: {fallback_error}"
                    )

            raise LLMError(f"LLM invocation failed for {task_name}: {e}")
