"""Session summary chain."""

from rewindlearn.chains.base import BaseChain


class SummaryChain(BaseChain):
    """Generate session summary."""

    def post_process(self, result: str) -> str:
        """Ensure proper markdown formatting."""
        result = super().post_process(result)
        # Ensure it starts with a heading if not present
        if not result.startswith("#"):
            result = "# Session Summary\n\n" + result
        return result
