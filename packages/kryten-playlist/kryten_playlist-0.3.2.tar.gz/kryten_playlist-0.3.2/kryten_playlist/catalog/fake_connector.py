"""Fake connector for testing / dev."""

from __future__ import annotations

from typing import AsyncIterator

from kryten_playlist.catalog.models import CatalogItem


class FakeConnector:
    """A deterministic connector that emits a fixed set of items for testing."""

    def __init__(self, items: list[CatalogItem] | None = None):
        self._items = items if items is not None else self._default_items()

    @staticmethod
    def _default_items() -> list[CatalogItem]:
        return [
            CatalogItem(
                video_id="v001",
                title="Test Video 1",
                categories=["Horror", "Comedy"],
                duration_seconds=3600,
            ),
            CatalogItem(
                video_id="v002",
                title="Test Video 2",
                categories=["Sci-Fi"],
                duration_seconds=5400,
            ),
            CatalogItem(
                video_id="v003",
                title="Test Video 3",
                categories=[],
                duration_seconds=None,
            ),
        ]

    async def iter_items(self) -> AsyncIterator[CatalogItem]:
        for item in self._items:
            yield item
