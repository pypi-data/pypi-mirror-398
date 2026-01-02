"""Rating and leaderboard models."""

from __future__ import annotations

from typing import Any

from .common import ISODateTime, TolerantModel
from .enums import RatingRunStatus


class RatingStatus(TolerantModel):
    competition_id: int
    status: str
    started_at: ISODateTime | None = None
    updated_at: ISODateTime | None = None
    message: str | None = None
    progress: float | None = None

    @property
    def status_enum(self) -> RatingRunStatus | None:
        status = getattr(self, "status", None)
        if not status:
            return None
        try:
            return RatingRunStatus(status)
        except ValueError:
            return None


class RatingChange(TolerantModel):
    user_id: int | None = None
    username: str | None = None
    old_rating: float | None = None
    new_rating: float | None = None
    delta: float | None = None
    placed: int | None = None
    metadata: dict[str, Any] | None = None
