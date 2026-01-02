"""Enumeration types exposed by the SDK."""

from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    """Small helper that behaves like ``str`` while providing Enum semantics."""

    def __str__(self) -> str:  # pragma: no cover - trivial repr helper
        return str(self.value)


class SubmissionVerdict(StrEnum):
    ACCEPTED = "AC"
    WRONG_ANSWER = "WA"
    TIME_LIMIT = "TLE"
    MEMORY_LIMIT = "MLE"
    RUNTIME_ERROR = "RTE"
    COMPILE_ERROR = "CE"
    PENDING = "PENDING"
    SKIPPED = "SKIPPED"
    HIDDEN = "HIDDEN"


class SubmissionOrdering(StrEnum):
    CREATED_ASC = "created_at"
    CREATED_DESC = "-created_at"
    SCORE_ASC = "score"
    SCORE_DESC = "-score"
    RUNTIME_ASC = "runtime_ms"
    RUNTIME_DESC = "-runtime_ms"


class CompetitionOrdering(StrEnum):
    STARTS_ASC = "starts_at"
    STARTS_DESC = "-starts_at"
    ENDS_ASC = "ends_at"
    ENDS_DESC = "-ends_at"
    CREATED_ASC = "created_at"
    CREATED_DESC = "-created_at"


class CompetitionStatus(StrEnum):
    DRAFT = "draft"
    UPCOMING = "upcoming"
    RUNNING = "running"
    FINISHED = "finished"
    ARCHIVED = "archived"


class RatingRunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskVisibility(StrEnum):
    PRIVATE = "private"
    PUBLIC = "public"
    HIDDEN = "hidden"
    DRAFT = "draft"


class TaskType(StrEnum):
    CLASSIC = "classic"
    INTERACTIVE = "interactive"
    OUTPUT_ONLY = "output-only"
    CODE_TASK = "code"
