"""Learning resources chain."""

from rewindlearn.chains.base import BaseChain


class ResourcesChain(BaseChain):
    """Curate learning resources."""

    def post_process(self, result: str) -> str:
        result = super().post_process(result)
        if not result.startswith("#"):
            result = "# Learning Resources\n\n" + result
        return result
