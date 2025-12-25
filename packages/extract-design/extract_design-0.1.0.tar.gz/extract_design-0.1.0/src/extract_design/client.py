"""Client for the extract.design API."""

from __future__ import annotations

import time
from typing import Any

import httpx

from .errors import (
    ApiError,
    AuthenticationError,
    ExtractionFailedError,
    InsufficientCreditsError,
    NotFoundError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)
from .types import (
    ApiErrorResponse,
    Credits,
    ExtractionResult,
    ExtractOptions,
    ExtractResponse,
    UsageResponse,
    WaitOptions,
)

DEFAULT_BASE_URL = "https://extract.design"
DEFAULT_TIMEOUT = 30.0
DEFAULT_WAIT_TIMEOUT = 600.0  # 10 minutes
DEFAULT_WAIT_INTERVAL = 5.0  # 5 seconds


class ExtractDesign:
    """Client for the extract.design API.

    Example:
        ```python
        from extract_design import ExtractDesign

        client = ExtractDesign(api_key="sk_live_...")

        # Submit an extraction
        response = client.extract(image_url="https://example.com/product.jpg")

        # Wait for completion
        result = client.wait_for_completion(response.extraction_id)
        print(result.extraction_url)
        ```
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the ExtractDesign client.

        Args:
            api_key: Your API key (starts with sk_live_ or sk_test_).
            base_url: Base URL for the API (default: https://extract.design).
            timeout: Request timeout in seconds (default: 30.0).
        """
        if not api_key:
            raise ValueError("API key is required")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "extract-design-python/0.1.0",
            },
        )

    def __enter__(self) -> ExtractDesign:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def _request(self, method: str, path: str, json: dict[str, Any] | None = None) -> Any:
        """Make an authenticated request to the API."""
        response = self._client.request(method, path, json=json)

        if not response.is_success:
            self._handle_error_response(response)

        return response.json()

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses and raise appropriate errors."""
        try:
            data: ApiErrorResponse = response.json()
        except Exception:
            data = {"error": response.text or "Unknown error"}

        status = response.status_code

        if status == 400:
            raise ValidationError(data)
        elif status == 401:
            raise AuthenticationError(data)
        elif status == 402:
            raise InsufficientCreditsError(data)
        elif status == 404:
            raise NotFoundError(data)
        elif status == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(data, int(retry_after) if retry_after else None)
        else:
            raise ApiError(status, data)

    def extract(
        self,
        *,
        image_url: str | None = None,
        image_base64: str | None = None,
        preset: str | None = None,
        scale: int | None = None,
        face_enhance: bool | None = None,
        webhook_url: str | None = None,
        metadata: dict[str, Any] | None = None,
        remix_prompt: str | None = None,
    ) -> ExtractResponse:
        """Submit an image for design extraction.

        Args:
            image_url: URL of the image to extract from.
            image_base64: Base64-encoded image data.
            preset: Preset name for processing configuration.
            scale: Upscale factor (1-10, subject to plan limits).
            face_enhance: Enable face enhancement.
            webhook_url: Webhook URL to receive completion notification (Pro+ plans).
            metadata: Custom metadata to attach to the extraction (max 4KB).
            remix_prompt: Prompt to remix/transform the extracted design.

        Returns:
            The extraction ID and initial status.

        Example:
            ```python
            # Extract from URL
            result = client.extract(image_url="https://example.com/product.jpg")

            # Extract with upscaling
            result = client.extract(
                image_url="https://example.com/product.jpg",
                scale=4,
            )

            # Extract and remix
            result = client.extract(
                image_url="https://example.com/product.jpg",
                remix_prompt="Make it a watermelon",
            )
            ```
        """
        if not image_url and not image_base64:
            raise ValueError("Either image_url or image_base64 is required")

        if image_url and image_base64:
            raise ValueError("Only one of image_url or image_base64 should be provided")

        body: dict[str, Any] = {}

        if image_url:
            body["image_url"] = image_url
        if image_base64:
            body["image_file_b64"] = image_base64
        if preset:
            body["preset"] = preset
        if scale is not None:
            body["scale"] = scale
        if face_enhance is not None:
            body["face_enhance"] = face_enhance
        if webhook_url:
            body["webhook_url"] = webhook_url
        if metadata:
            body["metadata"] = metadata
        if remix_prompt:
            body["remix_prompt"] = remix_prompt

        data = self._request("POST", "/api/v1/extract", json=body)

        return ExtractResponse(
            extraction_id=data["extraction_id"],
            status=data["status"],
            preset=data["preset"],
            estimated_time_seconds=data["estimated_time_seconds"],
        )

    def extract_from_options(self, options: ExtractOptions) -> ExtractResponse:
        """Submit an extraction using an ExtractOptions object.

        Args:
            options: Extraction options.

        Returns:
            The extraction ID and initial status.
        """
        return self.extract(
            image_url=options.image_url,
            image_base64=options.image_base64,
            preset=options.preset,
            scale=options.scale,
            face_enhance=options.face_enhance,
            webhook_url=options.webhook_url,
            metadata=options.metadata,
            remix_prompt=options.remix_prompt,
        )

    def get_extraction(self, extraction_id: str) -> ExtractionResult:
        """Get the status and result of an extraction.

        Args:
            extraction_id: The extraction ID from the extract() call.

        Returns:
            The current status and result.

        Example:
            ```python
            result = client.get_extraction("550e8400-e29b-41d4-a716-446655440000")
            if result.status == "completed":
                print(result.extraction_url)
            ```
        """
        data = self._request("GET", f"/api/v1/extract/{extraction_id}")

        return ExtractionResult(
            extraction_id=data["extraction_id"],
            status=data["status"],
            extraction_url=data.get("extraction_url"),
            metadata=data.get("metadata"),
            estimated_seconds_remaining=data.get("estimated_seconds_remaining"),
            remix_prompt=data.get("remix_prompt"),
            remix_url=data.get("remix_url"),
            error=data.get("error"),
        )

    def wait_for_completion(
        self,
        extraction_id: str,
        *,
        timeout: float = DEFAULT_WAIT_TIMEOUT,
        interval: float = DEFAULT_WAIT_INTERVAL,
        on_progress: Any | None = None,
    ) -> ExtractionResult:
        """Wait for an extraction to complete.

        Args:
            extraction_id: The extraction ID to wait for.
            timeout: Maximum time to wait in seconds (default: 600 = 10 minutes).
            interval: Interval between status checks in seconds (default: 5).
            on_progress: Callback called on each status check.

        Returns:
            The completed extraction result.

        Raises:
            TimeoutError: If the extraction doesn't complete within the timeout.
            ExtractionFailedError: If the extraction fails.

        Example:
            ```python
            # Simple wait
            result = client.wait_for_completion(extraction_id)

            # With progress callback
            result = client.wait_for_completion(
                extraction_id,
                on_progress=lambda status: print(f"Status: {status.status}"),
            )

            # Custom timeout
            result = client.wait_for_completion(
                extraction_id,
                timeout=120,  # 2 minutes
                interval=3,   # Check every 3 seconds
            )
            ```
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            result = self.get_extraction(extraction_id)

            if on_progress:
                on_progress(result)

            if result.status == "completed":
                return result

            if result.status == "failed":
                raise ExtractionFailedError(extraction_id, result.error)

            time.sleep(interval)

        raise TimeoutError(extraction_id, timeout)

    def wait_for_completion_with_options(
        self,
        extraction_id: str,
        options: WaitOptions | None = None,
    ) -> ExtractionResult:
        """Wait for an extraction to complete using a WaitOptions object.

        Args:
            extraction_id: The extraction ID to wait for.
            options: Polling options.

        Returns:
            The completed extraction result.
        """
        if options is None:
            options = WaitOptions()

        return self.wait_for_completion(
            extraction_id,
            timeout=options.timeout,
            interval=options.interval,
            on_progress=options.on_progress,
        )

    def extract_and_wait(
        self,
        *,
        image_url: str | None = None,
        image_base64: str | None = None,
        preset: str | None = None,
        scale: int | None = None,
        face_enhance: bool | None = None,
        webhook_url: str | None = None,
        metadata: dict[str, Any] | None = None,
        remix_prompt: str | None = None,
        timeout: float = DEFAULT_WAIT_TIMEOUT,
        interval: float = DEFAULT_WAIT_INTERVAL,
        on_progress: Any | None = None,
    ) -> ExtractionResult:
        """Submit an extraction and wait for it to complete.

        Args:
            image_url: URL of the image to extract from.
            image_base64: Base64-encoded image data.
            preset: Preset name for processing configuration.
            scale: Upscale factor (1-10, subject to plan limits).
            face_enhance: Enable face enhancement.
            webhook_url: Webhook URL to receive completion notification (Pro+ plans).
            metadata: Custom metadata to attach to the extraction (max 4KB).
            remix_prompt: Prompt to remix/transform the extracted design.
            timeout: Maximum time to wait in seconds (default: 600 = 10 minutes).
            interval: Interval between status checks in seconds (default: 5).
            on_progress: Callback called on each status check.

        Returns:
            The completed extraction result.

        Example:
            ```python
            # One-liner for extraction
            result = client.extract_and_wait(
                image_url="https://example.com/product.jpg",
            )
            print(result.extraction_url)
            ```
        """
        response = self.extract(
            image_url=image_url,
            image_base64=image_base64,
            preset=preset,
            scale=scale,
            face_enhance=face_enhance,
            webhook_url=webhook_url,
            metadata=metadata,
            remix_prompt=remix_prompt,
        )
        return self.wait_for_completion(
            response.extraction_id,
            timeout=timeout,
            interval=interval,
            on_progress=on_progress,
        )

    def get_usage(self) -> UsageResponse:
        """Get account usage and credit information.

        Returns:
            Credit balance and plan information.

        Example:
            ```python
            usage = client.get_usage()
            print(f"Credits remaining: {usage.credits.total}")
            print(f"Plan: {usage.plan}")
            ```
        """
        data = self._request("GET", "/api/v1/usage")

        return UsageResponse(
            credits=Credits(
                subscription=data["credits"]["subscription"],
                purchased=data["credits"]["purchased"],
                total=data["credits"]["total"],
                limit=data["credits"]["limit"],
                used=data["credits"]["used"],
            ),
            plan=data["plan"],
        )

    def verify_api_key(self) -> bool:
        """Verify that the API key is valid.

        Returns:
            True if the API key is valid.

        Raises:
            AuthenticationError: If the API key is invalid.

        Example:
            ```python
            is_valid = client.verify_api_key()
            ```
        """
        self._request("GET", "/api/v1/ping")
        return True
