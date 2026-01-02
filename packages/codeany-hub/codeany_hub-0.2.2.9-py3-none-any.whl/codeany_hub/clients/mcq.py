"""MCQ configuration client."""

from __future__ import annotations

from typing import Any

from ..models import MCConfig, MCPatch
from .base import AsyncBaseClient, BaseClient


class MCQClient(BaseClient):
    def get_config(self, hub: str, task_id: int) -> MCConfig:
        data = self._request("GET", f"/api/hubs/{hub}/task/{task_id}/mc")
        return MCConfig.model_validate(data)

    def replace_config(self, hub: str, task_id: int, config: MCConfig) -> MCConfig:
        data = self._request(
            "PUT",
            f"/api/hubs/{hub}/task/{task_id}/mc",
            json=config.model_dump(exclude_unset=True),
        )
        return MCConfig.model_validate(data)

    def patch_config(self, hub: str, task_id: int, patch: MCPatch) -> MCConfig:
        data = self._request(
            "PATCH",
            f"/api/hubs/{hub}/task/{task_id}/mc",
            json=patch.model_dump(exclude_unset=True),
        )
        return MCConfig.model_validate(data)

    def clear_config(self, hub: str, task_id: int) -> None:
        self._request("DELETE", f"/api/hubs/{hub}/task/{task_id}/mc")

    def update_option(
        self,
        hub: str,
        task_id: int,
        option_id: int | str,
        payload: dict[str, Any],
    ) -> MCConfig:
        data = self._request(
            "PATCH",
            f"/api/hubs/{hub}/task/{task_id}/mc/options/{option_id}",
            json=payload,
        )
        return MCConfig.model_validate(data)

    def delete_option(self, hub: str, task_id: int, option_id: int | str) -> None:
        self._request(
            "DELETE",
            f"/api/hubs/{hub}/task/{task_id}/mc/options/{option_id}",
        )

    def set_correct(self, hub: str, task_id: int, option_ids: list[int | str]) -> MCConfig:
        data = self._request(
            "PUT",
            f"/api/hubs/{hub}/task/{task_id}/mc/correct",
            json={"options": option_ids},
        )
        return MCConfig.model_validate(data)


class AsyncMCQClient(AsyncBaseClient):
    async def get_config(self, hub: str, task_id: int) -> MCConfig:
        data = await self._request("GET", f"/api/hubs/{hub}/task/{task_id}/mc")
        return MCConfig.model_validate(data)

    async def replace_config(self, hub: str, task_id: int, config: MCConfig) -> MCConfig:
        data = await self._request(
            "PUT",
            f"/api/hubs/{hub}/task/{task_id}/mc",
            json=config.model_dump(exclude_unset=True),
        )
        return MCConfig.model_validate(data)

    async def patch_config(self, hub: str, task_id: int, patch: MCPatch) -> MCConfig:
        data = await self._request(
            "PATCH",
            f"/api/hubs/{hub}/task/{task_id}/mc",
            json=patch.model_dump(exclude_unset=True),
        )
        return MCConfig.model_validate(data)

    async def clear_config(self, hub: str, task_id: int) -> None:
        await self._request("DELETE", f"/api/hubs/{hub}/task/{task_id}/mc")

    async def update_option(
        self,
        hub: str,
        task_id: int,
        option_id: int | str,
        payload: dict[str, Any],
    ) -> MCConfig:
        data = await self._request(
            "PATCH",
            f"/api/hubs/{hub}/task/{task_id}/mc/options/{option_id}",
            json=payload,
        )
        return MCConfig.model_validate(data)

    async def delete_option(self, hub: str, task_id: int, option_id: int | str) -> None:
        await self._request(
            "DELETE",
            f"/api/hubs/{hub}/task/{task_id}/mc/options/{option_id}",
        )

    async def set_correct(self, hub: str, task_id: int, option_ids: list[int | str]) -> MCConfig:
        data = await self._request(
            "PUT",
            f"/api/hubs/{hub}/task/{task_id}/mc/correct",
            json={"options": option_ids},
        )
        return MCConfig.model_validate(data)
