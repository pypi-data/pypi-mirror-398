"""Custom exception hierarchy used by the Indox client."""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping, Optional


class IndoxClientError(Exception):
    """Base class for all SDK errors."""

    def __init__(self, message: str, *, payload: Optional[Mapping[str, Any]] = None):
        super().__init__(message)
        self.payload = payload or {}


class IndoxHTTPError(IndoxClientError):
    """Raised when the remote service returns a non-success HTTP status."""

    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        payload: Optional[Mapping[str, Any]] = None,
        request_id: Optional[str] = None,
        url: Optional[str] = None,
    ):
        super().__init__(message, payload=payload)
        self.status_code = status_code
        self.request_id = request_id
        self.url = url

    def to_dict(self) -> MutableMapping[str, Any]:
        """Return a dict representation that is easy to log/serialize."""
        return {
            "status_code": self.status_code,
            "message": str(self),
            "request_id": self.request_id,
            "url": self.url,
            "payload": self.payload,
        }
