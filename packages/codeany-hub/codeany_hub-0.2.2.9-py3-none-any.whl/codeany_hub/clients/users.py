"""Authentication-related client."""

from __future__ import annotations

from typing import Any

from ..core.tokens import JwtPair
from .base import AsyncBaseClient, BaseClient


class UsersClient(BaseClient):
    def obtain_pair(self, username: str, password: str) -> JwtPair:
        payload = {"username": username, "password": password}
        data = self._request("POST", "/api/users/", json=payload)
        return _jwt_pair_from_data(data)

    def refresh(self, refresh_token: str) -> JwtPair:
        data = self._request("POST", "/api/users/refresh", json={"refresh": refresh_token})
        return _jwt_pair_from_data(data)

    def hub_login(self, hub: str, username: str, password: str) -> JwtPair:
        data = self._request(
            "POST",
            f"/api/hubs/{hub}/login",
            json={"username": username, "password": password},
        )
        return _jwt_pair_from_data(data)

    def hub_register(self, hub: str, payload: dict[str, Any]) -> dict[str, Any]:
        data = self._request("POST", f"/api/hubs/{hub}/register", json=payload)
        return data

    def verify_oauth_token(
        self,
        hub: str,
        oauth_token: str,
        *,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        request_json: dict[str, Any] = {"oauth_token": oauth_token}
        if extra:
            request_json["extra"] = extra
        data = self._request(
            "POST",
            f"/api/hubs/{hub}/verify-oauth-token",
            json=request_json,
        )
        return data


class AsyncUsersClient(AsyncBaseClient):
    async def obtain_pair(self, username: str, password: str) -> JwtPair:
        payload = {"username": username, "password": password}
        data = await self._request("POST", "/api/users/", json=payload)
        return _jwt_pair_from_data(data)

    async def refresh(self, refresh_token: str) -> JwtPair:
        data = await self._request("POST", "/api/users/refresh", json={"refresh": refresh_token})
        return _jwt_pair_from_data(data)

    async def hub_login(self, hub: str, username: str, password: str) -> JwtPair:
        data = await self._request(
            "POST",
            f"/api/hubs/{hub}/login",
            json={"username": username, "password": password},
        )
        return _jwt_pair_from_data(data)

    async def hub_register(self, hub: str, payload: dict[str, Any]) -> dict[str, Any]:
        data = await self._request("POST", f"/api/hubs/{hub}/register", json=payload)
        return data

    async def verify_oauth_token(
        self,
        hub: str,
        oauth_token: str,
        *,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        request_json: dict[str, Any] = {"oauth_token": oauth_token}
        if extra:
            request_json["extra"] = extra
        data = await self._request(
            "POST",
            f"/api/hubs/{hub}/verify-oauth-token",
            json=request_json,
        )
        return data


def _jwt_pair_from_data(data: Any) -> JwtPair:
    if not isinstance(data, dict):
        raise ValueError("Expected dict response for token pair.")
    access = data.get("access")
    refresh = data.get("refresh")
    if not isinstance(access, str):
        raise ValueError("Missing access token in response.")
    return JwtPair(access=access, refresh=refresh if isinstance(refresh, str) else None)
