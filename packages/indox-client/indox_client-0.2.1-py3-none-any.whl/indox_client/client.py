"""Facade that exposes DocsClient and MediaClient under one object."""

from __future__ import annotations

import os
from typing import Optional

from .docs import DocsClient
from .media import MediaClient


DEFAULT_DOCS_BASE_URL = "https://indox.org/docs"
DEFAULT_MEDIA_BASE_URL = "https://indox.org/media"


class IndoxClient:
    """Convenience wrapper that bundles docs + media clients."""

    def __init__(
        self,
        *,
        api_key: str,
        docs_base_url: str = DEFAULT_DOCS_BASE_URL,
        media_base_url: str = DEFAULT_MEDIA_BASE_URL,
        timeout: Optional[tuple[float, float] | float] = None,
    ) -> None:
        docs_url = (docs_base_url or DEFAULT_DOCS_BASE_URL or "").strip().rstrip("/")
        media_url = (media_base_url or DEFAULT_MEDIA_BASE_URL or "").strip().rstrip("/")

        if not docs_url:
            raise ValueError("docs_base_url is required")
        if not media_url:
            raise ValueError("media_base_url is required")

        self.docs = DocsClient(base_url=docs_url, api_key=api_key, timeout=timeout)
        self.media = MediaClient(base_url=media_url, api_key=api_key, timeout=timeout)

    @classmethod
    def from_env(
        cls,
        *,
        api_key: Optional[str] = None,
        docs_base_url: Optional[str] = None,
        media_base_url: Optional[str] = None,
        timeout: Optional[tuple[float, float] | float] = None,
    ) -> "IndoxClient":
        """Instantiate the client using standard environment variables."""
        key = (api_key or os.getenv("INDOX_API_KEY") or "").strip()
        docs_url = (
            docs_base_url
            or os.getenv("INDOX_DOCS_URL")
            or DEFAULT_DOCS_BASE_URL
        ).strip()
        media_url = (
            media_base_url
            or os.getenv("INDOX_MEDIA_URL")
            or DEFAULT_MEDIA_BASE_URL
        ).strip()

        if not key:
            raise ValueError("api_key or INDOX_API_KEY is required")

        return cls(
            api_key=key,
            docs_base_url=docs_url,
            media_base_url=media_url,
            timeout=timeout,
        )

    def close(self) -> None:
        """Close the underlying HTTP sessions."""
        self.docs.close()
        self.media.close()

    def __enter__(self) -> "IndoxClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
