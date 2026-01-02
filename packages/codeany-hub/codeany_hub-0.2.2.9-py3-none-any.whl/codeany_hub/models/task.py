"""Task-related models."""

from __future__ import annotations

from typing import Any, Mapping

from pydantic import Field, field_validator

from .common import ISODateTime, TolerantModel
from .enums import TaskType, TaskVisibility
from .hub import Hub


class TestSet(TolerantModel):
    id: int | None = None
    name: str | None = None
    public: bool | None = None
    sample_count: int | None = None
    total_tests: int | None = None


class TaskLimits(TolerantModel):
    """Time and memory constraints for a task."""

    time_limit: int
    memory_limit: int


class TaskStatementAsset(TolerantModel):
    name: str | None = None
    url: str | None = None
    size_bytes: int | None = Field(default=None, alias="size")
    checksum: str | None = None
    content_type: str | None = None


class TaskStatementSummary(TolerantModel):
    id: int
    language: str
    title: str | None = None
    is_default: bool | None = None
    updated_at: ISODateTime | None = None


class TaskStatement(TolerantModel):
    id: int | None = None
    language: str | None = None
    title: str | None = None
    body: str | None = None
    rendered: str | None = None
    is_default: bool | None = None
    is_public: bool | None = None
    updated_at: ISODateTime | None = None
    assets: list[TaskStatementAsset] | None = None
    metadata: dict[str, Any] | None = None


class TaskStatementListEntry(TolerantModel):
    """Condensed statement metadata used by the new task statements endpoints."""

    id: int
    name: str
    title: dict[str, str] | None = None


class TaskStatements(TolerantModel):
    """Full multilingual task statement payload."""

    id: int
    name: str
    title: dict[str, Any] | None = None
    statements: dict[str, Any] | None = None
    input_format: dict[str, Any] | None = None
    output_format: dict[str, Any] | None = None
    notes: dict[str, Any] | None = None
    scores_format: dict[str, Any] | None = None
    allowed_languages_effective: list[str] | None = None
    allowed_languages_labels: list[str] | None = None
    templates_by_language: dict[str, Any] | None = None


class TaskEditorial(TolerantModel):
    id: int | None = None
    title: str | None = None
    body: str | None = None
    rendered: str | None = None
    updated_at: ISODateTime | None = None
    metadata: dict[str, Any] | None = None


class TaskIO(TolerantModel):
    input: str | None = None
    output: str | None = None
    checker: str | None = None
    attachments: list[TaskStatementAsset] | None = None
    metadata: dict[str, Any] | None = None


class TaskExamples(TolerantModel):
    example_inputs: list[str] | None = None
    example_outputs: list[str] | None = None


class TestSetShort(TolerantModel):
    """Short serializer returned by the testset list and mutation endpoints."""

    id: int
    index: int | None = None
    test_count: int | None = None
    score: int | None = None
    test_score: str | None = None
    links: list[Any] | None = None


class TestSetDetail(TolerantModel):
    """Detailed serializer for a single testset."""

    id: int
    index: int | None = None
    name: str | None = None
    tests: list[Any] | None = None
    test_count: int | None = None
    score: int | None = None
    test_score: str | None = None
    links: list[Any] | None = None
    metadata: dict[str, Any] | None = None


class TestCase(TolerantModel):
    input: str | None = None
    output: str | None = None


class TestSetUploadEvent(TolerantModel):
    status: str | None = None
    message: str | None = None


class Task(TolerantModel):
    id: int
    hub: Hub | None = None
    name: str
    slug: str | None = None
    type: str | None = None
    visibility: str | None = None
    created_at: ISODateTime | None = None
    updated_at: ISODateTime | None = None
    points: float | None = None
    time_limit_ms: int | None = None
    memory_limit_mb: int | None = None
    test_sets: list[TestSet] | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("hub", mode="before")
    @classmethod
    def _coerce_hub(cls, value: Any) -> Hub | Mapping[str, Any] | None:
        if value is None or isinstance(value, Hub):
            return value
        if isinstance(value, str):
            return Hub(slug=value)
        if isinstance(value, Mapping):
            return value
        return value

    @property
    def visibility_enum(self) -> TaskVisibility | None:
        return _to_visibility(self.visibility)

    @property
    def type_enum(self) -> TaskType | None:
        return _to_task_type(self.type)


def _to_visibility(value: str | None) -> TaskVisibility | None:
    if value is None:
        return None
    try:
        return TaskVisibility(value)
    except ValueError:
        return None


def _to_task_type(value: str | None) -> TaskType | None:
    if value is None:
        return None
    try:
        return TaskType(value)
    except ValueError:
        return None
