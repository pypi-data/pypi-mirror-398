from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class PagedResponse(Generic[T]):
    """Container for paginated API responses."""

    items: list[T]
    next_page_token: str | None

    def has_next(self) -> bool:
        """Check if there are more pages available."""
        return self.next_page_token is not None
