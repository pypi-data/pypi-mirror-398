"""Custom exception classes for the extract.design SDK."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .types import ApiErrorResponse


class ExtractDesignError(Exception):
    """Base error class for all extract.design API errors."""

    pass


class ApiError(ExtractDesignError):
    """Error thrown when the API returns an error response."""

    def __init__(self, status: int, response: ApiErrorResponse) -> None:
        self.status = status
        self.error_message = response["error"]
        self.error_details = response.get("error_details")
        super().__init__(f"API error ({status}): {response['error']}")


class AuthenticationError(ApiError):
    """Error thrown when authentication fails (401)."""

    def __init__(self, response: ApiErrorResponse) -> None:
        super().__init__(401, response)


class InsufficientCreditsError(ApiError):
    """Error thrown when the account has insufficient credits (402)."""

    def __init__(self, response: ApiErrorResponse) -> None:
        super().__init__(402, response)


class RateLimitError(ApiError):
    """Error thrown when rate limited (429)."""

    def __init__(self, response: ApiErrorResponse, retry_after: int | None = None) -> None:
        super().__init__(429, response)
        self.retry_after = retry_after


class NotFoundError(ApiError):
    """Error thrown when a resource is not found (404)."""

    def __init__(self, response: ApiErrorResponse) -> None:
        super().__init__(404, response)


class ValidationError(ApiError):
    """Error thrown when the request is invalid (400)."""

    def __init__(self, response: ApiErrorResponse) -> None:
        super().__init__(400, response)


class TimeoutError(ExtractDesignError):
    """Error thrown when waiting for an extraction times out."""

    def __init__(self, extraction_id: str, timeout: float) -> None:
        self.extraction_id = extraction_id
        self.timeout = timeout
        super().__init__(f"Extraction {extraction_id} did not complete within {timeout}s")


class ExtractionFailedError(ExtractDesignError):
    """Error thrown when an extraction fails."""

    def __init__(self, extraction_id: str, reason: str | None = None) -> None:
        self.extraction_id = extraction_id
        self.reason = reason
        message = f"Extraction {extraction_id} failed"
        if reason:
            message += f": {reason}"
        super().__init__(message)
