"""Tests for the ExtractDesign client."""

import pytest

from extract_design import ExtractDesign


def test_client_requires_api_key() -> None:
    """Test that client raises error without API key."""
    with pytest.raises(ValueError, match="API key is required"):
        ExtractDesign(api_key="")


def test_client_initialization() -> None:
    """Test basic client initialization."""
    client = ExtractDesign(api_key="sk_test_123")
    assert client._api_key == "sk_test_123"
    assert client._base_url == "https://extract.design"
    assert client._timeout == 30.0
    client.close()


def test_client_custom_config() -> None:
    """Test client with custom configuration."""
    client = ExtractDesign(
        api_key="sk_test_123",
        base_url="https://custom.example.com/",
        timeout=60.0,
    )
    assert client._base_url == "https://custom.example.com"  # Trailing slash removed
    assert client._timeout == 60.0
    client.close()


def test_client_context_manager() -> None:
    """Test client as context manager."""
    with ExtractDesign(api_key="sk_test_123") as client:
        assert client._api_key == "sk_test_123"


def test_extract_requires_image() -> None:
    """Test that extract raises error without image."""
    client = ExtractDesign(api_key="sk_test_123")
    with pytest.raises(ValueError, match="Either image_url or image_base64 is required"):
        client.extract()
    client.close()


def test_extract_rejects_both_image_types() -> None:
    """Test that extract raises error with both image types."""
    client = ExtractDesign(api_key="sk_test_123")
    with pytest.raises(ValueError, match="Only one of image_url or image_base64"):
        client.extract(image_url="https://example.com/img.jpg", image_base64="base64data")
    client.close()
