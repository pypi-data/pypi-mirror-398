"""Unit tests for indox_client."""

import pytest
import responses
from indox_client import IndoxClient, IndoxClientError, IndoxHTTPError


class TestIndoxClient:
    """Test IndoxClient initialization."""

    def test_init_requires_api_key(self):
        with pytest.raises(ValueError, match="api_key is required"):
            IndoxClient(api_key="")

    def test_init_with_api_key(self):
        client = IndoxClient(api_key="test-key")
        assert client.docs.api_key == "test-key"
        assert client.media.api_key == "test-key"

    def test_context_manager(self):
        with IndoxClient(api_key="test-key") as client:
            assert client.docs is not None
            assert client.media is not None


class TestDocsClient:
    """Test DocsClient methods."""

    @responses.activate
    def test_supported_conversions(self):
        responses.add(
            responses.GET,
            "https://indox.org/docs/api/v1/docs/formats/",
            json={"formats": ["pdf", "docx"]},
            status=200,
        )
        client = IndoxClient(api_key="test-key")
        result = client.docs.supported_conversions()
        assert result["formats"] == ["pdf", "docx"]

    @responses.activate
    def test_convert_url(self):
        responses.add(
            responses.POST,
            "https://indox.org/docs/api/v1/docs/convert/json/",
            json={"conversion_id": "abc123", "status": "pending"},
            status=202,
        )
        client = IndoxClient(api_key="test-key")
        result = client.docs.convert_url(
            file_url="https://example.com/doc.pdf",
            target_formats=["docx"],
        )
        assert result["conversion_id"] == "abc123"

    def test_convert_url_requires_source(self):
        client = IndoxClient(api_key="test-key")
        with pytest.raises(IndoxClientError, match="Provide file_url or s3_key"):
            client.docs.convert_url(target_formats=["docx"])

    def test_convert_url_requires_formats(self):
        client = IndoxClient(api_key="test-key")
        with pytest.raises(IndoxClientError, match="target_formats is required"):
            client.docs.convert_url(file_url="https://example.com/doc.pdf", target_formats=[])


class TestMediaClient:
    """Test MediaClient methods."""

    @responses.activate
    def test_image_formats(self):
        responses.add(
            responses.GET,
            "https://indox.org/media/api/v1/image/formats/",
            json={"formats": ["png", "jpg", "webp"]},
            status=200,
        )
        client = IndoxClient(api_key="test-key")
        result = client.media.image_formats()
        assert "png" in result["formats"]

    @responses.activate
    def test_convert_image_from_url(self):
        responses.add(
            responses.POST,
            "https://indox.org/media/api/v1/image/convert/",
            json={"conversion_id": "img123", "status": "pending"},
            status=202,
        )
        client = IndoxClient(api_key="test-key")
        result = client.media.convert_image(
            file_url="https://example.com/image.png",
            target_formats=["webp"],
        )
        assert result["conversion_id"] == "img123"


class TestHTTPErrors:
    """Test error handling."""

    @responses.activate
    def test_http_error_raised(self):
        responses.add(
            responses.GET,
            "https://indox.org/docs/api/v1/docs/formats/",
            json={"detail": "Unauthorized"},
            status=401,
        )
        client = IndoxClient(api_key="bad-key")
        with pytest.raises(IndoxHTTPError) as exc_info:
            client.docs.supported_conversions()
        assert exc_info.value.status_code == 401

    @responses.activate
    def test_http_error_to_dict(self):
        responses.add(
            responses.GET,
            "https://indox.org/docs/api/v1/docs/formats/",
            json={"detail": "Not found"},
            status=404,
            headers={"X-Request-ID": "req-123"},
        )
        client = IndoxClient(api_key="test-key")
        with pytest.raises(IndoxHTTPError) as exc_info:
            client.docs.supported_conversions()
        error_dict = exc_info.value.to_dict()
        assert error_dict["status_code"] == 404
        assert error_dict["request_id"] == "req-123"
