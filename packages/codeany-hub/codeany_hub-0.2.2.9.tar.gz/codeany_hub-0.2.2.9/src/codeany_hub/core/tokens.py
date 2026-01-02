"""Token primitives and storage abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any
import json
import os


@dataclass(slots=True)
class JwtPair:
    """Access/refresh token pair returned by the Codeany Hub APIs."""

    access: str
    refresh: str | None = None


class TokenStore(ABC):
    """Interface for persisting authentication tokens."""

    @abstractmethod
    def get(self) -> JwtPair | None:
        """Return the cached tokens, if present."""

    @abstractmethod
    def set(self, pair: JwtPair | None) -> None:
        """Persist the provided token pair. ``None`` clears the storage."""

    def clear(self) -> None:
        """Clear stored tokens."""

        self.set(None)


class InMemoryTokenStore(TokenStore):
    """Volatile storage – tokens live only for the lifetime of the process."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._pair: JwtPair | None = None

    def get(self) -> JwtPair | None:
        with self._lock:
            return self._pair

    def set(self, pair: JwtPair | None) -> None:
        with self._lock:
            self._pair = pair


class FileTokenStore(TokenStore):
    """Simple JSON file store for token pairs."""

    def __init__(self, path: os.PathLike[str] | str, *, mode: int = 0o600) -> None:
        self._path = Path(path)
        self._mode = mode
        self._lock = RLock()

    def get(self) -> JwtPair | None:
        with self._lock:
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
            except FileNotFoundError:
                return None
            except json.JSONDecodeError:
                return None

        access = data.get("access")
        refresh = data.get("refresh")
        if isinstance(access, str):
            return JwtPair(access=access, refresh=refresh if isinstance(refresh, str) else None)
        return None

    def set(self, pair: JwtPair | None) -> None:
        with self._lock:
            if pair is None:
                try:
                    self._path.unlink()
                except FileNotFoundError:
                    return
                except OSError:
                    return
                return

            self._path.parent.mkdir(parents=True, exist_ok=True)
            payload: dict[str, Any] = {"access": pair.access}
            if pair.refresh:
                payload["refresh"] = pair.refresh
            self._path.write_text(json.dumps(payload), encoding="utf-8")
            try:
                os.chmod(self._path, self._mode)
            except PermissionError:
                pass
