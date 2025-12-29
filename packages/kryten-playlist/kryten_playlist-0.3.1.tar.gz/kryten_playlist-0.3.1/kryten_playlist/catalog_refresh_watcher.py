from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable

import aiosqlite

from kryten_playlist.catalog.fake_connector import FakeConnector
from kryten_playlist.catalog.worker import run_catalog_refresh
from kryten_playlist.nats.kv import BUCKET_SNAPSHOT, KvJson

logger = logging.getLogger(__name__)


@dataclass
class CatalogRefreshWatchState:
    last_seen_correlation_id: str = ""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def process_catalog_refresh_marker(
    kv: KvJson,
    *,
    state: CatalogRefreshWatchState,
    on_refresh: Callable[[], Awaitable[None]] | None = None,
) -> dict[str, Any] | None:
    """Check for a new catalog_refresh marker and optionally run the pipeline.

    Returns the marker doc when a new request is observed, otherwise None.
    """
    marker = await kv.get_json(BUCKET_SNAPSHOT, "catalog_refresh/last")
    if not isinstance(marker, dict):
        return None

    correlation_id = str(marker.get("correlation_id") or "").strip()
    if not correlation_id or correlation_id == state.last_seen_correlation_id:
        return None

    state.last_seen_correlation_id = correlation_id

    # Run the refresh callback if provided
    if on_refresh is not None:
        await on_refresh()

    # Record an acknowledgement
    ack = {
        "processed_at": _now_iso(),
        "marker": marker,
    }
    await kv.put_json(BUCKET_SNAPSHOT, "catalog_refresh/last_processed", ack)

    return marker


async def run_catalog_refresh_watcher(
    *,
    kv: KvJson,
    shutdown_event: asyncio.Event,
    poll_seconds: float = 2.0,
    sqlite_conn: aiosqlite.Connection | None = None,
    manifest_base_url: str = "https://mediacms.example.com/media",
    run_refresh: bool = True,
) -> None:
    """Background watcher that polls for catalog_refresh markers.

    If run_refresh is True and sqlite_conn is provided, actually runs the
    catalog refresh pipeline when a new marker is detected.
    """
    state = CatalogRefreshWatchState()

    async def _do_refresh() -> None:
        if not run_refresh or sqlite_conn is None:
            logger.info("catalog_refresh marker observed but refresh disabled or no sqlite_conn")
            return
        try:
            connector = FakeConnector()  # TODO: swap for real connector
            await run_catalog_refresh(
                connector=connector,
                sqlite_conn=sqlite_conn,
                kv=kv,
                manifest_base_url=manifest_base_url,
                source="watcher",
            )
        except Exception:
            logger.exception("catalog_refresh pipeline failed")

    while not shutdown_event.is_set():
        try:
            marker = await process_catalog_refresh_marker(kv, state=state, on_refresh=_do_refresh)
            if marker is not None:
                logger.info(
                    "Observed catalog_refresh request correlation_id=%s requested_by=%s",
                    str(marker.get("correlation_id") or ""),
                    str(marker.get("requested_by") or ""),
                )
        except Exception:
            logger.exception("catalog_refresh watcher loop error")

        try:
            await asyncio.wait_for(shutdown_event.wait(), timeout=poll_seconds)
        except TimeoutError:
            pass
