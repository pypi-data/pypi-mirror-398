"""Hub membership client."""

from __future__ import annotations

from typing import Any

from ..core.pagination import Page
from ..models import ProfileHub
from .base import AsyncBaseClient, BaseClient


class MembersClient(BaseClient):
    def list(
        self,
        hub: str,
        *,
        page: int = 1,
        per_page: int = 10,
        params: dict[str, Any] | None = None,
    ) -> Page[ProfileHub]:
        query: dict[str, Any] = {"page": page, "page_size": per_page}
        if params:
            query.update(params)
        data = self._request("GET", f"/api/hubs/{hub}/members", params=query)
        return _build_page(data)

    def add(self, hub: str, username: str) -> ProfileHub:
        data = self._request(
            "POST",
            f"/api/hubs/{hub}/member/add",
            json={"username": username},
        )
        return ProfileHub.model_validate(data)

    def remove(self, hub: str, username: str) -> None:
        self._request("DELETE", f"/api/hubs/{hub}/member/delete/{username}")

    def retrieve(self, hub: str, username: str) -> ProfileHub:
        data = self._request("GET", f"/api/hubs/{hub}/member/{username}")
        return ProfileHub.model_validate(data)

    def set_permission(self, hub: str, username: str, permission: str) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/hubs/{hub}/member/{username}/modify/permission",
            json={"permission": permission},
        )

    def bulk_modify(self, hub: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/hubs/{hub}/members/bulks/modify",
            json=payload,
        )

    def search(self, hub: str, params: dict[str, Any]) -> Page[ProfileHub]:
        data = self._request(
            "GET",
            f"/api/hubs/{hub}/members/search",
            params=params,
        )
        return _build_page(data)

    def filters(self, hub: str) -> dict[str, Any]:
        data = self._request("GET", f"/api/hubs/{hub}/members/filters")
        if not isinstance(data, dict):
            raise ValueError("Unexpected payload for member filters.")
        return data

    def update_profile(
        self,
        hub: str,
        username: str,
        payload: dict[str, Any],
    ) -> ProfileHub:
        files, data = _split_files(payload)
        response = self._request(
            "PUT",
            f"/api/hubs/{hub}/member/{username}/profile/update",
            json=None if files else payload,
            data=data if files else None,
            files=files if files else None,
        )
        return ProfileHub.model_validate(response)


class AsyncMembersClient(AsyncBaseClient):
    async def list(
        self,
        hub: str,
        *,
        page: int = 1,
        per_page: int = 10,
        params: dict[str, Any] | None = None,
    ) -> Page[ProfileHub]:
        query: dict[str, Any] = {"page": page, "page_size": per_page}
        if params:
            query.update(params)
        data = await self._request("GET", f"/api/hubs/{hub}/members", params=query)
        return _build_page(data)

    async def add(self, hub: str, username: str) -> ProfileHub:
        data = await self._request(
            "POST",
            f"/api/hubs/{hub}/member/add",
            json={"username": username},
        )
        return ProfileHub.model_validate(data)

    async def remove(self, hub: str, username: str) -> None:
        await self._request("DELETE", f"/api/hubs/{hub}/member/delete/{username}")

    async def retrieve(self, hub: str, username: str) -> ProfileHub:
        data = await self._request("GET", f"/api/hubs/{hub}/member/{username}")
        return ProfileHub.model_validate(data)

    async def set_permission(self, hub: str, username: str, permission: str) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/api/hubs/{hub}/member/{username}/modify/permission",
            json={"permission": permission},
        )

    async def bulk_modify(self, hub: str, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/api/hubs/{hub}/members/bulks/modify",
            json=payload,
        )

    async def search(self, hub: str, params: dict[str, Any]) -> Page[ProfileHub]:
        data = await self._request(
            "GET",
            f"/api/hubs/{hub}/members/search",
            params=params,
        )
        return _build_page(data)

    async def filters(self, hub: str) -> dict[str, Any]:
        data = await self._request("GET", f"/api/hubs/{hub}/members/filters")
        if not isinstance(data, dict):
            raise ValueError("Unexpected payload for member filters.")
        return data

    async def update_profile(
        self,
        hub: str,
        username: str,
        payload: dict[str, Any],
    ) -> ProfileHub:
        files, data = _split_files(payload)
        response = await self._request(
            "PUT",
            f"/api/hubs/{hub}/member/{username}/profile/update",
            json=None if files else payload,
            data=data if files else None,
            files=files if files else None,
        )
        return ProfileHub.model_validate(response)


def _build_page(data: Any) -> Page[ProfileHub]:
    if not isinstance(data, dict):
        raise ValueError("Expected dict payload for paginated response.")
    results_raw = data.get("results", [])
    if not isinstance(results_raw, list):
        raise ValueError("Expected list of results in paginated payload.")
    results = [ProfileHub.model_validate(item) for item in results_raw]
    return Page(
        count=data.get("count"),
        next=data.get("next"),
        previous=data.get("previous"),
        results=results,
    )


def _split_files(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    files: dict[str, Any] = {}
    data: dict[str, Any] = {}
    for key, value in payload.items():
        if _looks_like_file(value):
            files[key] = value
        else:
            data[key] = value
    return files, data


def _looks_like_file(value: Any) -> bool:
    if hasattr(value, "read"):
        return True
    if isinstance(value, tuple) and len(value) >= 2 and hasattr(value[1], "read"):
        return True
    return False
