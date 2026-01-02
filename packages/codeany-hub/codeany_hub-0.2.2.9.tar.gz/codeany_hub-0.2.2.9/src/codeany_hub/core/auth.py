"""Authentication strategies used by the Transport layer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import httpx

from .errors import raise_for_response
from .tokens import InMemoryTokenStore, JwtPair, TokenStore


class AuthStrategy(ABC):
    """Attach authentication headers and refresh tokens when necessary."""

    def __init__(self, store: TokenStore | None = None) -> None:
        self._store = store or InMemoryTokenStore()

    @abstractmethod
    def attach(self, headers: dict[str, str]) -> None:
        """Add authentication headers to the outgoing request."""

    @abstractmethod
    def try_refresh(self, client: httpx.Client) -> bool:
        """Attempt to refresh credentials after a 401 response."""

    def clear(self) -> None:
        """Forget stored credentials."""

        self._store.clear()

    def bind_store(self, store: TokenStore) -> None:
        """Replace the underlying token store."""

        self._store = store

    def get_store(self) -> TokenStore:
        return self._store

    def _token(self) -> JwtPair | None:
        return self._store.get()

    def _save(self, pair: JwtPair | None) -> None:
        self._store.set(pair)


class SimpleJwtAuth(AuthStrategy):
    """Authenticates via the `/api/users/` SimpleJWT endpoints."""

    def __init__(
        self,
        username: str,
        password: str,
        store: TokenStore | None = None,
    ) -> None:
        super().__init__(store)
        self._username = username
        self._password = password

    def attach(self, headers: dict[str, str]) -> None:
        pair = self._token()
        if pair:
            headers["Authorization"] = f"Bearer {pair.access}"

    def login(self, client: httpx.Client) -> JwtPair:
        response = client.post(
            "/api/users/",
            json={"username": self._username, "password": self._password},
        )
        if response.is_error:
            raise_for_response(response)
        data = response.json()
        pair = _parse_token_pair(data)
        self._save(pair)
        return pair

    async def async_login(self, client: httpx.AsyncClient) -> JwtPair:
        response = await client.post(
            "/api/users/",
            json={"username": self._username, "password": self._password},
        )
        if response.is_error:
            raise_for_response(response)
        data = response.json()
        pair = _parse_token_pair(data)
        self._save(pair)
        return pair

    def try_refresh(self, client: httpx.Client) -> bool:
        pair = self._token()
        if pair and pair.refresh:
            response = client.post("/api/users/refresh", json={"refresh": pair.refresh})
            if response.is_success:
                data = response.json()
                new_pair = _parse_token_pair(data)
                if not new_pair.refresh:
                    new_pair = JwtPair(access=new_pair.access, refresh=pair.refresh)
                self._save(new_pair)
                return True

        try:
            self.login(client)
        except Exception:
            return False
        return True

    async def async_try_refresh(self, client: httpx.AsyncClient) -> bool:
        pair = self._token()
        if pair and pair.refresh:
            response = await client.post(
                "/api/users/refresh",
                json={"refresh": pair.refresh},
            )
            if response.is_success:
                data = response.json()
                new_pair = _parse_token_pair(data)
                if not new_pair.refresh:
                    new_pair = JwtPair(access=new_pair.access, refresh=pair.refresh)
                self._save(new_pair)
                return True

        try:
            await self.async_login(client)
        except Exception:
            return False
        return True


class HubLoginAuth(AuthStrategy):
    """Per-hub login based on `/api/hubs/{hub}/login`."""

    def __init__(
        self,
        hub: str,
        username: str,
        password: str,
        store: TokenStore | None = None,
    ) -> None:
        super().__init__(store)
        self._hub = hub
        self._username = username
        self._password = password

    def attach(self, headers: dict[str, str]) -> None:
        pair = self._token()
        if pair:
            headers["Authorization"] = f"Bearer {pair.access}"

    def login(self, client: httpx.Client) -> JwtPair:
        response = client.post(
            f"/api/hubs/{self._hub}/login",
            json={"username": self._username, "password": self._password},
        )
        if response.is_error:
            raise_for_response(response)
        data = response.json()
        pair = _parse_token_pair(data)
        self._save(pair)
        return pair

    async def async_login(self, client: httpx.AsyncClient) -> JwtPair:
        response = await client.post(
            f"/api/hubs/{self._hub}/login",
            json={"username": self._username, "password": self._password},
        )
        if response.is_error:
            raise_for_response(response)
        data = response.json()
        pair = _parse_token_pair(data)
        self._save(pair)
        return pair

    def register(self, client: httpx.Client, payload: dict[str, Any]) -> dict[str, Any]:
        response = client.post(f"/api/hubs/{self._hub}/register", json=payload)
        if response.is_error:
            raise_for_response(response)
        data = response.json()
        pair = _parse_token_pair(data)
        if pair.access:
            self._save(pair)
        return data

    def try_refresh(self, client: httpx.Client) -> bool:
        pair = self._token()
        if pair and pair.refresh:
            response = client.post(
                "/api/users/refresh",
                json={"refresh": pair.refresh},
            )
            if response.is_success:
                new_pair = _parse_token_pair(response.json())
                if not new_pair.refresh:
                    new_pair = JwtPair(access=new_pair.access, refresh=pair.refresh)
                self._save(new_pair)
                return True

        try:
            self.login(client)
        except Exception:
            return False
        return True

    async def async_try_refresh(self, client: httpx.AsyncClient) -> bool:
        pair = self._token()
        if pair and pair.refresh:
            response = await client.post(
                "/api/users/refresh",
                json={"refresh": pair.refresh},
            )
            if response.is_success:
                new_pair = _parse_token_pair(response.json())
                if not new_pair.refresh:
                    new_pair = JwtPair(access=new_pair.access, refresh=pair.refresh)
                self._save(new_pair)
                return True

        try:
            await self.async_login(client)
        except Exception:
            return False
        return True


class OAuthBridge(AuthStrategy):
    """Completes hub OAuth verification flows."""

    def __init__(self, hub: str, store: TokenStore | None = None) -> None:
        super().__init__(store)
        self._hub = hub

    def attach(self, headers: dict[str, str]) -> None:
        pair = self._token()
        if pair:
            headers["Authorization"] = f"Bearer {pair.access}"

    def complete(
        self,
        client: httpx.Client,
        oauth_token: str,
        *,
        extra: dict[str, Any] | None = None,
    ) -> JwtPair:
        payload: dict[str, Any] = {"oauth_token": oauth_token}
        if extra:
            payload["extra"] = extra
        response = client.post(
            f"/api/hubs/{self._hub}/verify-oauth-token",
            json=payload,
        )
        if response.is_error:
            raise_for_response(response)
        pair = _parse_token_pair(response.json())
        self._save(pair)
        return pair

    async def async_complete(
        self,
        client: httpx.AsyncClient,
        oauth_token: str,
        *,
        extra: dict[str, Any] | None = None,
    ) -> JwtPair:
        payload: dict[str, Any] = {"oauth_token": oauth_token}
        if extra:
            payload["extra"] = extra
        response = await client.post(
            f"/api/hubs/{self._hub}/verify-oauth-token",
            json=payload,
        )
        if response.is_error:
            raise_for_response(response)
        pair = _parse_token_pair(response.json())
        self._save(pair)
        return pair

    def try_refresh(self, client: httpx.Client) -> bool:
        pair = self._token()
        if not pair or not pair.refresh:
            return False
        response = client.post("/api/users/refresh", json={"refresh": pair.refresh})
        if response.is_success:
            new_pair = _parse_token_pair(response.json())
            if not new_pair.refresh:
                new_pair = JwtPair(access=new_pair.access, refresh=pair.refresh)
            self._save(new_pair)
            return True
        return False

    async def async_try_refresh(self, client: httpx.AsyncClient) -> bool:
        pair = self._token()
        if not pair or not pair.refresh:
            return False
        response = await client.post("/api/users/refresh", json={"refresh": pair.refresh})
        if response.is_success:
            new_pair = _parse_token_pair(response.json())
            if not new_pair.refresh:
                new_pair = JwtPair(access=new_pair.access, refresh=pair.refresh)
            self._save(new_pair)
            return True
        return False


def _parse_token_pair(data: dict[str, Any]) -> JwtPair:
    access = data.get("access")
    if not isinstance(access, str):
        # Some hub-login endpoints return `token` instead of `access`; accept both.
        access = data.get("token")
    refresh = data.get("refresh")
    if not isinstance(access, str):
        raise ValueError("Response did not include an access token.")
    return JwtPair(access=access, refresh=refresh if isinstance(refresh, str) else None)
