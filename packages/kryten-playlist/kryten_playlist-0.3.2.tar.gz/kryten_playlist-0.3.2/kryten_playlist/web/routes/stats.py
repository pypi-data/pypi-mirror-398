"""Stats and Likes API routes."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from kryten_playlist.domain.schemas import (
    CurrentVideoOut,
    LikeCurrentOut,
    StatsItemOut,
    TopLikedOut,
    TopPlayedOut,
)
from kryten_playlist.nats.kv import BUCKET_ANALYTICS, BUCKET_LIKES, KvJson
from kryten_playlist.storage.catalog_repo import CatalogRepository
from kryten_playlist.web.deps import Session, get_kv, get_sqlite, require_session

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _isoformat(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


async def _get_current_video(kv: KvJson) -> dict[str, Any] | None:
    """Get current playing video from state KV."""
    doc = await kv.get_json(BUCKET_ANALYTICS, "current_video")
    return doc if isinstance(doc, dict) else None


async def _get_play_counts(kv: KvJson) -> dict[str, int]:
    """Get all play counts."""
    doc = await kv.get_json(BUCKET_ANALYTICS, "play_counts")
    return doc if isinstance(doc, dict) else {}


async def _set_play_counts(kv: KvJson, counts: dict[str, int]) -> None:
    await kv.put_json(BUCKET_ANALYTICS, "play_counts", counts)


async def _get_like_counts(kv: KvJson) -> dict[str, int]:
    """Get all like counts."""
    doc = await kv.get_json(BUCKET_LIKES, "like_counts")
    return doc if isinstance(doc, dict) else {}


async def _set_like_counts(kv: KvJson, counts: dict[str, int]) -> None:
    await kv.put_json(BUCKET_LIKES, "like_counts", counts)


async def _get_user_like_key(kv: KvJson, username: str, video_id: str) -> dict[str, Any] | None:
    """Check if user already liked this video recently."""
    doc = await kv.get_json(BUCKET_LIKES, f"user_likes/{username}/{video_id}")
    return doc if isinstance(doc, dict) else None


async def _set_user_like_key(kv: KvJson, username: str, video_id: str, expires_at: str) -> None:
    await kv.put_json(BUCKET_LIKES, f"user_likes/{username}/{video_id}", {
        "liked_at": _isoformat(_utcnow()),
        "expires_at": expires_at,
    })


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/current", response_model=CurrentVideoOut)
async def get_current_video(
    request: Request,
    session: Session = Depends(require_session),
    kv: KvJson = Depends(get_kv),
) -> CurrentVideoOut:
    """Get the currently playing video."""
    doc = await _get_current_video(kv)
    if not doc:
        return CurrentVideoOut(video_id=None, title=None, playing=False)

    return CurrentVideoOut(
        video_id=doc.get("video_id"),
        title=doc.get("title"),
        playing=True,
    )


@router.post("/like", response_model=LikeCurrentOut)
async def like_current(
    request: Request,
    session: Session = Depends(require_session),
    kv: KvJson = Depends(get_kv),
) -> LikeCurrentOut:
    """Like the currently playing video.

    - Any authenticated user can like
    - Dedupe: same user can't like same video within 24 hours
    """
    current = await _get_current_video(kv)
    if not current or not current.get("video_id"):
        return LikeCurrentOut(
            status="error",
            error="no_current_video",
        )

    video_id = str(current["video_id"])
    username = session.username

    # Check for duplicate within dedupe window (24 hours)
    dedupe_hours = 24
    existing = await _get_user_like_key(kv, username, video_id)
    if existing:
        expires_raw = existing.get("expires_at")
        if expires_raw:
            try:
                expires_at = datetime.fromisoformat(expires_raw)
                if expires_at > _utcnow():
                    # Still within dedupe window
                    counts = await _get_like_counts(kv)
                    return LikeCurrentOut(
                        status="duplicate",
                        video_id=video_id,
                        like_count=counts.get(video_id, 0),
                    )
            except ValueError:
                pass

    # Increment like count
    counts = await _get_like_counts(kv)
    counts[video_id] = counts.get(video_id, 0) + 1
    await _set_like_counts(kv, counts)

    # Record dedupe key
    expires_at = _utcnow() + timedelta(hours=dedupe_hours)
    await _set_user_like_key(kv, username, video_id, _isoformat(expires_at))

    return LikeCurrentOut(
        status="ok",
        video_id=video_id,
        like_count=counts[video_id],
    )


@router.get("/top-played", response_model=TopPlayedOut)
async def top_played(
    request: Request,
    limit: int = 10,
    session: Session = Depends(require_session),
    kv: KvJson = Depends(get_kv),
    sqlite_conn=Depends(get_sqlite),
) -> TopPlayedOut:
    """Get top played videos."""
    if limit < 1:
        limit = 1
    if limit > 50:
        limit = 50

    counts = await _get_play_counts(kv)
    if not counts:
        return TopPlayedOut(items=[])

    # Sort by count descending
    sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    video_ids = [vid for vid, _ in sorted_items]

    # Fetch titles from catalog
    repo = CatalogRepository(sqlite_conn)
    catalog_items = await repo.get_items_by_video_ids(video_ids)

    items: list[StatsItemOut] = []
    for vid, count in sorted_items:
        cat_item = catalog_items.get(vid, {})
        items.append(StatsItemOut(
            video_id=vid,
            title=str(cat_item.get("title") or vid),
            count=count,
            thumbnail_url=cat_item.get("thumbnail_url"),
        ))

    return TopPlayedOut(items=items)


@router.get("/top-liked", response_model=TopLikedOut)
async def top_liked(
    request: Request,
    limit: int = 10,
    session: Session = Depends(require_session),
    kv: KvJson = Depends(get_kv),
    sqlite_conn=Depends(get_sqlite),
) -> TopLikedOut:
    """Get top liked videos."""
    if limit < 1:
        limit = 1
    if limit > 50:
        limit = 50

    counts = await _get_like_counts(kv)
    if not counts:
        return TopLikedOut(items=[])

    # Sort by count descending
    sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    video_ids = [vid for vid, _ in sorted_items]

    # Fetch titles from catalog
    repo = CatalogRepository(sqlite_conn)
    catalog_items = await repo.get_items_by_video_ids(video_ids)

    items: list[StatsItemOut] = []
    for vid, count in sorted_items:
        cat_item = catalog_items.get(vid, {})
        items.append(StatsItemOut(
            video_id=vid,
            title=str(cat_item.get("title") or vid),
            count=count,
            thumbnail_url=cat_item.get("thumbnail_url"),
        ))

    return TopLikedOut(items=items)


# ---------------------------------------------------------------------------
# Internal helpers for service.py to call
# ---------------------------------------------------------------------------


async def increment_play_count(kv: KvJson, video_id: str) -> int:
    """Increment play count for a video. Returns new count."""
    counts = await _get_play_counts(kv)
    counts[video_id] = counts.get(video_id, 0) + 1
    await _set_play_counts(kv, counts)
    return counts[video_id]


async def set_current_video(kv: KvJson, video_id: str, title: str) -> None:
    """Set the currently playing video."""
    await kv.put_json(BUCKET_ANALYTICS, "current_video", {
        "video_id": video_id,
        "title": title,
        "started_at": _isoformat(_utcnow()),
    })


async def clear_current_video(kv: KvJson) -> None:
    """Clear current video when nothing is playing."""
    try:
        await kv.delete(BUCKET_ANALYTICS, "current_video")
    except RuntimeError:
        pass
