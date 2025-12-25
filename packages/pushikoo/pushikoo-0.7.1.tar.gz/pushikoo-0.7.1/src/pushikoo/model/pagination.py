from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")

# Maximum number of items that can be requested per page
MAX_PAGE_LIMIT = 100


def apply_page_limit(limit: int | None) -> int | None:
    """
    Apply MAX_PAGE_LIMIT to a requested limit value.

    - If limit is None, return None (no limit)
    - If limit is -1, return MAX_PAGE_LIMIT (all items, but capped)
    - If limit is positive, return min(limit, MAX_PAGE_LIMIT)
    """
    if limit is None:
        return None
    if limit == -1:
        return MAX_PAGE_LIMIT
    return min(limit, MAX_PAGE_LIMIT)


class Page(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T]
    total: int
    limit: int | None
    offset: int | None
