"""Multiple-choice configuration models."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from .common import TolerantModel


class MCOption(TolerantModel):
    id: int | str
    text: str
    is_correct: bool | None = None
    explanation: str | None = None


class MCConfig(TolerantModel):
    question: str | None = None
    options: list[MCOption] = Field(default_factory=list)
    allow_multiple: bool | None = None
    shuffle_options: bool | None = None
    metadata: dict[str, Any] | None = None


class MCPatch(TolerantModel):
    question: str | None = None
    options: list[dict[str, Any]] | None = None
    allow_multiple: bool | None = None
    shuffle_options: bool | None = None
