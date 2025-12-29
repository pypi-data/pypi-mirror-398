"""Data models and connector protocol for catalog refresh."""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Protocol

DEFAULT_MEDIACMS_BASE_URL = "https://www.420grindhouse.com"
VIDEO_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def generate_snapshot_id() -> str:
    """Generate a unique snapshot id (ISO timestamp + random suffix)."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    suffix = secrets.token_hex(3)
    return f"{ts}-{suffix}"


def generate_manifest_url(video_id: str, base_url: str = DEFAULT_MEDIACMS_BASE_URL) -> str | None:
    """Generate a Cytube manifest URL for a given video ID.
    
    Args:
        video_id: The video ID string.
        base_url: The base URL of the MediaCMS instance.
        
    Returns:
        The complete manifest URL string, or None if video_id is invalid.
    """
    vid = (video_id or "").strip()
    if not vid:
        return None
        
    if not VIDEO_ID_PATTERN.match(vid):
        # Invalid format
        return None
        
    base = base_url.rstrip("/")
    return f"{base}/api/v1/media/cytube/{vid}.json?format=json"


@dataclass(frozen=True)
class CatalogItem:
    """A single catalog item as emitted by a connector."""

    video_id: str
    title: str
    categories: list[str] = field(default_factory=list)
    mediacms_category: str | None = None  # The raw MediaCMS category (or primary one)
    sanitized_category: str | None = None # The sanitized category (no numbering)
    duration_seconds: int | None = None
    thumbnail_url: str | None = None

    def manifest_url(self, base_url: str = DEFAULT_MEDIACMS_BASE_URL) -> str | None:
        """Derive Cytube manifest URL from video_id."""
        return generate_manifest_url(self.video_id, base_url)

    def to_dict(self) -> dict[str, Any]:
        return {
            "video_id": self.video_id,
            "title": self.title,
            "categories": list(self.categories),
            "mediacms_category": self.mediacms_category,
            "sanitized_category": self.sanitized_category,
            "duration_seconds": self.duration_seconds,
            "thumbnail_url": self.thumbnail_url,
        }


class CatalogConnector(Protocol):
    """Protocol for catalog connectors that fetch items from a source."""

    async def iter_items(self) -> AsyncIterator[CatalogItem]:
        """Yield catalog items from the underlying source."""
        ...


@dataclass
class SnapshotMetadata:
    """Metadata about a catalog snapshot stored in KV."""

    snapshot_id: str
    source: str = "mediacms"
    created_at: str = field(default_factory=_now_iso)
    item_count: int = 0
    notes: str = ""
    schema_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "source": self.source,
            "created_at": self.created_at,
            "item_count": self.item_count,
            "notes": self.notes,
            "schema_version": self.schema_version,
        }
