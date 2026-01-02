"""Shared HTTP plumbing for DocsClient and MediaClient."""

from __future__ import annotations

import json
from typing import Any, Iterable, Mapping, MutableMapping, Optional

import requests

from .exceptions import IndoxClientError, IndoxHTTPError
from .version import __version__


DEFAULT_TIMEOUT = (5, 60)  # (connect, read)


class BaseServiceClient:
    """Convenience wrapper around `requests` with Indox defaults."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        timeout: Optional[tuple[float, float] | float] = None,
        session: Optional[requests.Session] = None,
    ) -> None:
        if not base_url:
            raise ValueError("base_url is required")
        if not api_key:
            raise ValueError("api_key is required")

        self.base_url = base_url.rstrip("/")
        self.api_key = api_key.strip()
        self.timeout = timeout or DEFAULT_TIMEOUT
        self._session = session or requests.Session()
        self._user_agent = f"indox-client/{__version__}"

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #
    def _build_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{self.base_url}{path}"

    def _headers(self, extra: Optional[Mapping[str, str]] = None) -> MutableMapping[str, str]:
        headers: MutableMapping[str, str] = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "User-Agent": self._user_agent,
        }
        if extra:
            headers.update({k: v for k, v in extra.items() if v is not None})
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json_body: Optional[Mapping[str, Any]] = None,
        data: Optional[Mapping[str, Any]] = None,
        files: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[tuple[float, float] | float] = None,
        expected: Iterable[int] = (200, 201, 202),
        stream: bool = False,
    ) -> Any:
        url = self._build_url(path)
        final_headers = self._headers(headers)

        try:
            response = self._session.request(
                method=method.upper(),
                url=url,
                params=params,
                json=json_body,
                data=data,
                files=files,
                headers=final_headers,
                timeout=timeout or self.timeout,
                stream=stream,
            )
        except requests.RequestException as exc:
            raise IndoxClientError(f"Request to {url} failed: {exc}") from exc

        if response.status_code not in expected:
            payload = _safe_json(response)
            request_id = response.headers.get("X-Request-ID")
            message = payload.get("detail") if isinstance(payload, dict) else response.text
            raise IndoxHTTPError(
                response.status_code,
                message or f"Unexpected status {response.status_code}",
                payload=payload if isinstance(payload, Mapping) else {"raw": response.text},
                request_id=request_id,
                url=url,
            )

        if stream:
            return response

        if not response.content:
            return {}

        return _safe_json(response)

    def close(self) -> None:
        self._session.close()

    # ------------------------------------------------------------------ #
    # Convenience wrappers for subclasses
    # ------------------------------------------------------------------ #
    def _post_json(self, path: str, payload: Mapping[str, Any], **kwargs) -> Any:
        return self._request("POST", path, json_body=payload, **kwargs)

    def _post_multipart(self, path: str, data: Mapping[str, Any], files: Mapping[str, Any], **kwargs) -> Any:
        return self._request("POST", path, data=data, files=files, **kwargs)

    def _get(self, path: str, params: Optional[Mapping[str, Any]] = None, **kwargs) -> Any:
        return self._request("GET", path, params=params, **kwargs)


def _safe_json(response: requests.Response) -> Any:
    try:
        return response.json()
    except json.JSONDecodeError:
        return {"raw": response.text}
