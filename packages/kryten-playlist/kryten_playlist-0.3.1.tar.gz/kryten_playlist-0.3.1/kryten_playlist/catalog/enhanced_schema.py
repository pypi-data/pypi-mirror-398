"""Enhanced catalog schema with LLM-ready fields.

This module defines the extended SQLite schema for storing enriched catalog data.
"""

from __future__ import annotations

# SQL schema for the enhanced catalog
ENHANCED_SCHEMA = """
-- Core catalog items with enhanced metadata
CREATE TABLE IF NOT EXISTS catalog_item (
    video_id TEXT PRIMARY KEY,

    -- Original data from MediaCMS
    raw_title TEXT NOT NULL,
    thumbnail_url TEXT,
    duration_seconds INTEGER,

    -- Sanitized/parsed title data
    sanitized_title TEXT NOT NULL,
    title_base TEXT NOT NULL,
    year INTEGER,
    season INTEGER,
    episode INTEGER,
    episode_title TEXT,
    is_tv INTEGER NOT NULL DEFAULT 0,

    -- LLM-generated fields (NULL until enriched)
    synopsis TEXT,
    cast_list TEXT,  -- JSON array of names
    director TEXT,
    genre TEXT,  -- Primary genre
    mood TEXT,  -- e.g., "dark", "uplifting", "comedic"
    era TEXT,  -- e.g., "1980s", "2010s", "classic"
    content_rating TEXT,  -- e.g., "PG", "R", "TV-MA"
    llm_notes TEXT,  -- Free-form LLM observations

    -- Scheduling/filtering flags
    weekend_only INTEGER NOT NULL DEFAULT 0,
    prime_time_only INTEGER NOT NULL DEFAULT 0,
    holiday_content INTEGER NOT NULL DEFAULT 0,

    -- Metadata
    snapshot_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    llm_enriched_at TEXT,  -- When LLM fields were populated
    mediacms_category TEXT NULL,  -- Raw category from MediaCMS
    sanitized_category TEXT NULL  -- Sanitized category (removed numbering)
);

-- Categories from MediaCMS
CREATE TABLE IF NOT EXISTS catalog_category (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- Many-to-many: items to categories
CREATE TABLE IF NOT EXISTS catalog_item_category (
    video_id TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    PRIMARY KEY (video_id, category_id),
    FOREIGN KEY (video_id) REFERENCES catalog_item(video_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES catalog_category(id) ON DELETE CASCADE
);

-- Custom tags (LLM-generated or manual)
CREATE TABLE IF NOT EXISTS catalog_tag (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    is_llm_generated INTEGER NOT NULL DEFAULT 0
);

-- Many-to-many: items to tags
CREATE TABLE IF NOT EXISTS catalog_item_tag (
    video_id TEXT NOT NULL,
    tag_id INTEGER NOT NULL,
    confidence REAL,  -- LLM confidence score 0.0-1.0
    PRIMARY KEY (video_id, tag_id),
    FOREIGN KEY (video_id) REFERENCES catalog_item(video_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES catalog_tag(id) ON DELETE CASCADE
);

-- Full-text search virtual table
CREATE VIRTUAL TABLE IF NOT EXISTS catalog_fts USING fts5(
    video_id,
    sanitized_title,
    title_base,
    synopsis,
    cast_list,
    director,
    llm_notes,
    content='catalog_item',
    content_rowid='rowid'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS catalog_fts_insert AFTER INSERT ON catalog_item BEGIN
    INSERT INTO catalog_fts(rowid, video_id, sanitized_title, title_base, synopsis, cast_list, director, llm_notes)
    VALUES (NEW.rowid, NEW.video_id, NEW.sanitized_title, NEW.title_base, NEW.synopsis, NEW.cast_list, NEW.director, NEW.llm_notes);
END;

CREATE TRIGGER IF NOT EXISTS catalog_fts_delete AFTER DELETE ON catalog_item BEGIN
    INSERT INTO catalog_fts(catalog_fts, rowid, video_id, sanitized_title, title_base, synopsis, cast_list, director, llm_notes)
    VALUES ('delete', OLD.rowid, OLD.video_id, OLD.sanitized_title, OLD.title_base, OLD.synopsis, OLD.cast_list, OLD.director, OLD.llm_notes);
END;

CREATE TRIGGER IF NOT EXISTS catalog_fts_update AFTER UPDATE ON catalog_item BEGIN
    INSERT INTO catalog_fts(catalog_fts, rowid, video_id, sanitized_title, title_base, synopsis, cast_list, director, llm_notes)
    VALUES ('delete', OLD.rowid, OLD.video_id, OLD.sanitized_title, OLD.title_base, OLD.synopsis, OLD.cast_list, OLD.director, OLD.llm_notes);
    INSERT INTO catalog_fts(rowid, video_id, sanitized_title, title_base, synopsis, cast_list, director, llm_notes)
    VALUES (NEW.rowid, NEW.video_id, NEW.sanitized_title, NEW.title_base, NEW.synopsis, NEW.cast_list, NEW.director, NEW.llm_notes);
END;

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_catalog_item_is_tv ON catalog_item(is_tv);
CREATE INDEX IF NOT EXISTS idx_catalog_item_year ON catalog_item(year);
CREATE INDEX IF NOT EXISTS idx_catalog_item_season_episode ON catalog_item(title_base, season, episode);
CREATE INDEX IF NOT EXISTS idx_catalog_item_duration ON catalog_item(duration_seconds);
CREATE INDEX IF NOT EXISTS idx_catalog_item_weekend_only ON catalog_item(weekend_only);
CREATE INDEX IF NOT EXISTS idx_catalog_item_era ON catalog_item(era);
CREATE INDEX IF NOT EXISTS idx_catalog_item_genre ON catalog_item(genre);
"""


async def init_enhanced_schema(conn) -> None:
    """Initialize the enhanced catalog schema."""
    await conn.executescript(ENHANCED_SCHEMA)
    
    # Migration: Check for mediacms_category column
    cursor = await conn.execute("PRAGMA table_info(catalog_item)")
    columns = {row[1] for row in await cursor.fetchall()}
    
    if "mediacms_category" not in columns:
        await conn.execute("ALTER TABLE catalog_item ADD COLUMN mediacms_category TEXT NULL")
    
    if "sanitized_category" not in columns:
        await conn.execute("ALTER TABLE catalog_item ADD COLUMN sanitized_category TEXT NULL")
        
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_catalog_item_mediacms_category ON catalog_item(mediacms_category)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_catalog_item_sanitized_category ON catalog_item(sanitized_category)")
    
    await conn.commit()
