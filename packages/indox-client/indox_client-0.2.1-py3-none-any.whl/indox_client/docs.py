"""Client for the Indox document conversion service."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional

from .base import BaseServiceClient
from .exceptions import IndoxClientError


class DocsClient(BaseServiceClient):
    """High-level wrapper around `/api/v1/docs/*` endpoints."""

    def supported_conversions(self) -> Mapping[str, Any]:
        """Return the formats/operations advertised by the service."""
        return self._get("/api/v1/docs/formats/")

    def convert_file(
        self,
        *,
        file_path: str | os.PathLike[str],
        target_formats: Iterable[str],
        destination: str = "aws",
        redirect_url: Optional[str] = None,
        engine: Optional[str] = None,
        options: Optional[Mapping[str, Any]] = None,
        s3_key: Optional[str] = None,
    ) -> Mapping[str, Any]:
        """Upload a local file for conversion."""
        formats = _clean_formats(target_formats)
        if not formats:
            raise IndoxClientError("target_formats is required")

        payload: Dict[str, Any] = {
            "target_formats": formats,
            "destination": destination,
        }
        if redirect_url:
            payload["redirect_url"] = redirect_url
        if engine:
            payload["engine"] = engine
        if s3_key:
            payload["s3_key"] = s3_key
        if options is not None:
            payload["options"] = json.dumps(options)

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(path)

        with path.open("rb") as fh:
            files = {"file": (path.name, fh)}
            return self._post_multipart("/api/v1/docs/convert/", data=payload, files=files)

    def convert_url(
        self,
        *,
        file_url: Optional[str] = None,
        s3_key: Optional[str] = None,
        target_formats: Iterable[str],
        destination: str = "aws",
        redirect_url: Optional[str] = None,
        engine: Optional[str] = None,
        options: Optional[Mapping[str, Any]] = None,
    ) -> Mapping[str, Any]:
        """Trigger a conversion for a remote file or S3 object."""
        formats = _clean_formats(target_formats)
        if not formats:
            raise IndoxClientError("target_formats is required")
        if not file_url and not s3_key:
            raise IndoxClientError("Provide file_url or s3_key")

        payload: Dict[str, Any] = {
            "target_formats": formats,
            "destination": destination,
        }
        if file_url:
            payload["url"] = file_url
        if s3_key:
            payload["s3_key"] = s3_key
        if redirect_url:
            payload["redirect_url"] = redirect_url
        if engine:
            payload["engine"] = engine
        if options is not None:
            payload["options"] = options

        return self._post_json("/api/v1/docs/convert/json/", payload)

    def get_conversion(self, conversion_id: str) -> Mapping[str, Any]:
        """Fetch metadata for a conversion or batch."""
        return self._get(f"/api/v1/conversion/{conversion_id}/")

    def wait_for_completion(
        self,
        conversion_id: str,
        *,
        timeout_seconds: float = 60.0,
        poll_interval: float = 0.5,
    ) -> Mapping[str, Any]:
        """Block until a conversion completes or the timeout elapses."""
        params = {"timeout": timeout_seconds, "interval": poll_interval}
        return self._get(f"/api/v1/conversion/wait/{conversion_id}/", params=params)

    def download(
        self,
        *,
        conversion_id: str,
        output_path: str | os.PathLike[str],
        fmt: Optional[str] = None,
    ) -> Path:
        """Download the converted artifact to disk."""
        params = {"format": fmt} if fmt else None
        response = self._request(
            "GET",
            f"/api/v1/docs/{conversion_id}/download/",
            params=params,
            stream=True,
            expected=(200,),
        )
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("wb") as fh:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    fh.write(chunk)
        return target


def _clean_formats(formats: Iterable[str]) -> list[str]:
    cleaned: list[str] = []
    for fmt in formats:
        token = (fmt or "").strip().lower().lstrip(".")
        if token:
            cleaned.append(token)
    return cleaned
