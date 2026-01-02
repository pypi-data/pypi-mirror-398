"""Generic polling helper for long-running operations."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

Status = TypeVar("Status")


class Poller:
    """Repeatedly invokes `tick` until `is_done` signals completion."""

    def __init__(self, *, sleep: Callable[[float], None] | None = None) -> None:
        self._sleep = sleep or time.sleep

    def run(
        self,
        tick: Callable[[], Status],
        is_done: Callable[[Status], bool],
        *,
        interval_s: float = 1.5,
        timeout_s: float = 120.0,
    ) -> Status:
        start = time.monotonic()
        while True:
            status = tick()
            if is_done(status):
                return status
            if timeout_s is not None and (time.monotonic() - start) >= timeout_s:
                raise TimeoutError("Polling timed out.")
            self._sleep(interval_s)
