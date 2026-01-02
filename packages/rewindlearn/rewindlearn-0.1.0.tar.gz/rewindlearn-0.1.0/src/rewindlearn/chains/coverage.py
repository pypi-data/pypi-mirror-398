"""Coverage gaps chain."""

from rewindlearn.chains.base import BaseChain


class CoverageChain(BaseChain):
    """Analyze coverage gaps."""

    def post_process(self, result: str) -> str:
        result = super().post_process(result)
        if not result.startswith("#"):
            result = "# Coverage Gaps\n\n" + result
        return result
