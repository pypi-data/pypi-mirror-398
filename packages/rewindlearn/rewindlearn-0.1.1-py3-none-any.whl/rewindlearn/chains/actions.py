"""Action items chain."""

from rewindlearn.chains.base import BaseChain


class ActionsChain(BaseChain):
    """Extract action items."""

    def post_process(self, result: str) -> str:
        result = super().post_process(result)
        if not result.startswith("#"):
            result = "# Action Items\n\n" + result
        return result
