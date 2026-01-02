"""Top-level facades for the Codeany Hub SDK (sync & async)."""

from __future__ import annotations

import logging
import os
from typing import Iterable, Mapping, Sequence

import httpx

from .clients import (
    AsyncCompetitionsClient,
    AsyncHubsClient,
    AsyncImportsClient,
    AsyncJudgeClient,
    AsyncMCQClient,
    AsyncMembersClient,
    AsyncRatingsClient,
    AsyncSubmissionsClient,
    AsyncTasksClient,
    AsyncUsersClient,
    CompetitionsClient,
    HubsClient,
    ImportsClient,
    JudgeClient,
    MCQClient,
    MembersClient,
    RatingsClient,
    SubmissionsClient,
    TasksClient,
    UsersClient,
)
from .core import (
    AsyncTransport,
    AuthStrategy,
    CapabilityProbe,
    FileTokenStore,
    HubLoginAuth,
    InMemoryTokenStore,
    SimpleJwtAuth,
    TokenStore,
    Transport,
    TransportHooks,
    RetryPolicy,
)


class _EnvOverlay:
    def __init__(self, values: Mapping[str, str]) -> None:
        self._values = values
        self._originals: dict[str, str | None] = {}

    def __enter__(self) -> None:
        for key, value in self._values.items():
            self._originals[key] = os.environ.get(key)
            os.environ[key] = value

    def __exit__(self, exc_type, exc, tb) -> None:
        for key, original in self._originals.items():
            if original is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original


class CodeanyClient:
    """Primary entry point for interacting with the Codeany Hub APIs."""

    def __init__(
        self,
        base_url: str,
        *,
        auth: AuthStrategy | None = None,
        timeout: float = 20.0,
        default_hub: str | None = None,
        token_store: TokenStore | None = None,
        fetch_docs: bool = True,
        headers: Mapping[str, str] | None = None,
        hooks: TransportHooks | None = None,
        log_requests: bool = False,
        logger: logging.Logger | None = None,
        retry_policy: RetryPolicy | None = None,
        retries: int = 0,
        retry_statuses: Iterable[int] | None = None,
        retry_methods: Iterable[str] | None = None,
        retry_exceptions: Sequence[type[BaseException]] | None = None,
        retry_backoff: float = 0.2,
    ) -> None:
        if token_store and auth:
            auth.bind_store(token_store)

        self.transport = Transport(
            base_url,
            auth=auth,
            timeout=timeout,
            headers=headers,
            hooks=hooks,
            log_requests=log_requests,
            logger=logger,
            retry_policy=retry_policy,
            retries=retries,
            retry_statuses=retry_statuses,
            retry_methods=retry_methods,
            retry_exceptions=retry_exceptions,
            retry_backoff=retry_backoff,
        )
        self.token_store = token_store or (auth.get_store() if auth else None)
        self.users = UsersClient(self.transport)
        self.hubs = HubsClient(self.transport)
        self.members = MembersClient(self.transport)
        self.tasks = TasksClient(self.transport)
        self.mcq = MCQClient(self.transport)
        self.competitions = CompetitionsClient(self.transport)
        self.submissions = SubmissionsClient(self.transport)
        self.ratings = RatingsClient(self.transport)
        self.imports = ImportsClient(self.transport)
        self.judge = JudgeClient(self.transport)

        self.default_hub = default_hub
        self.capabilities: dict[str, bool] = {}
        if fetch_docs:
            self.capabilities = CapabilityProbe().probe(self.transport)

    def close(self) -> None:
        self.transport.close()

    def __enter__(self) -> "CodeanyClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
        return None

    def refresh_capabilities(self) -> dict[str, bool]:
        self.capabilities = CapabilityProbe().probe(self.transport)
        return self.capabilities

    @classmethod
    def with_simple_jwt(
        cls,
        base_url: str,
        username: str,
        password: str,
        *,
        timeout: float = 20.0,
        token_store: TokenStore | None = None,
        default_hub: str | None = None,
        fetch_docs: bool = True,
        headers: Mapping[str, str] | None = None,
        hooks: TransportHooks | None = None,
        log_requests: bool = False,
        logger: logging.Logger | None = None,
        retry_policy: RetryPolicy | None = None,
        retries: int = 0,
        retry_statuses: Iterable[int] | None = None,
        retry_methods: Iterable[str] | None = None,
        retry_exceptions: Sequence[type[BaseException]] | None = None,
        retry_backoff: float = 0.2,
    ) -> "CodeanyClient":
        store = token_store or InMemoryTokenStore()
        auth = SimpleJwtAuth(username, password, store=store)
        with httpx.Client(base_url=base_url, timeout=timeout) as client:
            auth.login(client)

        return cls(
            base_url,
            auth=auth,
            timeout=timeout,
            default_hub=default_hub,
            token_store=store,
            fetch_docs=fetch_docs,
            headers=headers,
            hooks=hooks,
            log_requests=log_requests,
            logger=logger,
            retry_policy=retry_policy,
            retries=retries,
            retry_statuses=retry_statuses,
            retry_methods=retry_methods,
            retry_exceptions=retry_exceptions,
            retry_backoff=retry_backoff,
        )

    @classmethod
    def with_hub_login(
        cls,
        base_url: str,
        hub: str,
        username: str,
        password: str,
        *,
        timeout: float = 20.0,
        token_store: TokenStore | None = None,
        default_hub: str | None = None,
        fetch_docs: bool = True,
        headers: Mapping[str, str] | None = None,
        hooks: TransportHooks | None = None,
        log_requests: bool = False,
        logger: logging.Logger | None = None,
        retry_policy: RetryPolicy | None = None,
        retries: int = 0,
        retry_statuses: Iterable[int] | None = None,
        retry_methods: Iterable[str] | None = None,
        retry_exceptions: Sequence[type[BaseException]] | None = None,
        retry_backoff: float = 0.2,
    ) -> "CodeanyClient":
        store = token_store or InMemoryTokenStore()
        auth = HubLoginAuth(hub, username, password, store=store)
        with httpx.Client(base_url=base_url, timeout=timeout) as client:
            auth.login(client)

        return cls(
            base_url,
            auth=auth,
            timeout=timeout,
            default_hub=default_hub or hub,
            token_store=store,
            fetch_docs=fetch_docs,
            headers=headers,
            hooks=hooks,
            log_requests=log_requests,
            logger=logger,
            retry_policy=retry_policy,
            retries=retries,
            retry_statuses=retry_statuses,
            retry_methods=retry_methods,
            retry_exceptions=retry_exceptions,
            retry_backoff=retry_backoff,
        )

    @classmethod
    def from_env(
        cls,
        *,
        prefix: str = "CODEANY_",
        timeout: float | None = None,
        fetch_docs: bool | None = None,
        headers: Mapping[str, str] | None = None,
        hooks: TransportHooks | None = None,
        log_requests: bool | None = None,
        logger: logging.Logger | None = None,
        env: Mapping[str, str] | None = None,
        retry_policy: RetryPolicy | None = None,
        retries: int | None = None,
        retry_statuses: Iterable[int] | None = None,
        retry_methods: Iterable[str] | None = None,
        retry_exceptions: Sequence[type[BaseException]] | None = None,
        retry_backoff: float | None = None,
    ) -> "CodeanyClient":
        overlay = None
        if env is not None:
            overlay = _EnvOverlay(env)
            overlay.__enter__()
        try:
            env_mapping = os.environ
            base_url = cls._require_env(prefix, "BASE_URL")
            strategy = env_mapping.get(f"{prefix}AUTH", "simple_jwt").strip().lower()
            default_hub = env_mapping.get(f"{prefix}DEFAULT_HUB")
            timeout_val = timeout if timeout is not None else cls._env_float(env_mapping.get(f"{prefix}TIMEOUT"), 20.0)
            fetch_docs_val = (
                fetch_docs
                if fetch_docs is not None
                else cls._env_bool(env_mapping.get(f"{prefix}FETCH_DOCS"), True)
            )
            log_requests_val = (
                log_requests
                if log_requests is not None
                else cls._env_bool(env_mapping.get(f"{prefix}LOG_REQUESTS"), False)
            )
            retries_val = retries if retries is not None else cls._env_int(env_mapping.get(f"{prefix}RETRIES"), 0)
            retry_backoff_val = (
                retry_backoff
                if retry_backoff is not None
                else cls._env_float(env_mapping.get(f"{prefix}RETRY_BACKOFF"), 0.2)
            )

            token_store: TokenStore | None = None
            token_path = env_mapping.get(f"{prefix}TOKEN_STORE_PATH")
            if token_path:
                token_store = FileTokenStore(token_path)

            if strategy in {"", "simple_jwt", "simple-jwt"}:
                username = cls._require_env(prefix, "USERNAME")
                password = cls._require_env(prefix, "PASSWORD")
                return cls.with_simple_jwt(
                    base_url,
                    username,
                    password,
                    timeout=timeout_val,
                    token_store=token_store,
                    default_hub=default_hub,
                    fetch_docs=fetch_docs_val,
                    headers=headers,
                    hooks=hooks,
                    log_requests=log_requests_val,
                    logger=logger,
                    retry_policy=retry_policy,
                    retries=retries_val,
                    retry_statuses=retry_statuses,
                    retry_methods=retry_methods,
                    retry_exceptions=retry_exceptions,
                    retry_backoff=retry_backoff_val,
                )

            if strategy in {"hub_login", "hub-login", "hub"}:
                hub = cls._require_env(prefix, "HUB")
                username = cls._require_env(prefix, "USERNAME")
                password = cls._require_env(prefix, "PASSWORD")
                return cls.with_hub_login(
                    base_url,
                    hub,
                    username,
                    password,
                    timeout=timeout_val,
                    token_store=token_store,
                    default_hub=default_hub or hub,
                    fetch_docs=fetch_docs_val,
                    headers=headers,
                    hooks=hooks,
                    log_requests=log_requests_val,
                    logger=logger,
                    retry_policy=retry_policy,
                    retries=retries_val,
                    retry_statuses=retry_statuses,
                    retry_methods=retry_methods,
                    retry_exceptions=retry_exceptions,
                    retry_backoff=retry_backoff_val,
                )

            if strategy in {"none", "unauthenticated"}:
                return cls(
                    base_url,
                    auth=None,
                    timeout=timeout_val,
                    default_hub=default_hub,
                    token_store=token_store,
                    fetch_docs=fetch_docs_val,
                    headers=headers,
                    hooks=hooks,
                    log_requests=log_requests_val,
                    logger=logger,
                    retry_policy=retry_policy,
                    retries=retries_val,
                    retry_statuses=retry_statuses,
                    retry_methods=retry_methods,
                    retry_exceptions=retry_exceptions,
                    retry_backoff=retry_backoff_val,
                )
        finally:
            if overlay:
                overlay.__exit__(None, None, None)

        raise ValueError(f"Unsupported CODEANY auth strategy: {strategy!r}")

    @staticmethod
    def _env_bool(value: str | None, default: bool) -> bool:
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _env_int(value: str | None, default: int) -> int:
        if value is None:
            return default
        try:
            return int(value)
        except ValueError as exc:  # pragma: no cover - defensive
            raise ValueError(f"Invalid integer value: {value!r}") from exc

    @staticmethod
    def _env_float(value: str | None, default: float) -> float:
        if value is None:
            return default
        try:
            return float(value)
        except ValueError as exc:  # pragma: no cover - defensive
            raise ValueError(f"Invalid float value: {value!r}") from exc

    @staticmethod
    def _require_env(prefix: str, key: str) -> str:
        value = os.environ.get(f"{prefix}{key}")
        if not value:
            raise ValueError(f"Missing required environment variable {prefix}{key}")
        return value


class AsyncCodeanyClient:
    """Async counterpart to :class:`CodeanyClient`."""

    def __init__(
        self,
        base_url: str,
        *,
        auth: AuthStrategy | None = None,
        timeout: float = 20.0,
        default_hub: str | None = None,
        token_store: TokenStore | None = None,
        headers: Mapping[str, str] | None = None,
        hooks: TransportHooks | None = None,
        async_hooks: TransportHooks | None = None,
        log_requests: bool = False,
        logger: logging.Logger | None = None,
        retry_policy: RetryPolicy | None = None,
        retries: int = 0,
        retry_statuses: Iterable[int] | None = None,
        retry_methods: Iterable[str] | None = None,
        retry_exceptions: Sequence[type[BaseException]] | None = None,
        retry_backoff: float = 0.2,
    ) -> None:
        if token_store and auth:
            auth.bind_store(token_store)

        self.transport = AsyncTransport(
            base_url,
            auth=auth,
            timeout=timeout,
            headers=headers,
            hooks=hooks,
            async_hooks=async_hooks,
            log_requests=log_requests,
            logger=logger,
            retry_policy=retry_policy,
            retries=retries,
            retry_statuses=retry_statuses,
            retry_methods=retry_methods,
            retry_exceptions=retry_exceptions,
            retry_backoff=retry_backoff,
        )
        self.token_store = token_store or (auth.get_store() if auth else None)
        self.users = AsyncUsersClient(self.transport)
        self.hubs = AsyncHubsClient(self.transport)
        self.members = AsyncMembersClient(self.transport)
        self.tasks = AsyncTasksClient(self.transport)
        self.mcq = AsyncMCQClient(self.transport)
        self.competitions = AsyncCompetitionsClient(self.transport)
        self.submissions = AsyncSubmissionsClient(self.transport)
        self.ratings = AsyncRatingsClient(self.transport)
        self.imports = AsyncImportsClient(self.transport)
        self.judge = AsyncJudgeClient(self.transport)

        self.default_hub = default_hub
        self.capabilities: dict[str, bool] = {}

    async def refresh_capabilities(self) -> dict[str, bool]:
        self.capabilities = await CapabilityProbe().async_probe(self.transport)
        return self.capabilities

    async def aclose(self) -> None:
        await self.transport.aclose()

    async def __aenter__(self) -> "AsyncCodeanyClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()
        return None

    close = aclose  # alias for symmetry with sync client

    @classmethod
    async def with_simple_jwt(
        cls,
        base_url: str,
        username: str,
        password: str,
        *,
        timeout: float = 20.0,
        token_store: TokenStore | None = None,
        default_hub: str | None = None,
        fetch_docs: bool = True,
        headers: Mapping[str, str] | None = None,
        hooks: TransportHooks | None = None,
        async_hooks: TransportHooks | None = None,
        log_requests: bool = False,
        logger: logging.Logger | None = None,
        retry_policy: RetryPolicy | None = None,
        retries: int = 0,
        retry_statuses: Iterable[int] | None = None,
        retry_methods: Iterable[str] | None = None,
        retry_exceptions: Sequence[type[BaseException]] | None = None,
        retry_backoff: float = 0.2,
    ) -> "AsyncCodeanyClient":
        store = token_store or InMemoryTokenStore()
        auth = SimpleJwtAuth(username, password, store=store)
        async with httpx.AsyncClient(base_url=base_url, timeout=timeout) as client:
            await auth.async_login(client)

        instance = cls(
            base_url,
            auth=auth,
            timeout=timeout,
            default_hub=default_hub,
            token_store=store,
            headers=headers,
            hooks=hooks,
            async_hooks=async_hooks,
            log_requests=log_requests,
            logger=logger,
            retry_policy=retry_policy,
            retries=retries,
            retry_statuses=retry_statuses,
            retry_methods=retry_methods,
            retry_exceptions=retry_exceptions,
            retry_backoff=retry_backoff,
        )
        if fetch_docs:
            await instance.refresh_capabilities()
        return instance

    @classmethod
    async def with_hub_login(
        cls,
        base_url: str,
        hub: str,
        username: str,
        password: str,
        *,
        timeout: float = 20.0,
        token_store: TokenStore | None = None,
        default_hub: str | None = None,
        fetch_docs: bool = True,
        headers: Mapping[str, str] | None = None,
        hooks: TransportHooks | None = None,
        async_hooks: TransportHooks | None = None,
        log_requests: bool = False,
        logger: logging.Logger | None = None,
        retry_policy: RetryPolicy | None = None,
        retries: int = 0,
        retry_statuses: Iterable[int] | None = None,
        retry_methods: Iterable[str] | None = None,
        retry_exceptions: Sequence[type[BaseException]] | None = None,
        retry_backoff: float = 0.2,
    ) -> "AsyncCodeanyClient":
        store = token_store or InMemoryTokenStore()
        auth = HubLoginAuth(hub, username, password, store=store)
        async with httpx.AsyncClient(base_url=base_url, timeout=timeout) as client:
            await auth.async_login(client)

        instance = cls(
            base_url,
            auth=auth,
            timeout=timeout,
            default_hub=default_hub or hub,
            token_store=store,
            headers=headers,
            hooks=hooks,
            async_hooks=async_hooks,
            log_requests=log_requests,
            logger=logger,
            retry_policy=retry_policy,
            retries=retries,
            retry_statuses=retry_statuses,
            retry_methods=retry_methods,
            retry_exceptions=retry_exceptions,
            retry_backoff=retry_backoff,
        )
        if fetch_docs:
            await instance.refresh_capabilities()
        return instance

    @classmethod
    async def from_env(
        cls,
        *,
        prefix: str = "CODEANY_",
        timeout: float | None = None,
        fetch_docs: bool | None = None,
        headers: Mapping[str, str] | None = None,
        hooks: TransportHooks | None = None,
        async_hooks: TransportHooks | None = None,
        log_requests: bool | None = None,
        logger: logging.Logger | None = None,
        env: Mapping[str, str] | None = None,
        retry_policy: RetryPolicy | None = None,
        retries: int | None = None,
        retry_statuses: Iterable[int] | None = None,
        retry_methods: Iterable[str] | None = None,
        retry_exceptions: Sequence[type[BaseException]] | None = None,
        retry_backoff: float | None = None,
    ) -> "AsyncCodeanyClient":
        overlay = None
        if env is not None:
            overlay = _EnvOverlay(env)
            overlay.__enter__()
        try:
            env_mapping = os.environ
            base_url = CodeanyClient._require_env(prefix, "BASE_URL")
            strategy = env_mapping.get(f"{prefix}AUTH", "simple_jwt").strip().lower()
            default_hub = env_mapping.get(f"{prefix}DEFAULT_HUB")
            timeout_val = timeout if timeout is not None else CodeanyClient._env_float(env_mapping.get(f"{prefix}TIMEOUT"), 20.0)
            fetch_docs_val = (
                fetch_docs
                if fetch_docs is not None
                else CodeanyClient._env_bool(env_mapping.get(f"{prefix}FETCH_DOCS"), True)
            )
            log_requests_val = (
                log_requests
                if log_requests is not None
                else CodeanyClient._env_bool(env_mapping.get(f"{prefix}LOG_REQUESTS"), False)
            )
            retries_val = retries if retries is not None else CodeanyClient._env_int(env_mapping.get(f"{prefix}RETRIES"), 0)
            retry_backoff_val = (
                retry_backoff
                if retry_backoff is not None
                else CodeanyClient._env_float(env_mapping.get(f"{prefix}RETRY_BACKOFF"), 0.2)
            )

            token_store: TokenStore | None = None
            token_path = env_mapping.get(f"{prefix}TOKEN_STORE_PATH")
            if token_path:
                token_store = FileTokenStore(token_path)

            if strategy in {"", "simple_jwt", "simple-jwt"}:
                username = CodeanyClient._require_env(prefix, "USERNAME")
                password = CodeanyClient._require_env(prefix, "PASSWORD")
                return await cls.with_simple_jwt(
                    base_url,
                    username,
                    password,
                    timeout=timeout_val,
                    token_store=token_store,
                    default_hub=default_hub,
                    fetch_docs=fetch_docs_val,
                    headers=headers,
                    hooks=hooks,
                    async_hooks=async_hooks,
                    log_requests=log_requests_val,
                    logger=logger,
                    retry_policy=retry_policy,
                    retries=retries_val,
                    retry_statuses=retry_statuses,
                    retry_methods=retry_methods,
                    retry_exceptions=retry_exceptions,
                    retry_backoff=retry_backoff_val,
                )

            if strategy in {"hub_login", "hub-login", "hub"}:
                hub = CodeanyClient._require_env(prefix, "HUB")
                username = CodeanyClient._require_env(prefix, "USERNAME")
                password = CodeanyClient._require_env(prefix, "PASSWORD")
                return await cls.with_hub_login(
                    base_url,
                    hub,
                    username,
                    password,
                    timeout=timeout_val,
                    token_store=token_store,
                    default_hub=default_hub or hub,
                    fetch_docs=fetch_docs_val,
                    headers=headers,
                    hooks=hooks,
                    async_hooks=async_hooks,
                    log_requests=log_requests_val,
                    logger=logger,
                    retry_policy=retry_policy,
                    retries=retries_val,
                    retry_statuses=retry_statuses,
                    retry_methods=retry_methods,
                    retry_exceptions=retry_exceptions,
                    retry_backoff=retry_backoff_val,
                )

            if strategy in {"none", "unauthenticated"}:
                instance = cls(
                    base_url,
                    auth=None,
                    timeout=timeout_val,
                    default_hub=default_hub,
                    token_store=token_store,
                    headers=headers,
                    hooks=hooks,
                    async_hooks=async_hooks,
                    log_requests=log_requests_val,
                    logger=logger,
                    retry_policy=retry_policy,
                    retries=retries_val,
                    retry_statuses=retry_statuses,
                    retry_methods=retry_methods,
                    retry_exceptions=retry_exceptions,
                    retry_backoff=retry_backoff_val,
                )
                if fetch_docs_val:
                    await instance.refresh_capabilities()
                return instance
        finally:
            if overlay:
                overlay.__exit__(None, None, None)

        raise ValueError(f"Unsupported CODEANY auth strategy: {strategy!r}")
