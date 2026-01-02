"""Competition models."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from .common import ISODateTime, TolerantModel
from .enums import CompetitionStatus
from .hub import Hub
from .task import Task


class CompetitionListItem(TolerantModel):
    id: int
    hub: Hub | None = None
    name: str
    slug: str | None = None
    status: str | None = None
    rated: bool | None = None
    visible: bool | None = None
    starts_at: ISODateTime | None = None
    ends_at: ISODateTime | None = None
    participants_count: int | None = None
    tasks_count: int | None = None


class Competition(CompetitionListItem):
    description: str | None = None
    registration_open: bool | None = None
    registration_closes_at: ISODateTime | None = None
    duration_minutes: int | None = None
    languages: list[str] = Field(default_factory=list)
    tasks: list[Task] = Field(default_factory=list)
    settings: dict[str, Any] | None = None

    @property
    def status_enum(self) -> CompetitionStatus | None:
        status = self.status
        if not status:
            return None
        try:
            return CompetitionStatus(status)
        except ValueError:
            return None


class CompetitionRatingOptions(TolerantModel):
    allow_ties: bool | None = None
    rating_floor: int | None = None
    rating_ceiling: int | None = None
    consider_practice: bool | None = None


class CompetitionRatingSettings(TolerantModel):
    enabled: bool | None = None
    rating_system: str | None = None
    last_rated_at: ISODateTime | None = None
    options: CompetitionRatingOptions | None = None
