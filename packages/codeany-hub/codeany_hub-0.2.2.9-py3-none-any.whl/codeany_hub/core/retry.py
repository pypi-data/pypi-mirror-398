"""Retry policy primitives for transports."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, Sequence

import httpx

DEFAULT_RETRY_STATUSES: tuple[int, ...] = (408, 425, 429, 500, 502, 503, 504)
DEFAULT_RETRY_METHODS: tuple[str, ...] = ("GET", "HEAD", "OPTIONS", "TRACE")
DEFAULT_RETRY_EXCEPTIONS: tuple[type[BaseException], ...] = (
    httpx.ConnectError,
    httpx.ReadError,
    httpx.WriteError,
    httpx.RemoteProtocolError,
    httpx.TimeoutException,
)


class RetryPolicy(ABC):
    """Strategy interface that decides when/how to retry failed requests."""

    @property
    @abstractmethod
    def max_attempts(self) -> int:
        """Total attempts permitted (initial request counts as attempt 1)."""

    @abstractmethod
    def get_retry_delay_for_response(
        self,
        method: str,
        attempt: int,
        response: httpx.Response,
    ) -> float | None:
        """Return delay (seconds) before retrying an HTTP response or ``None``."""

    @abstractmethod
    def get_retry_delay_for_error(
        self,
        method: str,
        attempt: int,
        exc: httpx.HTTPError,
    ) -> float | None:
        """Return delay (seconds) before retrying an exception or ``None``."""


@dataclass(slots=True)
class ExponentialBackoffRetry(RetryPolicy):
    """Simple exponential backoff retry policy."""

    retries: int = 0
    statuses: Sequence[int] = DEFAULT_RETRY_STATUSES
    methods: Iterable[str] = DEFAULT_RETRY_METHODS
    exceptions: Sequence[type[BaseException]] = DEFAULT_RETRY_EXCEPTIONS
    backoff_factor: float = 0.2

    def __post_init__(self) -> None:
        self._methods = {method.upper() for method in self.methods}

    @property
    def max_attempts(self) -> int:
        return max(1, int(self.retries) + 1)

    def get_retry_delay_for_response(
        self,
        method: str,
        attempt: int,
        response: httpx.Response,
    ) -> float | None:
        if attempt >= self.max_attempts:
            return None
        if response.status_code not in self.statuses:
            return None
        if method.upper() not in self._methods:
            return None
        return self._delay(attempt)

    def get_retry_delay_for_error(
        self,
        method: str,
        attempt: int,
        exc: httpx.HTTPError,
    ) -> float | None:
        if attempt >= self.max_attempts:
            return None
        if method.upper() not in self._methods:
            return None
        if not isinstance(exc, tuple(self.exceptions)):
            return None
        return self._delay(attempt)

    def _delay(self, attempt: int) -> float:
        if self.backoff_factor <= 0:
            return 0.0
        # attempt is 1-based; delay grows each retry.
        return self.backoff_factor * (2 ** (attempt - 1))
