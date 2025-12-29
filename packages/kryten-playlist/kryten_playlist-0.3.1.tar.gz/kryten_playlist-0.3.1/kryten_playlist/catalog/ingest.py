"""CLI script to ingest catalog from MediaCMS into enhanced local database.

Usage:
    python -m kryten_playlist.catalog.ingest --base-url https://mediacms.example.com --db catalog.db

This will:
1. Fetch all media items from MediaCMS API
2. Parse and sanitize titles
3. Store in SQLite with enhanced schema (LLM fields left empty for later enrichment)
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

from kryten_playlist.catalog.enhanced_schema import init_enhanced_schema
from kryten_playlist.catalog.mediacms_connector import MediaCMSConnector
from kryten_playlist.catalog.models import generate_snapshot_id
from kryten_playlist.catalog.title_sanitizer import parse_title

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def ingest_catalog(
    base_url: str,
    db_path: str,
    timeout: float = 30.0,
    concurrency: int = 24,
) -> dict[str, int]:
    """Ingest catalog from MediaCMS into local SQLite database.

    Returns dict with counts: {"items": N, "categories": N, "new": N, "updated": N}
    """
    connector = MediaCMSConnector(base_url=base_url, timeout=timeout, concurrency=concurrency)
    snapshot_id = generate_snapshot_id()
    now = datetime.now(timezone.utc).isoformat()

    stats = {"items": 0, "categories": 0, "new": 0, "updated": 0}

    async with aiosqlite.connect(db_path) as conn:
        # Initialize schema
        await init_enhanced_schema(conn)

        # Track existing items for update vs insert
        cursor = await conn.execute("SELECT video_id FROM catalog_item")
        existing_ids = {row[0] for row in await cursor.fetchall()}

        # Category cache
        category_cache: dict[str, int] = {}

        async def get_or_create_category(name: str) -> int:
            if name in category_cache:
                return category_cache[name]

            cursor = await conn.execute(
                "SELECT id FROM catalog_category WHERE name = ?", (name,)
            )
            row = await cursor.fetchone()
            if row:
                category_cache[name] = row[0]
                return row[0]

            cursor = await conn.execute(
                "INSERT INTO catalog_category (name) VALUES (?)", (name,)
            )
            cat_id = cursor.lastrowid
            category_cache[name] = cat_id
            stats["categories"] += 1
            return cat_id

        logger.info("Starting catalog ingest from %s", base_url)
        logger.info("Snapshot ID: %s", snapshot_id)

        start_time = datetime.now()

        async for item in connector.iter_items():
            stats["items"] += 1

            # Parse and sanitize title
            parsed = parse_title(item.title)

            if item.video_id in existing_ids:
                # Update existing item (preserve LLM fields)
                await conn.execute(
                    """
                    UPDATE catalog_item SET
                        raw_title = ?,
                        thumbnail_url = ?,
                        duration_seconds = ?,
                        sanitized_title = ?,
                        title_base = ?,
                        year = ?,
                        season = ?,
                        episode = ?,
                        episode_title = ?,
                        is_tv = ?,
                        snapshot_id = ?,
                        updated_at = ?,
                        mediacms_category = ?,
                        sanitized_category = ?
                    WHERE video_id = ?
                    """,
                    (
                        item.title,
                        item.thumbnail_url,
                        item.duration_seconds,
                        parsed.sanitized,
                        parsed.title_base,
                        parsed.year,
                        parsed.season,
                        parsed.episode,
                        parsed.episode_title,
                        1 if parsed.is_tv else 0,
                        snapshot_id,
                        now,
                        item.mediacms_category,
                        item.sanitized_category,
                        item.video_id,
                    ),
                )
                stats["updated"] += 1
            else:
                # Insert new item
                await conn.execute(
                    """
                    INSERT INTO catalog_item (
                        video_id, raw_title, thumbnail_url, duration_seconds,
                        sanitized_title, title_base, year, season, episode, episode_title,
                        is_tv, snapshot_id, created_at, updated_at, mediacms_category, sanitized_category
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.video_id,
                        item.title,
                        item.thumbnail_url,
                        item.duration_seconds,
                        parsed.sanitized,
                        parsed.title_base,
                        parsed.year,
                        parsed.season,
                        parsed.episode,
                        parsed.episode_title,
                        1 if parsed.is_tv else 0,
                        snapshot_id,
                        now,
                        now,
                        item.mediacms_category,
                        item.sanitized_category,
                    ),
                )
                stats["new"] += 1

            # Handle categories
            await conn.execute(
                "DELETE FROM catalog_item_category WHERE video_id = ?",
                (item.video_id,),
            )
            for cat_name in item.categories:
                cat_id = await get_or_create_category(cat_name)
                await conn.execute(
                    "INSERT OR IGNORE INTO catalog_item_category (video_id, category_id) VALUES (?, ?)",
                    (item.video_id, cat_id),
                )

            if stats["items"] % 100 == 0:
                logger.info("Processed %d items...", stats["items"])
                await conn.commit()

        await conn.commit()

    elapsed = datetime.now() - start_time
    total_seconds = elapsed.total_seconds()
    items_per_second = stats["items"] / max(total_seconds, 1)
    avg_ms = (total_seconds / max(stats["items"], 1)) * 1000

    logger.info(
        "Ingest complete: %d items (%d new, %d updated), %d categories",
        stats["items"],
        stats["new"],
        stats["updated"],
        stats["categories"],
    )
    logger.info(
        "Time: %s | Rate: %.1f items/sec | Avg: %.1f ms/item",
        elapsed,
        items_per_second,
        avg_ms,
    )
    return stats


async def show_stats(db_path: str) -> None:
    """Show statistics about the catalog database."""
    if not Path(db_path).exists():
        print(f"Database not found: {db_path}")
        return

    async with aiosqlite.connect(db_path) as conn:
        cursor = await conn.execute("SELECT COUNT(*) FROM catalog_item WHERE mediacms_category IS NOT NULL")
        total = (await cursor.fetchone())[0]

        cursor = await conn.execute("SELECT COUNT(*) FROM catalog_item WHERE is_tv = 1 AND mediacms_category IS NOT NULL")
        tv_count = (await cursor.fetchone())[0]

        cursor = await conn.execute("SELECT COUNT(*) FROM catalog_item WHERE is_tv = 0 AND mediacms_category IS NOT NULL")
        movie_count = (await cursor.fetchone())[0]

        cursor = await conn.execute("SELECT COUNT(*) FROM catalog_item WHERE synopsis IS NOT NULL AND mediacms_category IS NOT NULL")
        enriched = (await cursor.fetchone())[0]

        cursor = await conn.execute("SELECT COUNT(*) FROM catalog_category")
        categories = (await cursor.fetchone())[0]

        cursor = await conn.execute("SELECT COUNT(*) FROM catalog_tag")
        tags = (await cursor.fetchone())[0]

        cursor = await conn.execute(
            "SELECT SUM(duration_seconds) FROM catalog_item WHERE duration_seconds IS NOT NULL AND mediacms_category IS NOT NULL"
        )
        total_duration = (await cursor.fetchone())[0] or 0

        print(f"\n📊 Catalog Statistics for {db_path}")
        print("=" * 50)
        print(f"  Total items:      {total:,}")
        print(f"  TV episodes:      {tv_count:,}")
        print(f"  Movies:           {movie_count:,}")
        print(f"  LLM enriched:     {enriched:,} ({100*enriched/total:.1f}%)" if total else "  LLM enriched:     0")
        print(f"  Categories:       {categories:,}")
        print(f"  Tags:             {tags:,}")
        print(f"  Total duration:   {total_duration // 3600:,}h {(total_duration % 3600) // 60}m")
        print()


async def search_catalog(db_path: str, query: str, limit: int = 20) -> None:
    """Search the catalog using full-text search."""
    if not Path(db_path).exists():
        print(f"Database not found: {db_path}")
        return

    async with aiosqlite.connect(db_path) as conn:
        cursor = await conn.execute(
            """
            SELECT
                ci.video_id,
                ci.sanitized_title,
                ci.is_tv,
                ci.duration_seconds,
                ci.synopsis
            FROM catalog_fts
            JOIN catalog_item ci ON catalog_fts.video_id = ci.video_id
            WHERE catalog_fts MATCH ? AND ci.mediacms_category IS NOT NULL
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit),
        )
        results = await cursor.fetchall()

        print(f"\n🔍 Search results for '{query}'")
        print("=" * 60)
        if not results:
            print("  No results found.")
        else:
            for video_id, title, is_tv, duration, synopsis in results:
                type_icon = "📺" if is_tv else "🎬"
                dur_str = f"{duration // 60}m" if duration else "?m"
                print(f"  {type_icon} {title} [{dur_str}]")
                if synopsis:
                    print(f"      {synopsis[:80]}...")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest and manage enhanced catalog from MediaCMS"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest catalog from MediaCMS")
    ingest_parser.add_argument(
        "--base-url",
        required=True,
        help="MediaCMS base URL (e.g., https://mediacms.example.com)",
    )
    ingest_parser.add_argument(
        "--db",
        default="catalog.db",
        help="SQLite database path (default: catalog.db)",
    )
    ingest_parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="HTTP timeout in seconds (default: 30)",
    )
    ingest_parser.add_argument(
        "--concurrency",
        type=int,
        default=24,
        help="Number of concurrent requests (default: 24)",
    )

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show catalog statistics")
    stats_parser.add_argument(
        "--db",
        default="catalog.db",
        help="SQLite database path (default: catalog.db)",
    )

    # Search command
    search_parser = subparsers.add_parser("search", help="Search the catalog")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "--db",
        default="catalog.db",
        help="SQLite database path (default: catalog.db)",
    )
    search_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum results (default: 20)",
    )

    args = parser.parse_args()

    if args.command == "ingest":
        asyncio.run(ingest_catalog(args.base_url, args.db, args.timeout, args.concurrency))
    elif args.command == "stats":
        asyncio.run(show_stats(args.db))
    elif args.command == "search":
        asyncio.run(search_catalog(args.db, args.query, args.limit))


if __name__ == "__main__":
    main()
