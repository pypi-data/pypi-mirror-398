"""Pagination utilities for cursor-based pagination"""

from __future__ import annotations

from typing import AsyncGenerator, Awaitable, Callable, Generic, Optional, TypeVar

T = TypeVar("T")


class PaginatedResponse(Generic[T]):
    """Response from a paginated API endpoint"""

    def __init__(
        self,
        data: list[T],
        next_cursor: Optional[str] = None,
        has_more: bool = False,
    ):
        """
        Initialize a paginated response.

        Args:
            data: List of items in this page
            next_cursor: Cursor for the next page (if available)
            has_more: Whether there are more pages available
        """
        self.data = data
        self.next_cursor = next_cursor
        self.has_more = has_more


async def paginate_all(
    fetch_page: Callable[[Optional[str]], Awaitable[PaginatedResponse[T]]],
    initial_cursor: Optional[str] = None,
) -> AsyncGenerator[T, None]:
    """
    Iterator helper for auto-pagination.

    Automatically fetches all pages using cursor-based pagination.

    Args:
        fetch_page: Async function that fetches a page given an optional cursor
        initial_cursor: Optional initial cursor to start from

    Yields:
        Individual items from all pages

    Example:
        ```python
        async def fetch_events(cursor: Optional[str] = None):
            response = await client.request("GET", "/events", params={"cursor": cursor})
            return PaginatedResponse(
                data=response["data"],
                next_cursor=response.get("nextCursor"),
                has_more=response.get("hasMore", False),
            )

        async for event in paginate_all(fetch_events):
            print(event.id)
        ```
    """
    cursor: Optional[str] = initial_cursor
    has_more = True

    while has_more:
        response = await fetch_page(cursor)

        for item in response.data:
            yield item

        cursor = response.next_cursor
        has_more = response.has_more and cursor is not None


async def collect_all(
    fetch_page: Callable[[Optional[str]], Awaitable[PaginatedResponse[T]]],
    initial_cursor: Optional[str] = None,
) -> list[T]:
    """
    Collect all items from paginated endpoint into a list.

    Args:
        fetch_page: Async function that fetches a page given an optional cursor
        initial_cursor: Optional initial cursor to start from

    Returns:
        List of all items from all pages

    Example:
        ```python
        async def fetch_events(cursor: Optional[str] = None):
            response = await client.request("GET", "/events", params={"cursor": cursor})
            return PaginatedResponse(
                data=response["data"],
                next_cursor=response.get("nextCursor"),
                has_more=response.get("hasMore", False),
            )

        all_events = await collect_all(fetch_events)
        ```
    """
    items: list[T] = []

    async for item in paginate_all(fetch_page, initial_cursor):
        items.append(item)

    return items
