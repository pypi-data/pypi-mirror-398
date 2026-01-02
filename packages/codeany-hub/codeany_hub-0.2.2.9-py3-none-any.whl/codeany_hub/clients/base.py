"""Base client helpers."""

from __future__ import annotations

from typing import Any, Mapping

from ..core.transport import AsyncTransport, Transport


class BaseClient:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    @property
    def transport(self) -> Transport:
        return self._transport

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        data: Any | None = None,
        files: Any | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        return self._transport.request(
            method,
            path,
            params=params,
            json=json,
            data=data,
            files=files,
            headers=headers,
        )


class AsyncBaseClient:
    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    @property
    def transport(self) -> AsyncTransport:
        return self._transport

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        data: Any | None = None,
        files: Any | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        return await self._transport.request(
            method,
            path,
            params=params,
            json=json,
            data=data,
            files=files,
            headers=headers,
        )
