"""Application configuration using Pydantic Settings."""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="REWINDLEARN_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM Providers
    openrouter_api_key: Optional[str] = Field(default=None, description="OpenRouter API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    default_provider: str = Field(default="openrouter", description="Default LLM provider")
    default_model: str = Field(
        default="anthropic/claude-sonnet-4",
        description="Default model to use (OpenRouter format: provider/model)"
    )

    # LangSmith Observability
    langsmith_api_key: Optional[str] = Field(default=None, description="LangSmith API key")
    langsmith_project: str = Field(default="rewindlearn", description="LangSmith project name")
    langsmith_tracing: bool = Field(default=False, description="Enable LangSmith tracing")

    # Processing Settings
    max_retries: int = Field(default=3, ge=1, le=10, description="Max LLM retry attempts")
    temperature_default: float = Field(default=0.3, ge=0.0, le=1.0)
    max_tokens_default: int = Field(default=4000, gt=0)

    # Fallback Models
    anthropic_fallback_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Anthropic model to use when falling back from OpenRouter"
    )
    openai_fallback_model: str = Field(
        default="gpt-4o",
        description="OpenAI model to use as last resort fallback"
    )

    # Paths
    templates_dir: Path = Field(default=Path("templates"), description="Templates directory")
    output_dir: Path = Field(default=Path("output"), description="Output directory")

    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for the specified provider."""
        if provider == "openrouter":
            return self.openrouter_api_key
        elif provider == "anthropic":
            return self.anthropic_api_key
        elif provider == "openai":
            return self.openai_api_key
        return None

    def validate_api_keys(self) -> None:
        """Raise error if no API keys are configured."""
        if not self.openrouter_api_key and not self.anthropic_api_key and not self.openai_api_key:
            raise ValueError(
                "No LLM API keys configured. "
                "Set REWINDLEARN_OPENROUTER_API_KEY, REWINDLEARN_ANTHROPIC_API_KEY, "
                "or REWINDLEARN_OPENAI_API_KEY"
            )


# Global settings instance (lazy loaded)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
