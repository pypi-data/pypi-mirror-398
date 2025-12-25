# extract-design

Official Python SDK for the [extract.design](https://extract.design) API - AI-powered design extraction for print-on-demand sellers.

## Installation

```bash
pip install extract-design
```

## Quick Start

```python
from extract_design import ExtractDesign

# Initialize the client
client = ExtractDesign(api_key="sk_live_...")

# Extract a design and wait for completion
result = client.extract_and_wait(
    image_url="https://example.com/product.jpg"
)

print(result.extraction_url)
```

## Usage

### Submit an Extraction

```python
from extract_design import ExtractDesign

client = ExtractDesign(api_key="sk_live_...")

# Submit and get extraction ID
response = client.extract(
    image_url="https://example.com/product.jpg"
)

print(f"Extraction ID: {response.extraction_id}")
print(f"Status: {response.status}")
print(f"Estimated time: {response.estimated_time_seconds}s")
```

### Check Extraction Status

```python
result = client.get_extraction(extraction_id)

if result.status == "completed":
    print(f"Design URL: {result.extraction_url}")
elif result.status == "failed":
    print(f"Error: {result.error}")
```

### Wait for Completion

```python
# Simple wait
result = client.wait_for_completion(extraction_id)

# With progress callback
result = client.wait_for_completion(
    extraction_id,
    on_progress=lambda r: print(f"Status: {r.status}"),
)

# Custom timeout and interval
result = client.wait_for_completion(
    extraction_id,
    timeout=120,  # 2 minutes
    interval=3,   # Check every 3 seconds
)
```

### Extract with Options

```python
# With upscaling
result = client.extract_and_wait(
    image_url="https://example.com/product.jpg",
    scale=4,
)

# With remix prompt
result = client.extract_and_wait(
    image_url="https://example.com/product.jpg",
    remix_prompt="Make it a watermelon",
)

# With webhook notification (Pro+ plans)
response = client.extract(
    image_url="https://example.com/product.jpg",
    webhook_url="https://your-api.com/webhook",
    metadata={"order_id": "12345"},
)
```

### Check Usage

```python
usage = client.get_usage()

print(f"Plan: {usage.plan}")
print(f"Credits remaining: {usage.credits.total}")
print(f"Credits used: {usage.credits.used}")
```

### Verify API Key

```python
try:
    client.verify_api_key()
    print("API key is valid")
except AuthenticationError:
    print("Invalid API key")
```

## Error Handling

```python
from extract_design import (
    ExtractDesign,
    AuthenticationError,
    InsufficientCreditsError,
    RateLimitError,
    ValidationError,
    TimeoutError,
    ExtractionFailedError,
)

client = ExtractDesign(api_key="sk_live_...")

try:
    result = client.extract_and_wait(
        image_url="https://example.com/product.jpg"
    )
except AuthenticationError:
    print("Invalid API key")
except InsufficientCreditsError:
    print("Not enough credits")
except RateLimitError as e:
    print(f"Rate limited, retry after {e.retry_after} seconds")
except ValidationError as e:
    print(f"Invalid request: {e.error_message}")
except TimeoutError as e:
    print(f"Extraction {e.extraction_id} timed out")
except ExtractionFailedError as e:
    print(f"Extraction failed: {e.reason}")
```

## Context Manager

The client can be used as a context manager to ensure proper cleanup:

```python
with ExtractDesign(api_key="sk_live_...") as client:
    result = client.extract_and_wait(
        image_url="https://example.com/product.jpg"
    )
    print(result.extraction_url)
```

## Configuration

```python
client = ExtractDesign(
    api_key="sk_live_...",
    base_url="https://extract.design",  # Custom base URL
    timeout=60.0,  # Request timeout in seconds
)
```

## Requirements

- Python 3.10+
- httpx

## License

MIT License - see [LICENSE](LICENSE) for details.
