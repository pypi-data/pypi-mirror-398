"""SQLite catalog rebuild logic for catalog refresh."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import AsyncIterator

import aiosqlite

from kryten_playlist.catalog.models import CatalogItem

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def rebuild_catalog(
    conn: aiosqlite.Connection,
    items: AsyncIterator[CatalogItem],
    *,
    snapshot_id: str,
    manifest_base_url: str = "https://mediacms.example.com/media",
) -> int:
    """Rebuild the catalog index from an async iterator of CatalogItems.

    Replaces all existing rows with the new snapshot. Uses a transaction to
    ensure atomicity.

    Returns the number of items inserted.
    """
    logger.info("Starting catalog rebuild for snapshot_id=%s", snapshot_id)

    now = _now_iso()
    count = 0

    # Collect all items first so we can do the rebuild atomically
    all_items: list[CatalogItem] = []
    async for item in items:
        all_items.append(item)

    # Collect all categories
    all_categories: set[str] = set()
    for item in all_items:
        for cat in item.categories:
            c = str(cat).strip()
            if c:
                all_categories.add(c)

    await conn.execute("BEGIN EXCLUSIVE")
    try:
        # Clear existing data
        await conn.execute("DELETE FROM catalog_item_category")
        await conn.execute("DELETE FROM catalog_item")
        await conn.execute("DELETE FROM catalog_category")

        # Insert categories
        for cat in sorted(all_categories):
            await conn.execute(
                "INSERT INTO catalog_category(category) VALUES(?)",
                (cat,),
            )

        # Insert items and category links
        for item in all_items:
            manifest_url = item.manifest_url(manifest_base_url)
            categories_json = json.dumps(item.categories)

            await conn.execute(
                "INSERT INTO catalog_item(video_id, title, categories_json, manifest_url, duration_seconds, thumbnail_url, snapshot_id, created_at) "
                "VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    item.video_id,
                    item.title,
                    categories_json,
                    manifest_url,
                    item.duration_seconds,
                    item.thumbnail_url,
                    snapshot_id,
                    now,
                ),
            )

            for cat in item.categories:
                c = str(cat).strip()
                if c:
                    await conn.execute(
                        "INSERT OR IGNORE INTO catalog_item_category(video_id, category) VALUES(?, ?)",
                        (item.video_id, c),
                    )

            count += 1

        await conn.execute("COMMIT")
    except Exception:
        await conn.execute("ROLLBACK")
        raise

    logger.info("Catalog rebuild complete: %d items for snapshot_id=%s", count, snapshot_id)
    return count
