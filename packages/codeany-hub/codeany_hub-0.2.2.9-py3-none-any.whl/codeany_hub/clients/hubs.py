"""Hub and membership client."""

from __future__ import annotations

from typing import Any

from ..models import Hub
from .base import AsyncBaseClient, BaseClient


class HubsClient(BaseClient):
    def list_mine(self) -> list[Hub]:
        data = self._request("GET", "/api/hubs/list")
        if not isinstance(data, list):
            raise ValueError("Unexpected payload for hubs list.")
        return [Hub.model_validate(item) for item in data]

    def detail(self, hub: str) -> Hub:
        data = self._request("GET", f"/api/hubs/detail/{hub}")
        if not isinstance(data, dict):
            raise ValueError("Unexpected payload for hub detail.")
        return Hub.model_validate(data)

    def create(self, payload: dict[str, Any]) -> Hub:
        data = self._request("POST", "/api/hubs/add/", json=payload)
        if not isinstance(data, dict):
            raise ValueError("Unexpected payload for hub create.")
        return Hub.model_validate(data)

    def delete(self, hub: str) -> None:
        self._request("DELETE", "/api/hubs/delete", json={"hub": hub})


class AsyncHubsClient(AsyncBaseClient):
    async def list_mine(self) -> list[Hub]:
        data = await self._request("GET", "/api/hubs/list")
        if not isinstance(data, list):
            raise ValueError("Unexpected payload for hubs list.")
        return [Hub.model_validate(item) for item in data]

    async def detail(self, hub: str) -> Hub:
        data = await self._request("GET", f"/api/hubs/detail/{hub}")
        if not isinstance(data, dict):
            raise ValueError("Unexpected payload for hub detail.")
        return Hub.model_validate(data)

    async def create(self, payload: dict[str, Any]) -> Hub:
        data = await self._request("POST", "/api/hubs/add/", json=payload)
        if not isinstance(data, dict):
            raise ValueError("Unexpected payload for hub create.")
        return Hub.model_validate(data)

    async def delete(self, hub: str) -> None:
        await self._request("DELETE", "/api/hubs/delete", json={"hub": hub})
