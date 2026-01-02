"""Ratings client with polling helpers."""

from __future__ import annotations

import asyncio
from typing import Any

from ..core.pagination import Page
from ..core.poller import Poller
from ..models import (
    CompetitionRatingOptions,
    CompetitionRatingSettings,
    RatingChange,
    RatingStatus,
)
from .base import AsyncBaseClient, BaseClient


class RatingsClient(BaseClient):
    def trigger(self, hub: str, competition_id: int) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/hubs/{hub}/competition/{competition_id}/rate",
        )

    def status(self, hub: str, competition_id: int) -> RatingStatus:
        data = self._request(
            "GET",
            f"/api/hubs/{hub}/competition/{competition_id}/rating-status",
        )
        return RatingStatus.model_validate(data)

    def update_options(
        self,
        hub: str,
        competition_id: int,
        partial: dict[str, Any],
    ) -> CompetitionRatingOptions:
        data = self._request(
            "PATCH",
            f"/api/hubs/{hub}/competition/{competition_id}/rating-options",
            json=partial,
        )
        return CompetitionRatingOptions.model_validate(data)

    def settings(self, hub: str, competition_id: int) -> CompetitionRatingSettings:
        data = self._request(
            "GET",
            f"/api/hubs/{hub}/competition/{competition_id}/rating-settings/",
        )
        return CompetitionRatingSettings.model_validate(data)

    def changes(
        self,
        hub: str,
        competition_id: int,
        params: dict[str, Any] | None = None,
    ) -> Page[RatingChange]:
        data = self._request(
            "GET",
            f"/api/hubs/{hub}/competition/{competition_id}/rating-changes",
            params=params,
        )
        return _build_page(data)

    def poll_status(
        self,
        hub: str,
        competition_id: int,
        *,
        interval_s: float = 1.5,
        timeout_s: float = 300.0,
    ) -> RatingStatus:
        poller = Poller()

        def tick() -> RatingStatus:
            return self.status(hub, competition_id)

        def is_done(status: RatingStatus) -> bool:
            return status.status in {"completed", "failed", "cancelled"}

        return poller.run(
            tick,
            is_done,
            interval_s=interval_s,
            timeout_s=timeout_s,
        )


class AsyncRatingsClient(AsyncBaseClient):
    async def trigger(self, hub: str, competition_id: int) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/api/hubs/{hub}/competition/{competition_id}/rate",
        )

    async def status(self, hub: str, competition_id: int) -> RatingStatus:
        data = await self._request(
            "GET",
            f"/api/hubs/{hub}/competition/{competition_id}/rating-status",
        )
        return RatingStatus.model_validate(data)

    async def update_options(
        self,
        hub: str,
        competition_id: int,
        partial: dict[str, Any],
    ) -> CompetitionRatingOptions:
        data = await self._request(
            "PATCH",
            f"/api/hubs/{hub}/competition/{competition_id}/rating-options",
            json=partial,
        )
        return CompetitionRatingOptions.model_validate(data)

    async def settings(self, hub: str, competition_id: int) -> CompetitionRatingSettings:
        data = await self._request(
            "GET",
            f"/api/hubs/{hub}/competition/{competition_id}/rating-settings/",
        )
        return CompetitionRatingSettings.model_validate(data)

    async def changes(
        self,
        hub: str,
        competition_id: int,
        params: dict[str, Any] | None = None,
    ) -> Page[RatingChange]:
        data = await self._request(
            "GET",
            f"/api/hubs/{hub}/competition/{competition_id}/rating-changes",
            params=params,
        )
        return _build_page(data)

    async def poll_status(
        self,
        hub: str,
        competition_id: int,
        *,
        interval_s: float = 1.5,
        timeout_s: float = 300.0,
    ) -> RatingStatus:
        loop = asyncio.get_running_loop()
        start = loop.time()
        while True:
            status = await self.status(hub, competition_id)
            if status.status in {"completed", "failed", "cancelled"}:
                return status
            if timeout_s is not None and (loop.time() - start) >= timeout_s:
                raise TimeoutError("Polling timed out.")
            await asyncio.sleep(interval_s)


def _build_page(data: Any) -> Page[RatingChange]:
    if not isinstance(data, dict):
        raise ValueError("Expected dict payload for rating changes.")
    results_raw = data.get("results", [])
    if not isinstance(results_raw, list):
        raise ValueError("Expected list of rating changes.")
    results = [RatingChange.model_validate(item) for item in results_raw]
    return Page(
        count=data.get("count"),
        next=data.get("next"),
        previous=data.get("previous"),
        results=results,
    )
