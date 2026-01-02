"""Client for the Indox media service (images + videos)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

from .base import BaseServiceClient
from .exceptions import IndoxClientError


class MediaClient(BaseServiceClient):
    """Wrapper around `/api/v1/image/*`, `/api/v1/video/*`, and download routes."""

    def image_formats(self) -> Mapping[str, Any]:
        """List supported image formats from `/api/v1/image/formats/`."""
        return self._get("/api/v1/image/formats/")

    def video_formats(self) -> Mapping[str, Any]:
        """List supported video formats from `/api/v1/video/formats/`."""
        return self._get("/api/v1/video/formats/")

    def image_operations(self) -> Mapping[str, Any]:
        """Fetch the advertised image operations for discovery."""
        return self._get("/api/v1/image/operations/")

    def video_operations(self) -> Mapping[str, Any]:
        """Fetch the advertised video operations for discovery."""
        return self._get("/api/v1/video/operations/")

    def convert_image(
        self,
        file_path: str | os.PathLike[str] | None = None,
        target_formats: Iterable[str] = (),
        *,
        file_url: Optional[str] = None,
        s3_key: Optional[str] = None,
        destination: str = "aws",
        redirect_url: Optional[str] = None,
        engine: Optional[str] = None,
        options: Optional[Mapping[str, Any]] = None,
    ) -> Mapping[str, Any]:
        """Start an image conversion job."""
        return self._convert_media(
            endpoint="/api/v1/image/convert/",
            file_path=file_path,
            file_url=file_url,
            s3_key=s3_key,
            target_formats=target_formats,
            destination=destination,
            redirect_url=redirect_url,
            engine=engine,
            options=options,
        )

    def convert_video(
        self,
        file_path: str | os.PathLike[str] | None = None,
        target_formats: Iterable[str] = (),
        *,
        file_url: Optional[str] = None,
        s3_key: Optional[str] = None,
        destination: str = "aws",
        redirect_url: Optional[str] = None,
        engine: Optional[str] = None,
        options: Optional[Mapping[str, Any]] = None,
    ) -> Mapping[str, Any]:
        """Start a video conversion job."""
        return self._convert_media(
            endpoint="/api/v1/video/convert/",
            file_path=file_path,
            file_url=file_url,
            s3_key=s3_key,
            target_formats=target_formats,
            destination=destination,
            redirect_url=redirect_url,
            engine=engine,
            options=options,
        )

    def get_image_conversion(self, conversion_id: str) -> Mapping[str, Any]:
        return self._get(f"/api/v1/image/conversion/{conversion_id}/")

    def get_video_conversion(self, conversion_id: str) -> Mapping[str, Any]:
        return self._get(f"/api/v1/video/conversion/{conversion_id}/")

    def wait_for_conversion(
        self,
        conversion_id: str,
        *,
        timeout_seconds: float = 60.0,
        poll_interval: float = 0.5,
    ) -> Mapping[str, Any]:
        params = {"timeout": timeout_seconds, "interval": poll_interval}
        return self._get(f"/api/v1/conversion/wait/{conversion_id}/", params=params)

    def download_media(
        self,
        *,
        conversion_id: str,
        output_path: str | os.PathLike[str],
        fmt: Optional[str] = None,
    ) -> Path:
        params = {"format": fmt} if fmt else None
        response = self._request(
            "GET",
            f"/api/v1/media/{conversion_id}/download/",
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

    def _convert_media(
        self,
        *,
        endpoint: str,
        file_path: str | os.PathLike[str] | None,
        file_url: Optional[str],
        s3_key: Optional[str],
        target_formats: Iterable[str],
        destination: str,
        redirect_url: Optional[str],
        engine: Optional[str],
        options: Optional[Mapping[str, Any]],
    ) -> Mapping[str, Any]:
        formats = _clean_formats(target_formats)
        if not formats:
            raise IndoxClientError("target_formats is required")

        payload: dict[str, Any] = {
            "target_formats": formats,
            "destination": destination,
        }
        if file_url:
            payload["file_url"] = file_url
        if s3_key:
            payload["s3_key"] = s3_key
        if redirect_url:
            payload["redirect_url"] = redirect_url
        if engine:
            payload["engine"] = engine
        if options is not None:
            payload["options"] = json.dumps(options) if file_path else options

        has_upload = file_path is not None
        if has_upload:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(path)
            with path.open("rb") as fh:
                files = {"file": (path.name, fh)}
                return self._post_multipart(endpoint, data=payload, files=files)

        if not file_url and not s3_key:
            raise IndoxClientError("Provide file_path, file_url, or s3_key")

        return self._post_json(endpoint, payload)


def _clean_formats(formats: Iterable[str]) -> list[str]:
    cleaned: list[str] = []
    for fmt in formats:
        token = (fmt or "").strip().lower().lstrip(".")
        if token:
            cleaned.append(token)
    return cleaned
