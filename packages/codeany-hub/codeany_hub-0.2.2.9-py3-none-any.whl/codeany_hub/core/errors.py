"""Error hierarchy and factories for Codeany Hub API responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, NoReturn

import httpx


@dataclass
class ApiError(Exception):
    """Base exception raised for HTTP errors."""

    status: int
    message: str
    payload: Any | None = None
    response: httpx.Response | None = None

    def __str__(self) -> str:  # pragma: no cover - simple repr helper
        return f"{self.status}: {self.message}"


class AuthError(ApiError):
    """Raised for authentication and authorization failures."""


class NotFoundError(ApiError):
    """Raised when a resource is not found (HTTP 404)."""


class RateLimitError(ApiError):
    """Raised when the API throttles the request (HTTP 429)."""


class ValidationError(ApiError):
    """Raised when submitted data fails validation (HTTP 400/422)."""


def raise_for_response(response: httpx.Response) -> NoReturn:
    """Raise an appropriate :class:`ApiError` for the given response."""

    status = response.status_code
    payload: Any | None = None
    message = response.reason_phrase or f"HTTP {status}"

    try:
        payload = response.json()
    except ValueError:
        payload = response.text or None

    if isinstance(payload, dict):
        message = _derive_message(payload, default=message)

    error_cls = _map_status_to_error(status)
    raise error_cls(status=status, message=message, payload=payload, response=response)


def _derive_message(payload: dict[str, Any], *, default: str) -> str:
    """Try common Django/DRF error shapes and fall back to a readable default."""

    if "detail" in payload and isinstance(payload["detail"], str):
        return payload["detail"]
    if "error" in payload:
        err = payload["error"]
        if isinstance(err, str):
            return err
        if isinstance(err, dict) and "message" in err and isinstance(err["message"], str):
            return err["message"]
    if "message" in payload and isinstance(payload["message"], str):
        return payload["message"]
    if "non_field_errors" in payload and isinstance(payload["non_field_errors"], list):
        combined = "; ".join(str(item) for item in payload["non_field_errors"])
        if combined:
            return combined
    return default


def _map_status_to_error(status: int) -> type[ApiError]:
    if status in (401, 403):
        return AuthError
    if status == 404:
        return NotFoundError
    if status == 429:
        return RateLimitError
    if status in (400, 422):
        return ValidationError
    return ApiError
