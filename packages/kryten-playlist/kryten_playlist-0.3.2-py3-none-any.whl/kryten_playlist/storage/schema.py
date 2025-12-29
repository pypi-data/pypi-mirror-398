from __future__ import annotations

import aiosqlite


async def init_catalog_schema(conn: aiosqlite.Connection) -> None:
    """Initialize catalog schema.
    
    Supports two database schemas:
    1. Legacy: title, categories_json, manifest_url columns
    2. Enriched (kryten-llm): raw_title, sanitized_title, genre, etc.
    
    For enriched databases, the FTS table catalog_fts is already present.
    """
    # Check if catalog_item table already exists with the enriched schema
    cursor = await conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='catalog_item'"
    )
    table_exists = await cursor.fetchone()
    
    if table_exists:
        # Table exists - check if it has the enriched schema (sanitized_title column)
        pragma_cursor = await conn.execute("PRAGMA table_info(catalog_item)")
        columns = {row[1] for row in await pragma_cursor.fetchall()}
        
        if "sanitized_title" in columns:
            # Enriched schema from kryten-llm - create index on sanitized_title if needed
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_catalog_sanitized_title ON catalog_item(sanitized_title)"
            )
        else:
            # Legacy schema - create index on title
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_catalog_title ON catalog_item(title)"
            )
    else:
        # Create legacy schema for new databases
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS catalog_item (
                video_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                categories_json TEXT NOT NULL,
                manifest_url TEXT NOT NULL,
                duration_seconds INTEGER NULL,
                thumbnail_url TEXT NULL,
                snapshot_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                mediacms_category TEXT NULL
            )
            """
        )
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_catalog_title ON catalog_item(title)")
    
    # Check if mediacms_category column exists in existing table (migration)
    cursor = await conn.execute("PRAGMA table_info(catalog_item)")
    columns = {row[1] for row in await cursor.fetchall()}
    
    if "mediacms_category" not in columns:
        await conn.execute("ALTER TABLE catalog_item ADD COLUMN mediacms_category TEXT NULL")
        # Create index for filtering by category
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_catalog_mediacms_category ON catalog_item(mediacms_category)")

    await conn.execute("CREATE INDEX IF NOT EXISTS idx_catalog_snapshot ON catalog_item(snapshot_id)")

    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS catalog_category (
            category TEXT PRIMARY KEY
        )
        """
    )

    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS catalog_item_category (
            video_id TEXT NOT NULL,
            category TEXT NOT NULL,
            PRIMARY KEY (video_id, category),
            FOREIGN KEY (video_id) REFERENCES catalog_item(video_id) ON DELETE CASCADE,
            FOREIGN KEY (category) REFERENCES catalog_category(category) ON DELETE CASCADE
        )
        """
    )

    await conn.commit()
