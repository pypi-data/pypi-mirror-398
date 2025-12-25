from sayou.core.exceptions import SayouCoreError


class ChunkingError(SayouCoreError):
    """Base exception for all chunking related errors."""

    pass


class SplitterError(ChunkingError):
    """Raised when a specific splitter fails."""

    pass
