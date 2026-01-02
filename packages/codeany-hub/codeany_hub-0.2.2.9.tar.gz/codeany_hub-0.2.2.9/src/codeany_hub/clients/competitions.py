"""Competitions client."""

from __future__ import annotations

from typing import Any

from ..core.pagination import Page
from ..filters import CompetitionsFilter
from ..models import Competition, CompetitionListItem, Task
from .base import AsyncBaseClient, BaseClient


class CompetitionsClient(BaseClient):
    def list(
        self,
        hub: str,
        *,
        filter: CompetitionsFilter | dict[str, Any] | None = None,
    ) -> Page[CompetitionListItem]:
        params = _resolve_filter(filter)
        data = self._request("GET", f"/api/hubs/{hub}/competitions", params=params)
        return _build_page(data, CompetitionListItem)

    def create(self, hub: str, payload: dict[str, Any]) -> Competition:
        data = self._request("POST", f"/api/hubs/{hub}/competition/add/", json=payload)
        return Competition.model_validate(data)

    def detail(self, hub: str, competition_id: int) -> Competition:
        data = self._request(
            "GET",
            f"/api/hubs/{hub}/competition/{competition_id}",
        )
        return Competition.model_validate(data)

    def update(self, hub: str, competition_id: int, payload: dict[str, Any]) -> Competition:
        data = self._request(
            "PUT",
            f"/api/hubs/{hub}/competition/{competition_id}/update",
            json=payload,
        )
        return Competition.model_validate(data)

    def delete(self, hub: str, competition_id: int) -> None:
        self._request("DELETE", f"/api/hubs/{hub}/competition/{competition_id}/delete")

    def languages(self, hub: str, competition_id: int) -> list[str]:
        data = self._request(
            "GET",
            f"/api/hubs/{hub}/competition/{competition_id}/languages",
        )
        if not isinstance(data, list):
            raise ValueError("Expected list of languages.")
        return [str(item) for item in data]

    def tasks(self, hub: str, competition_id: int) -> list[Task]:
        data = self._request(
            "GET",
            f"/api/hubs/{hub}/competition/{competition_id}/tasks",
        )
        if not isinstance(data, list):
            raise ValueError("Expected list of tasks.")
        return [Task.model_validate(item) for item in data]

    def update_tasks(
        self,
        hub: str,
        competition_id: int,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/hubs/{hub}/competition/{competition_id}/tasks/update",
            json=payload,
        )

    def leaderboard(
        self,
        hub: str,
        competition_id: int,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            f"/api/hubs/{hub}/competition/{competition_id}/leaderboard",
            params=params,
        )


class AsyncCompetitionsClient(AsyncBaseClient):
    async def list(
        self,
        hub: str,
        *,
        filter: CompetitionsFilter | dict[str, Any] | None = None,
    ) -> Page[CompetitionListItem]:
        params = _resolve_filter(filter)
        data = await self._request("GET", f"/api/hubs/{hub}/competitions", params=params)
        return _build_page(data, CompetitionListItem)

    async def create(self, hub: str, payload: dict[str, Any]) -> Competition:
        data = await self._request("POST", f"/api/hubs/{hub}/competition/add/", json=payload)
        return Competition.model_validate(data)

    async def detail(self, hub: str, competition_id: int) -> Competition:
        data = await self._request(
            "GET",
            f"/api/hubs/{hub}/competition/{competition_id}",
        )
        return Competition.model_validate(data)

    async def update(self, hub: str, competition_id: int, payload: dict[str, Any]) -> Competition:
        data = await self._request(
            "PUT",
            f"/api/hubs/{hub}/competition/{competition_id}/update",
            json=payload,
        )
        return Competition.model_validate(data)

    async def delete(self, hub: str, competition_id: int) -> None:
        await self._request("DELETE", f"/api/hubs/{hub}/competition/{competition_id}/delete")

    async def languages(self, hub: str, competition_id: int) -> list[str]:
        data = await self._request(
            "GET",
            f"/api/hubs/{hub}/competition/{competition_id}/languages",
        )
        if not isinstance(data, list):
            raise ValueError("Expected list of languages.")
        return [str(item) for item in data]

    async def tasks(self, hub: str, competition_id: int) -> list[Task]:
        data = await self._request(
            "GET",
            f"/api/hubs/{hub}/competition/{competition_id}/tasks",
        )
        if not isinstance(data, list):
            raise ValueError("Expected list of tasks.")
        return [Task.model_validate(item) for item in data]

    async def update_tasks(
        self,
        hub: str,
        competition_id: int,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/api/hubs/{hub}/competition/{competition_id}/tasks/update",
            json=payload,
        )

    async def leaderboard(
        self,
        hub: str,
        competition_id: int,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await self._request(
            "GET",
            f"/api/hubs/{hub}/competition/{competition_id}/leaderboard",
            params=params,
        )


def _resolve_filter(filter_obj: CompetitionsFilter | dict[str, Any] | None) -> dict[str, Any] | None:
    if filter_obj is None:
        return None
    if isinstance(filter_obj, CompetitionsFilter):
        return filter_obj.to_params()
    return filter_obj


def _build_page(data: Any, model_cls):
    if not isinstance(data, dict):
        raise ValueError("Expected dict payload for paginated response.")
    results_raw = data.get("results", [])
    if not isinstance(results_raw, list):
        raise ValueError("Expected list of results.")
    results = [model_cls.model_validate(item) for item in results_raw]
    return Page(
        count=data.get("count"),
        next=data.get("next"),
        previous=data.get("previous"),
        results=results,
    )
