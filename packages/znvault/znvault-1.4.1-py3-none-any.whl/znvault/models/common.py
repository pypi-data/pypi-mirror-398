# Path: zn-vault-sdk-python/src/znvault/models/common.py
"""Common model types."""

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class Page(Generic[T]):
    """Paginated response container."""

    items: list[T]
    total: int
    limit: int
    offset: int
    next_marker: str | None = None

    @property
    def has_more(self) -> bool:
        """Check if there are more items to fetch."""
        return self.offset + len(self.items) < self.total

    @classmethod
    def from_dict(cls, data: dict, item_type: type[T]) -> "Page[T]":
        """Create Page from API response dictionary."""
        items_key = None
        for key in ["items", "data", "entries", "keys", "secrets", "admins", "tenants", "roles"]:
            if key in data:
                items_key = key
                break

        if items_key:
            raw_items = data.get(items_key, [])
        elif isinstance(data, list):
            raw_items = data
        else:
            raw_items = []

        items = [
            item_type.from_dict(item) if hasattr(item_type, "from_dict") else item
            for item in raw_items
        ]

        return cls(
            items=items,
            total=data.get("total", len(items)),
            limit=data.get("limit", data.get("pageSize", len(items))),
            offset=data.get("offset", 0),
            next_marker=data.get("nextMarker"),
        )
