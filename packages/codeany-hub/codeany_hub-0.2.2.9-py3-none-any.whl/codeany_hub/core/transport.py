"""HTTP transports shared by all resource clients (sync + async)."""

from __future__ import annotations

import asyncio
import inspect
import logging
import time
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable, Iterable, Iterator, Mapping, Sequence

import httpx

from .auth import AuthStrategy
from .errors import raise_for_response
from .retry import (
    DEFAULT_RETRY_EXCEPTIONS,
    DEFAULT_RETRY_METHODS,
    DEFAULT_RETRY_STATUSES,
    ExponentialBackoffRetry,
    RetryPolicy,
)


DEFAULT_HEADERS: Mapping[str, str] = {
    "Accept": "application/json",
    "User-Agent": "codeany-hub-sdk/0.2.0",
}

LOGGER = logging.getLogger("codeany_hub.transport")


@dataclass(slots=True)
class RequestContext:
    """Shape passed to request hooks and logging."""

    method: str
    path: str
    params: Mapping[str, Any] | None
    json: Any | None
    data: Any | None
    files: Any | None
    headers: Mapping[str, str]
    attempt: int
    max_attempts: int


@dataclass(slots=True)
class ResponseContext:
    """Shape passed to response hooks and logging."""

    request: RequestContext
    response: httpx.Response
    duration: float
    attempt: int


@dataclass(slots=True)
class TransportHooks:
    """Container for request/response hook callables."""

    on_request: Sequence[Callable[[RequestContext], Any]] = ()
    on_response: Sequence[Callable[[ResponseContext], Any]] = ()


class Transport(AbstractContextManager["Transport"]):
    """Small wrapper around :class:`httpx.Client` with auth, retries, and hooks."""

    def __init__(
        self,
        base_url: str,
        *,
        auth: AuthStrategy | None = None,
        timeout: float | httpx.Timeout = 20.0,
        headers: Mapping[str, str] | None = None,
        client_factory: Callable[..., httpx.Client] = httpx.Client,
        hooks: TransportHooks | None = None,
        logger: logging.Logger | None = None,
        log_requests: bool = False,
        retry_policy: RetryPolicy | None = None,
        retries: int = 0,
        retry_statuses: Iterable[int] | None = None,
        retry_methods: Iterable[str] | None = None,
        retry_exceptions: Sequence[type[BaseException]] | None = None,
        retry_backoff: float = 0.2,
    ) -> None:
        self._auth = auth
        self._default_headers = dict(DEFAULT_HEADERS)
        if headers:
            self._default_headers.update(headers)
        self._client = client_factory(base_url=base_url, timeout=timeout)

        self._hooks = hooks or TransportHooks()
        self._logger = logger or LOGGER
        self._log_requests = log_requests
        self._policy = retry_policy or ExponentialBackoffRetry(
            retries=max(0, int(retries)),
            statuses=tuple(retry_statuses or DEFAULT_RETRY_STATUSES),
            methods=tuple(retry_methods or DEFAULT_RETRY_METHODS),
            exceptions=tuple(retry_exceptions or DEFAULT_RETRY_EXCEPTIONS),
            backoff_factor=max(0.0, float(retry_backoff)),
        )

    @property
    def base_url(self) -> str:
        return str(self._client.base_url)

    @property
    def auth(self) -> AuthStrategy | None:
        return self._auth

    def with_auth(self, auth: AuthStrategy | None) -> None:
        self._auth = auth

    def request(
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
        """Perform an HTTP request and return JSON-decoded data when available."""

        max_attempts = self._policy.max_attempts
        attempt = 1

        while True:
            combined_headers = dict(self._default_headers)
            if headers:
                combined_headers.update(headers)
            if self._auth:
                self._auth.attach(combined_headers)

            request_ctx = RequestContext(
                method=method,
                path=path,
                params=params,
                json=json,
                data=data,
                files=files,
                headers=combined_headers,
                attempt=attempt,
                max_attempts=max_attempts,
            )
            self._emit_request(request_ctx)

            start = time.perf_counter()
            try:
                response = self._client.request(
                    method,
                    path,
                    params=params,
                    json=json,
                    data=data,
                    files=files,
                    headers=combined_headers,
                )
            except httpx.HTTPError as exc:
                duration = time.perf_counter() - start
                self._emit_transport_error(request_ctx, duration, exc)
                delay = self._policy.get_retry_delay_for_error(method, attempt, exc)
                if delay is None:
                    raise
                self._sleep(delay)
                attempt += 1
                if attempt > max_attempts:
                    raise
                continue

            duration = time.perf_counter() - start
            response_ctx = ResponseContext(
                request=request_ctx,
                response=response,
                duration=duration,
                attempt=attempt,
            )
            self._emit_response(response_ctx)

            if response.status_code == 401 and self._auth:
                if not self._auth.try_refresh(self._client):
                    try:
                        raise_for_response(response)
                    finally:
                        response.close()
                else:
                    if attempt >= max_attempts:
                        try:
                            raise_for_response(response)
                        finally:
                            response.close()
                    response.close()
                    attempt += 1
                continue

            delay = None
            if response.is_error:
                delay = self._policy.get_retry_delay_for_response(method, attempt, response)
            if delay is not None:
                if attempt >= max_attempts:
                    try:
                        raise_for_response(response)
                    finally:
                        response.close()
                response.close()
                self._sleep(delay)
                attempt += 1
                continue

            if response.is_error:
                try:
                    raise_for_response(response)
                finally:
                    response.close()

            if response.status_code == 204:
                response.close()
                return None
            result = _decode_response(response)
            response.close()
            return result

    def stream(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        data: Any | None = None,
        files: Any | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Iterator[str]:
        """Stream textual response data from an HTTP endpoint."""

        def _iter() -> Iterator[str]:
            attempt = 1
            max_attempts = self._policy.max_attempts

            while True:
                combined_headers = dict(self._default_headers)
                if headers:
                    combined_headers.update(headers)
                if self._auth:
                    self._auth.attach(combined_headers)

                request_ctx = RequestContext(
                    method=method,
                    path=path,
                    params=params,
                    json=json,
                    data=data,
                    files=files,
                    headers=combined_headers,
                    attempt=attempt,
                    max_attempts=max_attempts,
                )
                self._emit_request(request_ctx)

                prepared_files = files() if callable(files) else files

                start = time.perf_counter()
                try:
                    stream_ctx = self._client.stream(
                        method,
                        path,
                        params=params,
                        json=json,
                        data=data,
                        files=prepared_files,
                        headers=combined_headers,
                    )
                    response = stream_ctx.__enter__()
                except httpx.HTTPError as exc:
                    duration = time.perf_counter() - start
                    self._emit_transport_error(request_ctx, duration, exc)
                    delay = self._policy.get_retry_delay_for_error(method, attempt, exc)
                    if delay is None or attempt >= max_attempts:
                        raise
                    self._sleep(delay)
                    attempt += 1
                    continue

                try:
                    duration = time.perf_counter() - start
                    response_ctx = ResponseContext(
                        request=request_ctx,
                        response=response,
                        duration=duration,
                        attempt=attempt,
                    )
                    self._emit_response(response_ctx)

                    if response.status_code == 401 and self._auth:
                        if not self._auth.try_refresh(self._client):
                            raise_for_response(response)
                        if attempt >= max_attempts:
                            raise_for_response(response)
                        attempt += 1
                        continue

                    delay = None
                    if response.is_error:
                        delay = self._policy.get_retry_delay_for_response(method, attempt, response)
                    if delay is not None:
                        if attempt >= max_attempts:
                            raise_for_response(response)
                        self._sleep(delay)
                        attempt += 1
                        continue

                    if response.is_error:
                        raise_for_response(response)

                    for chunk in response.iter_text():
                        if chunk:
                            yield chunk
                    return
                finally:
                    stream_ctx.__exit__(None, None, None)

        return _iter()

    def _emit_request(self, ctx: RequestContext) -> None:
        if self._log_requests:
            self._logger.info(
                "%s %s (attempt %d/%d)",
                ctx.method,
                ctx.path,
                ctx.attempt,
                ctx.max_attempts,
            )
        for handler in self._hooks.on_request:
            result = handler(ctx)
            if inspect.isawaitable(result):
                raise RuntimeError(
                    "Synchronous transport hooks must not be awaitable; use async_hooks for async handlers."
                )

    def _emit_response(self, ctx: ResponseContext) -> None:
        if self._log_requests:
            self._logger.info(
                "%s %s -> %s in %.3fs",
                ctx.request.method,
                ctx.request.path,
                ctx.response.status_code,
                ctx.duration,
            )
        for handler in self._hooks.on_response:
            result = handler(ctx)
            if inspect.isawaitable(result):
                raise RuntimeError(
                    "Synchronous transport hooks must not be awaitable; use async_hooks for async handlers."
                )

    def _emit_transport_error(
        self,
        ctx: RequestContext,
        duration: float,
        exc: httpx.HTTPError,
    ) -> None:
        if self._log_requests:
            self._logger.warning(
                "%s %s transport error after %.3fs: %s",
                ctx.method,
                ctx.path,
                duration,
                exc,
            )

    def _sleep(self, delay: float) -> None:
        if delay <= 0:
            return
        time.sleep(delay)

    def close(self) -> None:
        self._client.close()

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - trivial
        self.close()
        return None


class AsyncTransport(AbstractAsyncContextManager["AsyncTransport"]):
    """Async counterpart to :class:`Transport` using :class:`httpx.AsyncClient`."""

    def __init__(
        self,
        base_url: str,
        *,
        auth: AuthStrategy | None = None,
        timeout: float | httpx.Timeout = 20.0,
        headers: Mapping[str, str] | None = None,
        client_factory: Callable[..., httpx.AsyncClient] = httpx.AsyncClient,
        hooks: TransportHooks | None = None,
        async_hooks: TransportHooks | None = None,
        logger: logging.Logger | None = None,
        log_requests: bool = False,
        retry_policy: RetryPolicy | None = None,
        retries: int = 0,
        retry_statuses: Iterable[int] | None = None,
        retry_methods: Iterable[str] | None = None,
        retry_exceptions: Sequence[type[BaseException]] | None = None,
        retry_backoff: float = 0.2,
    ) -> None:
        self._auth = auth
        self._default_headers = dict(DEFAULT_HEADERS)
        if headers:
            self._default_headers.update(headers)
        self._client = client_factory(base_url=base_url, timeout=timeout)

        self._hooks = hooks or TransportHooks()
        self._async_hooks = async_hooks or TransportHooks()
        self._logger = logger or LOGGER
        self._log_requests = log_requests
        self._policy = retry_policy or ExponentialBackoffRetry(
            retries=max(0, int(retries)),
            statuses=tuple(retry_statuses or DEFAULT_RETRY_STATUSES),
            methods=tuple(retry_methods or DEFAULT_RETRY_METHODS),
            exceptions=tuple(retry_exceptions or DEFAULT_RETRY_EXCEPTIONS),
            backoff_factor=max(0.0, float(retry_backoff)),
        )

    @property
    def base_url(self) -> str:
        return str(self._client.base_url)

    @property
    def auth(self) -> AuthStrategy | None:
        return self._auth

    def with_auth(self, auth: AuthStrategy | None) -> None:
        self._auth = auth

    async def request(
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
        max_attempts = self._policy.max_attempts
        attempt = 1

        while True:
            combined_headers = dict(self._default_headers)
            if headers:
                combined_headers.update(headers)
            if self._auth:
                self._auth.attach(combined_headers)

            request_ctx = RequestContext(
                method=method,
                path=path,
                params=params,
                json=json,
                data=data,
                files=files,
                headers=combined_headers,
                attempt=attempt,
                max_attempts=max_attempts,
            )
            self._emit_request(request_ctx)
            await self._emit_async_request(request_ctx)

            start = time.perf_counter()
            try:
                response = await self._client.request(
                    method,
                    path,
                    params=params,
                    json=json,
                    data=data,
                    files=files,
                    headers=combined_headers,
                )
            except httpx.HTTPError as exc:
                duration = time.perf_counter() - start
                self._emit_transport_error(request_ctx, duration, exc)
                delay = self._policy.get_retry_delay_for_error(method, attempt, exc)
                if delay is None:
                    raise
                await self._sleep(delay)
                attempt += 1
                if attempt > max_attempts:
                    raise
                continue

            duration = time.perf_counter() - start
            response_ctx = ResponseContext(
                request=request_ctx,
                response=response,
                duration=duration,
                attempt=attempt,
            )
            self._emit_response(response_ctx)
            await self._emit_async_response(response_ctx)

            if response.status_code == 401 and self._auth:
                async_refresh = getattr(self._auth, "async_try_refresh", None)
                if not callable(async_refresh):
                    try:
                        raise_for_response(response)
                    finally:
                        await response.aclose()
                refreshed = await async_refresh(self._client)
                if not refreshed:
                    try:
                        raise_for_response(response)
                    finally:
                        await response.aclose()
                if attempt >= max_attempts:
                    try:
                        raise_for_response(response)
                    finally:
                        await response.aclose()
                await response.aclose()
                attempt += 1
                continue

            delay = None
            if response.is_error:
                delay = self._policy.get_retry_delay_for_response(method, attempt, response)
            if delay is not None:
                if attempt >= max_attempts:
                    try:
                        raise_for_response(response)
                    finally:
                        await response.aclose()
                await response.aclose()
                await self._sleep(delay)
                attempt += 1
                continue

            if response.is_error:
                try:
                    raise_for_response(response)
                finally:
                    await response.aclose()

            if response.status_code == 204:
                await response.aclose()
                return None
            result = _decode_response(response)
            await response.aclose()
            return result

    async def stream(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        data: Any | None = None,
        files: Any | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> AsyncIterator[str]:
        """Stream textual response data from an HTTP endpoint asynchronously."""

        async def _aiter() -> AsyncIterator[str]:
            attempt = 1
            max_attempts = self._policy.max_attempts

            while True:
                combined_headers = dict(self._default_headers)
                if headers:
                    combined_headers.update(headers)
                if self._auth:
                    self._auth.attach(combined_headers)

                request_ctx = RequestContext(
                    method=method,
                    path=path,
                    params=params,
                    json=json,
                    data=data,
                    files=files,
                    headers=combined_headers,
                    attempt=attempt,
                    max_attempts=max_attempts,
                )
                self._emit_request(request_ctx)
                await self._emit_async_request(request_ctx)

                prepared_files = files() if callable(files) else files

                start = time.perf_counter()
                try:
                    stream_ctx = self._client.stream(
                        method,
                        path,
                        params=params,
                        json=json,
                        data=data,
                        files=prepared_files,
                        headers=combined_headers,
                    )
                    response = await stream_ctx.__aenter__()
                except httpx.HTTPError as exc:
                    duration = time.perf_counter() - start
                    self._emit_transport_error(request_ctx, duration, exc)
                    delay = self._policy.get_retry_delay_for_error(method, attempt, exc)
                    if delay is None or attempt >= max_attempts:
                        raise
                    await self._sleep(delay)
                    attempt += 1
                    continue

                try:
                    duration = time.perf_counter() - start
                    response_ctx = ResponseContext(
                        request=request_ctx,
                        response=response,
                        duration=duration,
                        attempt=attempt,
                    )
                    self._emit_response(response_ctx)
                    await self._emit_async_response(response_ctx)

                    if response.status_code == 401 and self._auth:
                        async_refresh = getattr(self._auth, "async_try_refresh", None)
                        refreshed = False
                        if callable(async_refresh):
                            refreshed = await async_refresh(self._client)
                        else:
                            refreshed = self._auth.try_refresh(self._client)
                        if not refreshed or attempt >= max_attempts:
                            raise_for_response(response)
                        attempt += 1
                        continue

                    delay = None
                    if response.is_error:
                        delay = self._policy.get_retry_delay_for_response(method, attempt, response)
                    if delay is not None:
                        if attempt >= max_attempts:
                            raise_for_response(response)
                        await self._sleep(delay)
                        attempt += 1
                        continue

                    if response.is_error:
                        raise_for_response(response)

                    async for chunk in response.aiter_text():
                        if chunk:
                            yield chunk
                    return
                finally:
                    await stream_ctx.__aexit__(None, None, None)

        return _aiter()

    def _emit_request(self, ctx: RequestContext) -> None:
        if self._log_requests:
            self._logger.info(
                "%s %s (attempt %d/%d)",
                ctx.method,
                ctx.path,
                ctx.attempt,
                ctx.max_attempts,
            )
        for handler in self._hooks.on_request:
            result = handler(ctx)
            if inspect.isawaitable(result):
                raise RuntimeError(
                    "Synchronous transport hooks must not be awaitable; use async_hooks for async handlers."
                )

    def _emit_response(self, ctx: ResponseContext) -> None:
        if self._log_requests:
            self._logger.info(
                "%s %s -> %s in %.3fs",
                ctx.request.method,
                ctx.request.path,
                ctx.response.status_code,
                ctx.duration,
            )
        for handler in self._hooks.on_response:
            result = handler(ctx)
            if inspect.isawaitable(result):
                raise RuntimeError(
                    "Synchronous transport hooks must not be awaitable; use async_hooks for async handlers."
                )

    def _emit_transport_error(
        self,
        ctx: RequestContext,
        duration: float,
        exc: httpx.HTTPError,
    ) -> None:
        if self._log_requests:
            self._logger.warning(
                "%s %s transport error after %.3fs: %s",
                ctx.method,
                ctx.path,
                duration,
                exc,
            )

    async def _emit_async_request(self, ctx: RequestContext) -> None:
        for handler in self._async_hooks.on_request:
            result = handler(ctx)
            if inspect.isawaitable(result):
                await result

    async def _emit_async_response(self, ctx: ResponseContext) -> None:
        for handler in self._async_hooks.on_response:
            result = handler(ctx)
            if inspect.isawaitable(result):
                await result

    async def _sleep(self, delay: float) -> None:
        if delay <= 0:
            return
        await asyncio.sleep(delay)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncTransport":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - trivial
        await self.aclose()
        return None


def _decode_response(response: httpx.Response) -> Any:
    if response.headers.get("Content-Type", "").startswith("application/json"):
        try:
            return response.json()
        except ValueError:
            return response.text
    return response.content
