"""Task import client."""

from __future__ import annotations

import asyncio
from typing import Any

from ..core.poller import Poller
from .base import AsyncBaseClient, BaseClient


class ImportsClient(BaseClient):
    def start_cses(
        self,
        hub: str,
        *,
        cses_task_id: int,
        language: str = "en",
        points: int = 100,
        time_limit: int = 1000,
        memory_limit: int = 256,
    ) -> dict[str, Any]:
        payload = {
            "cses_task_id": cses_task_id,
            "language": language,
            "points": points,
            "time_limit": time_limit,
            "memory_limit": memory_limit,
        }
        return self._request(
            "POST",
            f"/api/hubs/{hub}/task/import/cses",
            json=payload,
        )

    def status(self, hub: str, celery_id: str) -> dict[str, Any]:
        return self._request(
            "GET",
            f"/api/hubs/{hub}/task/import/status/{celery_id}",
        )

    def poll(
        self,
        hub: str,
        celery_id: str,
        *,
        interval_s: float = 1.5,
        timeout_s: float = 600.0,
    ) -> dict[str, Any]:
        poller = Poller()

        def tick() -> dict[str, Any]:
            return self.status(hub, celery_id)

        def is_done(status: dict[str, Any]) -> bool:
            return bool(status.get("ready"))

        return poller.run(
            tick,
            is_done,
            interval_s=interval_s,
            timeout_s=timeout_s,
        )


class AsyncImportsClient(AsyncBaseClient):
    async def start_cses(
        self,
        hub: str,
        *,
        cses_task_id: int,
        language: str = "en",
        points: int = 100,
        time_limit: int = 1000,
        memory_limit: int = 256,
    ) -> dict[str, Any]:
        payload = {
            "cses_task_id": cses_task_id,
            "language": language,
            "points": points,
            "time_limit": time_limit,
            "memory_limit": memory_limit,
        }
        return await self._request(
            "POST",
            f"/api/hubs/{hub}/task/import/cses",
            json=payload,
        )

    async def status(self, hub: str, celery_id: str) -> dict[str, Any]:
        return await self._request(
            "GET",
            f"/api/hubs/{hub}/task/import/status/{celery_id}",
        )

    async def poll(
        self,
        hub: str,
        celery_id: str,
        *,
        interval_s: float = 1.5,
        timeout_s: float = 600.0,
    ) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        start = loop.time()
        while True:
            status = await self.status(hub, celery_id)
            if bool(status.get("ready")):
                return status
            if timeout_s is not None and (loop.time() - start) >= timeout_s:
                raise TimeoutError("Polling timed out.")
            await asyncio.sleep(interval_s)
