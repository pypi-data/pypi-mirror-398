"""Submissions client with filter support."""

from __future__ import annotations

from typing import Any, AsyncIterator, Iterator

from ..core.pagination import Page, iter_pages
from ..filters import SubmissionsFilter
from ..models import SubmissionRow
from .base import AsyncBaseClient, BaseClient


class SubmissionsClient(BaseClient):
    def list(
        self,
        hub: str,
        *,
        competition_id: int | None = None,
        filter: SubmissionsFilter | dict[str, Any] | None = None,
    ) -> Page[SubmissionRow]:
        params = _resolve_filter(filter)
        path = (
            f"/api/hubs/{hub}/competition/{competition_id}/submissions/"
            if competition_id is not None
            else f"/api/hubs/{hub}/submissions/"
        )
        data = self._request("GET", path, params=params)
        return _build_page(data)

    def iter_all(
        self,
        hub: str,
        *,
        competition_id: int | None = None,
        filter: SubmissionsFilter | dict[str, Any] | None = None,
    ) -> Iterator[SubmissionRow]:
        def fetch(page: int) -> Page[SubmissionRow]:
            params = dict(_resolve_filter(filter) or {})
            params["page"] = page
            return self.list(
                hub,
                competition_id=competition_id,
                filter=params,
            )

        return iter_pages(fetch)


class AsyncSubmissionsClient(AsyncBaseClient):
    async def list(
        self,
        hub: str,
        *,
        competition_id: int | None = None,
        filter: SubmissionsFilter | dict[str, Any] | None = None,
    ) -> Page[SubmissionRow]:
        params = _resolve_filter(filter)
        path = (
            f"/api/hubs/{hub}/competition/{competition_id}/submissions/"
            if competition_id is not None
            else f"/api/hubs/{hub}/submissions/"
        )
        data = await self._request("GET", path, params=params)
        return _build_page(data)

    async def iter_all(
        self,
        hub: str,
        *,
        competition_id: int | None = None,
        filter: SubmissionsFilter | dict[str, Any] | None = None,
    ) -> AsyncIterator[SubmissionRow]:
        params = _resolve_filter(filter) or {}
        page_number = 1
        while True:
            page_params = dict(params)
            page_params["page"] = page_number
            page = await self.list(
                hub,
                competition_id=competition_id,
                filter=page_params,
            )
            for row in page.results:
                yield row
            if not page.next:
                break
            page_number += 1


def _resolve_filter(filter_obj: SubmissionsFilter | dict[str, Any] | None) -> dict[str, Any] | None:
    if filter_obj is None:
        return None
    if isinstance(filter_obj, SubmissionsFilter):
        return filter_obj.to_params()
    return filter_obj


def _build_page(data: Any) -> Page[SubmissionRow]:
    if not isinstance(data, dict):
        raise ValueError("Expected dict payload for submissions list.")
    results_raw = data.get("results", [])
    if not isinstance(results_raw, list):
        raise ValueError("Expected list of results.")
    results = [SubmissionRow.model_validate(item) for item in results_raw]
    return Page(
        count=data.get("count"),
        next=data.get("next"),
        previous=data.get("previous"),
        results=results,
    )
