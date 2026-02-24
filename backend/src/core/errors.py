class AppError(Exception):
    """Base app exception."""


class IngestionError(AppError):
    """Raised when FAQ ingestion fails."""


class IndexNotBuiltError(AppError):
    """Raised when index artifacts are missing or invalid."""


class EmbeddingProviderError(AppError):
    """Raised when embedding provider fails."""


class LLMProviderError(AppError):
    """Raised when LLM provider fails."""