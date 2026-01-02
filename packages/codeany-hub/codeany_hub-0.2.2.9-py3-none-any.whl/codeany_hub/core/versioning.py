"""Capability probing for forward compatibility."""

from __future__ import annotations

from typing import Any

import httpx

from .errors import ApiError
from .transport import AsyncTransport, Transport

CAPABILITY_PATHS: dict[str, tuple[str, ...]] = {
    "hubs.members": ("/api/hubs/{hub}/members",),
    "competitions.base": (
        "/api/hubs/{hub}/competitions",
        "/api/hubs/{hub}/competition/{id}",
    ),
    "submissions.filters": (
        "/api/hubs/{hub}/submissions/",
        "/api/hubs/{hub}/competition/{id}/submissions/",
    ),
    "ratings.status": ("/api/hubs/{hub}/competition/{id}/rating-status",),
    "imports.cses": ("/api/hubs/{hub}/task/import/cses",),
    "judge.rejudge": ("/api/hubs/{hub}/submissions/{submission_id}/rejudge/",),
    "tasks.statements": (
        "/api/hubs/{hub}/task/{id}/statement",
        "/api/hubs/{hub}/task/{id}/statements/list",
    ),
    "tasks.editorial": ("/api/hubs/{hub}/task/{id}/editorial",),
    "tasks.io": ("/api/hubs/{hub}/task/{id}/io",),
    "mcq.config": ("/api/hubs/{hub}/task/{id}/mc",),
    "users.oauth": ("/api/hubs/{hub}/verify-oauth-token",),
}


class CapabilityProbe:
    """Inspect API surface to detect optional features."""

    def __init__(self, *, fallback: dict[str, bool] | None = None) -> None:
        self._fallback = fallback or {name: False for name in CAPABILITY_PATHS}

    def probe(self, transport: Transport) -> dict[str, bool]:
        try:
            payload = transport.request("GET", "/api/docs.json")
        except ApiError:
            return dict(self._fallback)
        except httpx.HTTPError:
            return dict(self._fallback)

        paths = _extract_paths(payload)
        capabilities = {"docs.available": bool(paths)}
        for capability, candidates in CAPABILITY_PATHS.items():
            capabilities[capability] = any(candidate in paths for candidate in candidates)
        return capabilities

    async def async_probe(self, transport: AsyncTransport) -> dict[str, bool]:
        try:
            payload = await transport.request("GET", "/api/docs.json")
        except ApiError:
            return dict(self._fallback)
        except httpx.HTTPError:
            return dict(self._fallback)

        paths = _extract_paths(payload)
        capabilities = {"docs.available": bool(paths)}
        for capability, candidates in CAPABILITY_PATHS.items():
            capabilities[capability] = any(candidate in paths for candidate in candidates)
        return capabilities


def _extract_paths(payload: Any) -> set[str]:
    if not isinstance(payload, dict):
        return set()
    paths = payload.get("paths")
    if isinstance(paths, dict):
        return set(paths)
    return set()
