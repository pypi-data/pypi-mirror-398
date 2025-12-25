from sayou.core.exceptions import SayouCoreError


class LoaderError(SayouCoreError):
    """Base exception for all loader errors."""

    pass


class WriterError(LoaderError):
    """Raised when a writing operation fails."""

    pass
