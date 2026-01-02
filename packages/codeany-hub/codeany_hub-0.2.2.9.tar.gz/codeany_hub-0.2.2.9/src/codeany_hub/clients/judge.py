"""Judge-related endpoints."""

from __future__ import annotations

from typing import Any

from .base import AsyncBaseClient, BaseClient


class JudgeClient(BaseClient):
    def rejudge(self, hub: str, submission_id: int) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/hubs/{hub}/submissions/{submission_id}/rejudge/",
        )


class AsyncJudgeClient(AsyncBaseClient):
    async def rejudge(self, hub: str, submission_id: int) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/api/hubs/{hub}/submissions/{submission_id}/rejudge/",
        )
