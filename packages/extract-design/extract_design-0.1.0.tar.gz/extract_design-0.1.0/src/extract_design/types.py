"""Type definitions for the extract.design SDK."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, TypedDict

if TYPE_CHECKING:
    from collections.abc import Callable

ExtractionStatus = Literal["pending", "processing", "completed", "failed"]


class _ApiErrorRequired(TypedDict):
    """Required fields for API error response."""

    error: str


class ApiErrorResponse(_ApiErrorRequired, total=False):
    """API error response structure."""

    error_details: str
    upgrade_url: str
    current_plan: str


@dataclass
class ExtractOptions:
    """Options for submitting an extraction."""

    image_url: str | None = None
    """URL of the image to extract from."""

    image_base64: str | None = None
    """Base64-encoded image data."""

    preset: str | None = None
    """Preset name for processing configuration."""

    scale: int | None = None
    """Upscale factor (1-10, subject to plan limits)."""

    face_enhance: bool | None = None
    """Enable face enhancement."""

    webhook_url: str | None = None
    """Webhook URL to receive completion notification (Pro+ plans)."""

    metadata: dict[str, Any] | None = None
    """Custom metadata to attach to the extraction (max 4KB)."""

    remix_prompt: str | None = None
    """Prompt to remix/transform the extracted design."""


@dataclass
class ExtractResponse:
    """Response from submitting an extraction."""

    extraction_id: str
    """Unique identifier for the extraction."""

    status: ExtractionStatus
    """Current status."""

    preset: str
    """Preset used for processing."""

    estimated_time_seconds: int
    """Estimated time until completion in seconds."""


@dataclass
class ExtractionResult:
    """Response from getting extraction status."""

    extraction_id: str
    """Unique identifier for the extraction."""

    status: ExtractionStatus
    """Current status."""

    extraction_url: str | None = None
    """URL to the extracted design (available when completed)."""

    metadata: dict[str, Any] | None = None
    """Custom metadata attached to the extraction."""

    estimated_seconds_remaining: int | None = None
    """Estimated seconds remaining (available when pending/processing)."""

    remix_prompt: str | None = None
    """The remix prompt used (if any)."""

    remix_url: str | None = None
    """URL to the remixed design (available when completed with remix)."""

    error: str | None = None
    """Error message (available when failed)."""


@dataclass
class Credits:
    """Credit usage information."""

    subscription: int
    """Credits from subscription."""

    purchased: int
    """Credits from one-time purchases."""

    total: int
    """Total available credits."""

    limit: int
    """Monthly credit limit."""

    used: int
    """Credits used this period."""


@dataclass
class UsageResponse:
    """Response from the usage endpoint."""

    credits: Credits
    """Credit information."""

    plan: str
    """Current plan name."""


@dataclass
class WaitOptions:
    """Options for polling/waiting for extraction completion."""

    timeout: float = 600.0
    """Maximum time to wait in seconds (default: 600 = 10 minutes)."""

    interval: float = 5.0
    """Interval between status checks in seconds (default: 5 seconds)."""

    on_progress: Callable[[ExtractionResult], None] | None = field(default=None, repr=False)
    """Callback called on each status check."""
