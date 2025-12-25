"""
Core Pagination Module

Utilities for pagination handling in FastAPI and async Python applications.
"""

from typing import Any, TypeVar, Generic
from pydantic import BaseModel, Field


T = TypeVar("T")


class PaginationParams(BaseModel):
    """
    Pagination request parameters.

    Use as FastAPI dependency for pagination.

    Example:
        ```python
        from fastapi import Depends
        from mehdashti_pagination import PaginationParams

        @router.get("/items")
        async def get_items(pagination: PaginationParams = Depends()):
            # pagination.page, pagination.page_size
            ...
        ```
    """

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=100, ge=1, le=10000, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get limit for database queries."""
        return self.page_size


class PaginationMetadata(BaseModel):
    """
    Pagination response metadata.

    Example:
        ```python
        {
            "page": 1,
            "page_size": 100,
            "total_items": 1250,
            "total_pages": 13,
            "has_next": True,
            "has_previous": False
        }
        ```
    """

    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Items per page")
    total_items: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response.

    Example:
        ```python
        from mehdashti_pagination import PaginatedResponse

        class Item(BaseModel):
            id: int
            name: str

        response = PaginatedResponse[Item](
            data=[Item(id=1, name="Item 1")],
            pagination=PaginationMetadata(...)
        )
        ```
    """

    data: list[T] = Field(..., description="List of items for current page")
    pagination: PaginationMetadata = Field(..., description="Pagination metadata")


class PaginationHelper:
    """
    Pagination Helper

    Provides utilities for pagination calculations and metadata generation.
    """

    @staticmethod
    def calculate_metadata(
        page: int,
        page_size: int,
        total_items: int,
    ) -> PaginationMetadata:
        """
        Calculate pagination metadata.

        Args:
            page: Current page (1-indexed)
            page_size: Items per page
            total_items: Total number of items

        Returns:
            PaginationMetadata with calculated fields

        Example:
            ```python
            metadata = PaginationHelper.calculate_metadata(
                page=1,
                page_size=100,
                total_items=1250
            )
            # metadata.total_pages == 13
            # metadata.has_next == True
            ```
        """
        total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 0
        has_next = page < total_pages
        has_previous = page > 1

        return PaginationMetadata(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous,
        )

    @staticmethod
    def validate_params(
        page: int,
        page_size: int,
        max_page_size: int = 10000,
        default_page_size: int = 100,
    ) -> tuple[int, int]:
        """
        Validate and normalize pagination parameters.

        Args:
            page: Requested page number
            page_size: Requested page size
            max_page_size: Maximum allowed page size
            default_page_size: Default page size if invalid

        Returns:
            Tuple of (normalized_page, normalized_page_size)

        Example:
            ```python
            page, page_size = PaginationHelper.validate_params(
                page=0,  # Invalid
                page_size=50000,  # Too large
            )
            # page == 1
            # page_size == 10000 (clamped to max)
            ```
        """
        # Validate page
        if page < 1:
            page = 1

        # Validate page_size
        if page_size < 1:
            page_size = default_page_size

        if page_size > max_page_size:
            page_size = max_page_size

        return page, page_size

    @staticmethod
    def calculate_offset_limit(page: int, page_size: int) -> tuple[int, int]:
        """
        Calculate offset and limit for database queries.

        Args:
            page: Current page (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (offset, limit)

        Example:
            ```python
            offset, limit = PaginationHelper.calculate_offset_limit(page=3, page_size=10)
            # offset == 20
            # limit == 10

            # Use in SQL:
            # SELECT * FROM items OFFSET {offset} LIMIT {limit}
            ```
        """
        offset = (page - 1) * page_size
        limit = page_size
        return offset, limit


def paginate_query(
    items: list[T],
    page: int,
    page_size: int,
) -> PaginatedResponse[T]:
    """
    Paginate a list of items (for in-memory pagination).

    Args:
        items: Full list of items
        page: Page number (1-indexed)
        page_size: Items per page

    Returns:
        PaginatedResponse with paginated data and metadata

    Example:
        ```python
        all_items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        result = paginate_query(all_items, page=2, page_size=3)
        # result.data == [4, 5, 6]
        # result.pagination.page == 2
        # result.pagination.total_pages == 4
        ```
    """
    total_items = len(items)
    offset, limit = PaginationHelper.calculate_offset_limit(page, page_size)

    # Slice items for current page
    paginated_data = items[offset : offset + limit]

    # Calculate metadata
    metadata = PaginationHelper.calculate_metadata(page, page_size, total_items)

    return PaginatedResponse(data=paginated_data, pagination=metadata)
