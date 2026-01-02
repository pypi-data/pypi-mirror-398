"""Configuration helpers for constructing SDK clients."""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator, Mapping, MutableMapping

from .client import AsyncCodeanyClient, CodeanyClient


def load_env_file(path: str) -> None:
    """Populate ``os.environ`` with variables from a simple ``.env`` file."""

    try:
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())
    except FileNotFoundError:
        return


@dataclass(slots=True)
class ClientConfig:
    base_url: str
    auth: str = "simple_jwt"
    username: str | None = None
    password: str | None = None
    hub: str | None = None
    default_hub: str | None = None
    fetch_docs: bool = True
    timeout: float = 20.0
    retries: int = 0
    retry_backoff: float = 0.2

    def to_env(self, prefix: str = "CODEANY_") -> dict[str, str]:
        """Encode this config as environment variables."""

        env: dict[str, str] = {
            f"{prefix}BASE_URL": self.base_url,
            f"{prefix}AUTH": self.auth,
            f"{prefix}TIMEOUT": str(self.timeout),
            f"{prefix}FETCH_DOCS": "1" if self.fetch_docs else "0",
            f"{prefix}RETRIES": str(self.retries),
            f"{prefix}RETRY_BACKOFF": str(self.retry_backoff),
        }
        if self.username is not None:
            env[f"{prefix}USERNAME"] = self.username
        if self.password is not None:
            env[f"{prefix}PASSWORD"] = self.password
        if self.hub is not None:
            env[f"{prefix}HUB"] = self.hub
        if self.default_hub is not None:
            env[f"{prefix}DEFAULT_HUB"] = self.default_hub
        return env

    def create_sync_client(self, prefix: str = "CODEANY_") -> CodeanyClient:
        """Instantiate a :class:`CodeanyClient` based on this configuration."""

        with _env_overlay(self.to_env(prefix)):
            return CodeanyClient.from_env(prefix=prefix, timeout=self.timeout)

    async def create_async_client(self, prefix: str = "CODEANY_") -> AsyncCodeanyClient:
        """Instantiate an :class:`AsyncCodeanyClient` based on this configuration."""

        with _env_overlay(self.to_env(prefix)):
            return await AsyncCodeanyClient.from_env(prefix=prefix, timeout=self.timeout)


def load_env(prefix: str = "CODEANY_", *, env: Mapping[str, str] | None = None) -> ClientConfig:
    """Load :class:`ClientConfig` from environment variables."""

    source: Mapping[str, str] = env or os.environ
    base_url = _require(source, f"{prefix}BASE_URL")
    auth = source.get(f"{prefix}AUTH", "simple_jwt").strip().lower()

    username = source.get(f"{prefix}USERNAME")
    password = source.get(f"{prefix}PASSWORD")
    hub = source.get(f"{prefix}HUB")
    default_hub = source.get(f"{prefix}DEFAULT_HUB")
    timeout = _float(source.get(f"{prefix}TIMEOUT"), 20.0)
    fetch_docs = _bool(source.get(f"{prefix}FETCH_DOCS"), True)
    retries = _int(source.get(f"{prefix}RETRIES"), 0)
    retry_backoff = _float(source.get(f"{prefix}RETRY_BACKOFF"), 0.2)

    return ClientConfig(
        base_url=base_url,
        auth=auth,
        username=username,
        password=password,
        hub=hub,
        default_hub=default_hub,
        fetch_docs=fetch_docs,
        timeout=timeout,
        retries=retries,
        retry_backoff=retry_backoff,
    )


def apply_env(config: ClientConfig, *, prefix: str = "CODEANY_", env: MutableMapping[str, str] | None = None) -> None:
    """Apply config values into an environment mapping."""

    mapping = env if env is not None else os.environ
    mapping.update(config.to_env(prefix))


def _require(source: Mapping[str, str], key: str) -> str:
    value = source.get(key)
    if not value:
        raise ValueError(f"Missing required environment variable {key}")
    return value


def _bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Invalid integer value: {value!r}") from exc


def _float(value: str | None, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"Invalid float value: {value!r}") from exc


@contextmanager
def _env_overlay(values: Mapping[str, str]) -> Iterator[None]:
    originals: dict[str, str | None] = {}
    for key, value in values.items():
        originals[key] = os.environ.get(key)
        os.environ[key] = value
    try:
        yield
    finally:
        for key, original in originals.items():
            if original is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original
