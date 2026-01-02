"""Pagination helpers and models."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Generic representation of paginated endpoints."""

    model_config = ConfigDict(extra="allow")

    count: int | None = None
    next: str | None = None
    previous: str | None = None
    results: list[T]


def iter_pages(fetch_page: Callable[[int], Page[T]]) -> Iterator[T]:
    """Iterate over all results for a paginated endpoint."""

    page_num = 1
    while True:
        page = fetch_page(page_num)
        for item in page.results:
            yield item
        if not page.next:
            break
        page_num += 1
