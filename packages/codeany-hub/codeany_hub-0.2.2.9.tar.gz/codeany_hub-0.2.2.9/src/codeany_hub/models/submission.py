"""Submission models."""

from __future__ import annotations

from typing import Any

from .common import ISODateTime, TolerantModel
from .competition import Competition
from .hub import Hub, Profile
from .task import Task
from .enums import SubmissionVerdict


class SubmissionRow(TolerantModel):
    id: int
    hub: Hub | None = None
    competition: Competition | None = None
    task: Task | None = None
    author: Profile | None = None
    language: str | None = None
    verdict: str | None = None
    verdict_alias: str | None = None
    score: float | None = None
    runtime_ms: int | None = None
    memory_kb: int | None = None
    created_at: ISODateTime | None = None
    raw: dict[str, Any] | None = None

    @property
    def verdict_enum(self) -> SubmissionVerdict | None:
        return _to_verdict(self.verdict)

    @property
    def verdict_alias_enum(self) -> SubmissionVerdict | None:
        return _to_verdict(self.verdict_alias)


def _to_verdict(value: str | None) -> SubmissionVerdict | None:
    if value is None:
        return None
    try:
        return SubmissionVerdict(value)
    except ValueError:
        return None
