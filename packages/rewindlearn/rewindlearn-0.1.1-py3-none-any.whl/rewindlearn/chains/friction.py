"""Friction analysis chain."""

from rewindlearn.chains.base import BaseChain


class FrictionChain(BaseChain):
    """Analyze student friction points."""

    def post_process(self, result: str) -> str:
        result = super().post_process(result)
        if not result.startswith("#"):
            result = "# Friction Analysis\n\n" + result
        return result
