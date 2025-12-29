from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import aiosqlite


@dataclass(frozen=True)
class CatalogSearchResult:
    snapshot_id: str
    items: list[dict]
    total: int


class CatalogRepository:
    def __init__(self, conn: aiosqlite.Connection):
        self._conn = conn
        # Ensure row_factory for dict-like row access
        self._conn.row_factory = aiosqlite.Row

    async def _detect_schema(self) -> tuple[str, list[str]]:
        """Returns (title_selection, search_columns).
        
        Detects if we are using the legacy schema (title column) or 
        enriched schema (sanitized_title/raw_title).
        """
        cursor = await self._conn.execute("PRAGMA table_info(catalog_item)")
        columns = {row["name"] for row in await cursor.fetchall()}
        
        if "title" in columns:
            return "title", ["title"]
        elif "sanitized_title" in columns:
            search_cols = ["sanitized_title"]
            if "raw_title" in columns:
                search_cols.append("raw_title")
            return "sanitized_title as title", search_cols
        else:
            return "video_id as title", ["video_id"]

    async def get_items_by_video_ids(self, video_ids: list[str]) -> dict[str, dict]:
        """Fetch catalog items by video_id.

        Returns a mapping of video_id -> item dict.
        Missing ids are omitted from the result.
        """
        ids = [str(v).strip() for v in (video_ids or []) if str(v).strip()]
        if not ids:
            return {}

        title_sel, _ = await self._detect_schema()
        placeholders = ",".join(["?"] * len(ids))
        cursor = await self._conn.execute(
            f"SELECT video_id, {title_sel}, duration_seconds, thumbnail_url, snapshot_id, genre, mood, era, year, synopsis "
            f"FROM catalog_item WHERE video_id IN ({placeholders}) AND mediacms_category IS NOT NULL",
            ids,
        )
        rows = await cursor.fetchall()

        out: dict[str, dict] = {}
        for r in rows:
            out[str(r["video_id"])] = {
                "video_id": r["video_id"],
                "title": r["title"],
                "genre": r["genre"],
                "mood": r["mood"],
                "era": r["era"],
                "year": r["year"],
                "synopsis": r["synopsis"],
                "duration_seconds": r["duration_seconds"],
                "thumbnail_url": r["thumbnail_url"],
                "snapshot_id": r["snapshot_id"],
            }
        return out

    async def get_item(self, video_id: str) -> dict | None:
        """Fetch a single catalog item by video_id."""
        vid = str(video_id).strip()
        if not vid:
            return None
            
        title_sel, _ = await self._detect_schema()
        cursor = await self._conn.execute(
            f"SELECT video_id, {title_sel}, duration_seconds, thumbnail_url, snapshot_id, genre, mood, era, year, synopsis "
            "FROM catalog_item WHERE video_id = ? AND mediacms_category IS NOT NULL",
            (vid,),
        )
        r = await cursor.fetchone()
        if not r:
            return None
            
        return {
            "video_id": r["video_id"],
            "title": r["title"],
            "genre": r["genre"],
            "mood": r["mood"],
            "era": r["era"],
            "year": r["year"],
            "synopsis": r["synopsis"],
            "duration_seconds": r["duration_seconds"],
            "thumbnail_url": r["thumbnail_url"],
            "snapshot_id": r["snapshot_id"],
        }

    async def get_categories(self) -> list[str]:
        """Get distinct genres from catalog."""
        try:
            cursor = await self._conn.execute(
                "SELECT category FROM catalog_category ORDER BY category ASC"
            )
            rows = await cursor.fetchall()
            return [r["category"] for r in rows]
        except Exception:
            return []

    async def get_pending_count(self) -> int:
        """Count items that are waiting for enrichment."""
        cursor = await self._conn.execute(
            "SELECT COUNT(*) FROM catalog_item WHERE llm_enriched_at IS NULL"
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def search(
        self,
        q: Optional[str],
        categories: list[str],
        limit: int,
        offset: int,
        # New facets
        series: Optional[str] = None,
        title: Optional[str] = None,
        theme: Optional[str] = None, # Maps to llm_notes or maybe tags? For now, searching llm_notes/synopsis
        actor: Optional[str] = None,
        director: Optional[str] = None,
        genre: Optional[str] = None,
        mood: Optional[str] = None,
        era: Optional[str] = None,
        # Access control
        include_uncategorized: bool = False,
    ) -> CatalogSearchResult:
        """Search catalog items using LIKE and facets."""
        q = (q or "").strip()

        where = []
        params: list[object] = []
        
        title_sel, search_cols = await self._detect_schema()

        if q:
            clauses = [f"{col} LIKE ?" for col in search_cols]
            where.append(f"({' OR '.join(clauses)})")
            params.extend([f"%{q}%"] * len(search_cols))

        if categories:
            placeholders = ",".join(["?"] * len(categories))
            where.append(f"video_id IN (SELECT video_id FROM catalog_item_category WHERE category IN ({placeholders}))")
            params.extend(categories)

        # Facet filters
        if series:
            # Series typically implies title_base match
            where.append("title_base LIKE ?")
            params.append(f"%{series}%")
            
        if title:
            # Specific title search (sanitized_title or raw_title)
            where.append("sanitized_title LIKE ?")
            params.append(f"%{title}%")
            
        if actor:
            where.append("cast_list LIKE ?")
            params.append(f"%{actor}%")
            
        if director:
            where.append("director LIKE ?")
            params.append(f"%{director}%")
            
        if genre:
            where.append("genre LIKE ?")
            params.append(f"%{genre}%")
            
        if mood:
            where.append("mood LIKE ?")
            params.append(f"%{mood}%")
            
        if era:
            where.append("era LIKE ?")
            params.append(f"%{era}%")

        if theme:
            # Searching synopsis and llm_notes for theme
            where.append("(synopsis LIKE ? OR llm_notes LIKE ?)")
            params.extend([f"%{theme}%", f"%{theme}%"])

        # Access control
        if not include_uncategorized:
            # Exclude items that are NULL or explicitly "Uncategorized"
            where.append("(mediacms_category IS NOT NULL AND mediacms_category != 'Uncategorized')")

        # Global filter: only show enriched items
        where.append("llm_enriched_at IS NOT NULL")

        where_sql = "" if not where else ("WHERE " + " AND ".join(where))

        count_cursor = await self._conn.execute(
            f"SELECT COUNT(*) AS cnt FROM catalog_item {where_sql}",
            params,
        )
        total_row = await count_cursor.fetchone()
        total = int(total_row["cnt"] if total_row else 0)

        cursor = await self._conn.execute(
            f"SELECT video_id, {title_sel}, duration_seconds, thumbnail_url, snapshot_id, genre, mood, era, year, synopsis "
            f"FROM catalog_item {where_sql} ORDER BY {search_cols[0]} ASC LIMIT ? OFFSET ?",
            [*params, limit, offset],
        )
        rows = await cursor.fetchall()

        snapshot_id = rows[0]["snapshot_id"] if rows else ""
        items = []
        for r in rows:
            items.append(
                {
                    "video_id": r["video_id"],
                    "title": r["title"],
                    "genre": r["genre"],
                    "mood": r["mood"],
                    "era": r["era"],
                    "year": r["year"],
                    "synopsis": r["synopsis"],
                    "duration_seconds": r["duration_seconds"],
                    "thumbnail_url": r["thumbnail_url"],
                }
            )

        return CatalogSearchResult(snapshot_id=snapshot_id, items=items, total=total)
