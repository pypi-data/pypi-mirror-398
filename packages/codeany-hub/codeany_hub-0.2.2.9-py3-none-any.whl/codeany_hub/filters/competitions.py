"""Filter builder for competition listings."""

from __future__ import annotations

from typing import Any

from ..models.enums import CompetitionOrdering, CompetitionStatus

class CompetitionsFilter:
    def __init__(self) -> None:
        self._params: dict[str, str] = {}
        self._include: set[str] = set()

    def search(self, text: str) -> "CompetitionsFilter":
        self._params["search"] = text
        return self

    def type(self, val: str) -> "CompetitionsFilter":
        self._params["type"] = val
        return self

    def visible(self, yes: bool) -> "CompetitionsFilter":
        self._params["visible"] = _bool(yes)
        return self

    def registration(self, yes: bool) -> "CompetitionsFilter":
        self._params["registration_open"] = _bool(yes)
        return self

    def started(self, code: int) -> "CompetitionsFilter":
        self._params["started"] = str(code)
        return self

    def status(self, text: str | CompetitionStatus) -> "CompetitionsFilter":
        self._params["status"] = _stringify(text)
        return self

    def rated(self, yes: bool) -> "CompetitionsFilter":
        self._params["rated"] = _bool(yes)
        return self

    def date_from(self, iso: str) -> "CompetitionsFilter":
        self._params["starts_at__gte"] = iso
        return self

    def date_to(self, iso: str) -> "CompetitionsFilter":
        self._params["ends_at__lte"] = iso
        return self

    def length_between(self, lo: int, hi: int) -> "CompetitionsFilter":
        self._params["duration__gte"] = str(lo)
        self._params["duration__lte"] = str(hi)
        return self

    def virtual(self, yes: bool) -> "CompetitionsFilter":
        self._params["virtual"] = _bool(yes)
        return self

    def include(self, *fields: str) -> "CompetitionsFilter":
        self._include.update(fields)
        return self

    def sort(self, key: str | CompetitionOrdering) -> "CompetitionsFilter":
        self._params["ordering"] = _stringify(key)
        return self

    def per_page(self, n: int) -> "CompetitionsFilter":
        self._params["page_size"] = str(n)
        return self

    def page(self, m: int) -> "CompetitionsFilter":
        self._params["page"] = str(m)
        return self

    def to_params(self) -> dict[str, str]:
        params = {k: v for k, v in self._params.items() if v is not None}
        if self._include:
            params["include"] = ",".join(sorted(self._include))
        return params.copy()


def _bool(flag: bool) -> str:
    return "1" if flag else "0"


def _stringify(value: Any) -> str:
    if isinstance(value, (CompetitionStatus, CompetitionOrdering)):
        return value.value
    return str(value)
