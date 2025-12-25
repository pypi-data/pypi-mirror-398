"""Official Python SDK for the extract.design API."""

from .client import ExtractDesign
from .errors import (
    ApiError,
    AuthenticationError,
    ExtractDesignError,
    ExtractionFailedError,
    InsufficientCreditsError,
    NotFoundError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)
from .types import (
    Credits,
    ExtractionResult,
    ExtractionStatus,
    ExtractOptions,
    ExtractResponse,
    UsageResponse,
    WaitOptions,
)

__all__ = [
    # Client
    "ExtractDesign",
    # Errors
    "ExtractDesignError",
    "ApiError",
    "AuthenticationError",
    "InsufficientCreditsError",
    "RateLimitError",
    "NotFoundError",
    "ValidationError",
    "TimeoutError",
    "ExtractionFailedError",
    # Types
    "ExtractionStatus",
    "ExtractOptions",
    "ExtractResponse",
    "ExtractionResult",
    "Credits",
    "UsageResponse",
    "WaitOptions",
]

__version__ = "0.1.0"
