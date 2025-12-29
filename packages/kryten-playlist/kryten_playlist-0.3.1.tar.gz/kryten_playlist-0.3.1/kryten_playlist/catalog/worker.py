"""Catalog refresh worker that performs the full pipeline."""

from __future__ import annotations

import logging
from typing import Any

import aiosqlite

from kryten_playlist.catalog.models import CatalogConnector, SnapshotMetadata, generate_snapshot_id
from kryten_playlist.catalog.rebuild import rebuild_catalog
from kryten_playlist.nats.kv import BUCKET_SNAPSHOT, KvJson

logger = logging.getLogger(__name__)


async def run_catalog_refresh(
    *,
    connector: CatalogConnector,
    sqlite_conn: aiosqlite.Connection,
    kv: KvJson,
    manifest_base_url: str = "https://mediacms.example.com/media",
    source: str = "mediacms",
    notes: str = "",
) -> SnapshotMetadata:
    """Execute a full catalog refresh.

    1. Generate a new snapshot_id.
    2. Rebuild SQLite using the connector.
    3. Write snapshot metadata to KV.
    4. Update the "current" pointer in KV.

    Returns the SnapshotMetadata for the new snapshot.
    Raises on failure (KV current is NOT updated on error).
    """
    snapshot_id = generate_snapshot_id()
    logger.info("catalog_refresh starting snapshot_id=%s", snapshot_id)

    # Rebuild SQLite
    item_count = await rebuild_catalog(
        sqlite_conn,
        connector.iter_items(),
        snapshot_id=snapshot_id,
        manifest_base_url=manifest_base_url,
    )

    # Build metadata
    meta = SnapshotMetadata(
        snapshot_id=snapshot_id,
        source=source,
        item_count=item_count,
        notes=notes,
    )

    # Write snapshot record
    await kv.put_json(BUCKET_SNAPSHOT, f"snapshots/{snapshot_id}", meta.to_dict())

    # Update current pointer
    await kv.put_json(BUCKET_SNAPSHOT, "current", meta.to_dict())

    logger.info(
        "catalog_refresh complete snapshot_id=%s item_count=%d",
        snapshot_id,
        item_count,
    )
    return meta
