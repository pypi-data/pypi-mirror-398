"""Filter builder for submissions endpoints."""

from __future__ import annotations

from typing import Any, Iterable

from ..models.enums import SubmissionOrdering, SubmissionVerdict


class SubmissionsFilter:
    """Chainable builder that outputs query parameters."""

    def __init__(self) -> None:
        self._params: dict[str, Any] = {}
        self._verdicts: list[str] = []

    def verdict(self, *aliases_or_numbers: str | int | SubmissionVerdict) -> "SubmissionsFilter":
        for value in aliases_or_numbers:
            self._verdicts.append(_stringify(value))
        return self

    def verdict_eq(self, alias_or_number: str | int | SubmissionVerdict) -> "SubmissionsFilter":
        self._verdicts = [_stringify(alias_or_number)]
        return self

    def verdict_ne(self, alias_or_number: str | int | SubmissionVerdict) -> "SubmissionsFilter":
        self._params["verdict__ne"] = _stringify(alias_or_number)
        return self

    def score_between(self, lo: float, hi: float) -> "SubmissionsFilter":
        self._params["score__gte"] = str(lo)
        self._params["score__lte"] = str(hi)
        return self

    def id_eq(self, n: int) -> "SubmissionsFilter":
        self._params["id"] = str(n)
        return self

    def id_ne(self, n: int) -> "SubmissionsFilter":
        self._params["id__ne"] = str(n)
        return self

    def user(self, query: str) -> "SubmissionsFilter":
        self._params["user"] = query
        return self

    def language(self, lang: str) -> "SubmissionsFilter":
        self._params["language"] = lang
        return self

    def date_from(self, iso: str) -> "SubmissionsFilter":
        self._params["created_at__gte"] = iso
        return self

    def date_to(self, iso: str) -> "SubmissionsFilter":
        self._params["created_at__lte"] = iso
        return self

    def competition_ids(self, ids: Iterable[int]) -> "SubmissionsFilter":
        values = ",".join(str(i) for i in ids)
        if values:
            self._params["competition_id"] = values
        return self

    def ordering(self, key: str | SubmissionOrdering) -> "SubmissionsFilter":
        self._params["ordering"] = _stringify(key)
        return self

    def per_page(self, n: int) -> "SubmissionsFilter":
        self._params["page_size"] = str(n)
        return self

    def page(self, n: int) -> "SubmissionsFilter":
        self._params["page"] = str(n)
        return self

    def to_params(self) -> dict[str, str]:
        params = {k: str(v) for k, v in self._params.items() if v is not None}
        if self._verdicts:
            params["verdict"] = ",".join(self._verdicts)
        return params.copy()


def _stringify(value: Any) -> str:
    if isinstance(value, (SubmissionVerdict, SubmissionOrdering)):
        return value.value
    return str(value)
