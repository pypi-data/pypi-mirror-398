# indox-client

Python SDK for the Indox media and document conversion services.

## Installation

```bash
pip install indox-client
```

## Quick Start

```python
from indox_client import IndoxClient

# Initialize with API key
client = IndoxClient(api_key="your-api-key")

# Or use environment variables
# export INDOX_API_KEY=your-api-key
client = IndoxClient.from_env()

# Convert a document
result = client.docs.convert_file(
    file_path="document.pdf",
    target_formats=["docx", "txt"]
)

# Wait for completion
completed = client.docs.wait_for_completion(result["conversion_id"])

# Download the result
client.docs.download(
    conversion_id=result["conversion_id"],
    output_path="output.docx",
    fmt="docx"
)
```

## Features

- **Document Conversion**: Convert between PDF, DOCX, TXT, and more
- **Media Conversion**: Convert images and videos between formats
- **Async Support**: Long-polling for conversion status
- **Multiple Sources**: Upload files, URLs, or S3 keys

## Usage

### Document Conversion

```python
# From local file
result = client.docs.convert_file(
    file_path="input.pdf",
    target_formats=["docx"]
)

# From URL
result = client.docs.convert_url(
    file_url="https://example.com/document.pdf",
    target_formats=["docx"]
)

# Check supported formats
formats = client.docs.supported_conversions()
```

### Media Conversion

```python
# Convert image
result = client.media.convert_image(
    file_path="image.png",
    target_formats=["webp", "jpg"]
)

# Convert video
result = client.media.convert_video(
    file_path="video.mp4",
    target_formats=["webm"]
)

# Check supported formats
image_formats = client.media.image_formats()
video_formats = client.media.video_formats()
```

### Context Manager

```python
with IndoxClient.from_env() as client:
    result = client.docs.convert_file(
        file_path="document.pdf",
        target_formats=["docx"]
    )
```

## Configuration

| Environment Variable | Description |
|---------------------|-------------|
| `INDOX_API_KEY` | Your API key |
| `INDOX_DOCS_URL` | Docs service URL (default: https://docs.indox.org/) |
| `INDOX_MEDIA_URL` | Media service URL (default: https://docs.indox.org/) |

## Error Handling

```python
from indox_client import IndoxClient, IndoxHTTPError, IndoxClientError

try:
    result = client.docs.convert_file(
        file_path="document.pdf",
        target_formats=["docx"]
    )
except IndoxHTTPError as e:
    print(f"HTTP {e.status_code}: {e}")
    print(f"Request ID: {e.request_id}")
except IndoxClientError as e:
    print(f"Client error: {e}")
```

## License

Proprietary - see LICENSE for details. 
