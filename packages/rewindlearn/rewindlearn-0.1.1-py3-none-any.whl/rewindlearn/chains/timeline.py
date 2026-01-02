"""Concept timeline chain."""

from rewindlearn.chains.base import BaseChain


class TimelineChain(BaseChain):
    """Generate concept timeline."""

    def post_process(self, result: str) -> str:
        """Ensure proper table formatting."""
        result = super().post_process(result)
        if not result.startswith("#"):
            result = "# Concept Timeline\n\n" + result
        return result
