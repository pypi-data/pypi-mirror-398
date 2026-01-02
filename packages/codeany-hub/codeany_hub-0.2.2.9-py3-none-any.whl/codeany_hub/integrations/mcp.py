"""Helpers tailored for Model Context Protocol (MCP) integrations."""

from __future__ import annotations

from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass
from typing import Callable, Iterator, Mapping, MutableMapping
import os

from ..client import AsyncCodeanyClient, CodeanyClient
from ..config import ClientConfig, apply_env, load_env

ConsentPrompt = Callable[[str], bool]


class ConsentRejectedError(PermissionError):
    """Raised when a user rejects an MCP-triggered action."""


@dataclass(slots=True)
class MCPClientBuilder:
    """Factory that builds SDK clients after obtaining user consent."""

    prefix: str = "CODEANY_"

    def load_config(self, *, env: Mapping[str, str] | None = None) -> ClientConfig:
        return load_env(prefix=self.prefix, env=env)

    def ensure_consent(self, prompt: ConsentPrompt, *, message: str) -> None:
        approved = prompt(message)
        if not approved:
            raise ConsentRejectedError(message)

    @contextmanager
    def build_sync_client(
        self,
        prompt: ConsentPrompt,
        *,
        env: MutableMapping[str, str] | None = None,
        consent_message: str | None = None,
    ) -> Iterator[CodeanyClient]:
        """Context manager that returns a configured :class:`CodeanyClient`."""

        message = consent_message or "Allow Codeany Hub access from MCP tool?"
        self.ensure_consent(prompt, message=message)
        config = self.load_config(env=env)
        apply_env(config, prefix=self.prefix, env=os.environ)
        client = config.create_sync_client(prefix=self.prefix)
        try:
            yield client
        finally:
            client.close()

    @contextmanager
    def build_async_client(
        self,
        prompt: ConsentPrompt,
        *,
        env: MutableMapping[str, str] | None = None,
        consent_message: str | None = None,
    ) -> Iterator[AsyncCodeanyClient]:
        """Context manager that returns a configured :class:`AsyncCodeanyClient`."""

        message = consent_message or "Allow Codeany Hub access from MCP tool?"
        self.ensure_consent(prompt, message=message)
        config = self.load_config(env=env)
        apply_env(config, prefix=self.prefix, env=os.environ)
        client = _AsyncClientContext(config, prefix=self.prefix)
        with client as ctx:
            yield ctx


class _AsyncClientContext(AbstractContextManager[AsyncCodeanyClient]):
    def __init__(self, config: ClientConfig, *, prefix: str) -> None:
        self._config = config
        self._prefix = prefix
        self._client: AsyncCodeanyClient | None = None

    def __enter__(self) -> AsyncCodeanyClient:
        raise RuntimeError("Use 'async with' for async clients.")

    async def __aenter__(self) -> AsyncCodeanyClient:
        self._client = await self._config.create_async_client(prefix=self._prefix)
        return self._client

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._client:
            await self._client.aclose()
        self._client = None
