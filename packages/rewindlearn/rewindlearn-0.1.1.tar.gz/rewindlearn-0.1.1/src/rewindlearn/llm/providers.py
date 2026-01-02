"""LLM provider clients."""

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from rewindlearn.core.config import Settings
from rewindlearn.core.exceptions import LLMError

# OpenRouter API base URL
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Model name mapping: OpenRouter short name -> Direct API model ID
# Used when falling back from OpenRouter to direct Anthropic API
ANTHROPIC_MODEL_MAP = {
    "claude-sonnet-4": "claude-sonnet-4-20250514",
    "claude-sonnet-4.5": "claude-sonnet-4-5-20250929",
    "claude-opus-4": "claude-opus-4-20250514",
    "claude-haiku-4.5": "claude-haiku-4-5-20250929",
    "claude-3-5-sonnet": "claude-3-5-sonnet-20241022",
    "claude-3-opus": "claude-3-opus-20240229",
    "claude-3-sonnet": "claude-3-sonnet-20240229",
    "claude-3-haiku": "claude-3-haiku-20240307",
}


class LLMProvider:
    """Factory for LLM clients.

    Provider selection priority:
    1. OpenRouter (if model contains "/" and openrouter_api_key is set)
    2. Anthropic (if model starts with "claude" and anthropic_api_key is set)
    3. OpenAI (if model starts with "gpt" and openai_api_key is set)
    4. OpenAI with gpt-4o (last resort fallback if openai_api_key is set)
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._clients: dict[str, BaseChatModel] = {}

    def get_client(self, model: str) -> BaseChatModel:
        """Get or create an LLM client for the specified model."""
        if model in self._clients:
            return self._clients[model]

        client = self._create_client(model)
        self._clients[model] = client
        return client

    def _create_client(self, model: str) -> BaseChatModel:
        """Create a new LLM client.

        Supports OpenRouter (provider/model format), Anthropic, and OpenAI.
        Fallback chain: OpenRouter -> Anthropic -> OpenAI
        """
        # Extract base model name for fallback (e.g., "anthropic/claude-sonnet-4" -> "claude-sonnet-4")
        base_model = model.split("/")[-1] if "/" in model else model

        # OpenRouter format: provider/model (e.g., "anthropic/claude-sonnet-4")
        if "/" in model and self.settings.openrouter_api_key:
            return ChatOpenAI(
                model=model,
                api_key=self.settings.openrouter_api_key,
                base_url=OPENROUTER_BASE_URL,
                max_retries=self.settings.max_retries,
            )

        # Fallback: Try Anthropic if model is Claude-based
        if base_model.startswith("claude") and self.settings.anthropic_api_key:
            # Map OpenRouter short name to Anthropic API model ID, or use configured fallback
            anthropic_model = ANTHROPIC_MODEL_MAP.get(
                base_model, self.settings.anthropic_fallback_model
            )
            return ChatAnthropic(
                model=anthropic_model,
                api_key=self.settings.anthropic_api_key,
                max_retries=self.settings.max_retries,
            )

        # Fallback: Try OpenAI if model is GPT-based
        if base_model.startswith("gpt") and self.settings.openai_api_key:
            return ChatOpenAI(
                model=base_model,
                api_key=self.settings.openai_api_key,
                max_retries=self.settings.max_retries,
            )

        # Last resort: Use OpenAI with configured fallback model if available
        if self.settings.openai_api_key:
            return ChatOpenAI(
                model=self.settings.openai_fallback_model,
                api_key=self.settings.openai_api_key,
                max_retries=self.settings.max_retries,
            )

        # Error handling with helpful messages
        if "/" in model and not self.settings.openrouter_api_key:
            if base_model.startswith("claude") and not self.settings.anthropic_api_key:
                raise LLMError(
                    f"No API key configured for model: {model}. "
                    "Set REWINDLEARN_OPENROUTER_API_KEY or REWINDLEARN_ANTHROPIC_API_KEY"
                )
            elif base_model.startswith("gpt") and not self.settings.openai_api_key:
                raise LLMError(
                    f"No API key configured for model: {model}. "
                    "Set REWINDLEARN_OPENROUTER_API_KEY or REWINDLEARN_OPENAI_API_KEY"
                )
            raise LLMError(
                f"OpenRouter API key not configured for model: {model}. "
                "Set REWINDLEARN_OPENROUTER_API_KEY"
            )
        elif base_model.startswith("claude"):
            raise LLMError(
                f"Anthropic API key not configured for model: {model}. "
                "Set REWINDLEARN_ANTHROPIC_API_KEY"
            )
        elif base_model.startswith("gpt"):
            raise LLMError(
                f"OpenAI API key not configured for model: {model}. "
                "Set REWINDLEARN_OPENAI_API_KEY"
            )
        else:
            raise LLMError(f"Unknown model format: {model}")
