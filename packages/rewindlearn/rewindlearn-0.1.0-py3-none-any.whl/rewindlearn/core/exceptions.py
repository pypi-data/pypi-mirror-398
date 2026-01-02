"""Custom exceptions for Rewind.Learn."""


class RewindLearnError(Exception):
    """Base exception for Rewind.Learn."""

    pass


class ConfigurationError(RewindLearnError):
    """Configuration-related errors."""

    pass


class TemplateError(RewindLearnError):
    """Template loading or validation errors."""

    pass


class ProcessorError(RewindLearnError):
    """File processing errors."""

    pass


class WorkflowError(RewindLearnError):
    """Workflow execution errors."""

    pass


class LLMError(RewindLearnError):
    """LLM invocation errors."""

    pass
