from __future__ import annotations

import secrets
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from kryten_playlist.domain.schemas import (
    PlaylistCreateIn,
    PlaylistCreateOut,
    PlaylistDetailOut,
    PlaylistForkIn,
    PlaylistIndexOut,
    PlaylistItemOut,
    PlaylistRefOut,
    PlaylistUpdateIn,
    Visibility,
)
from kryten_playlist.auth.otp import isoformat, parse_iso, utcnow
from kryten_playlist.nats.kv import BUCKET_PLAYLISTS
from kryten_playlist.web.deps import Session, get_kv, get_sqlite, require_blessed, require_session
from kryten_playlist.storage.catalog_repo import CatalogRepository

router = APIRouter()

# Schema version for new playlists
CURRENT_SCHEMA_VERSION = 2


def _can_view_playlist(meta: dict, session: Session) -> bool:
    """Check if user can view this playlist based on visibility."""
    visibility = meta.get("visibility", "private")
    owner = meta.get("owner") or meta.get("created_by", "")
    
    # Owner can always view
    if owner == session.username:
        return True
    # Private playlists are owner-only
    if visibility == "private":
        return False
    # Shared and public are visible to blessed/admin
    return True


def _can_edit_playlist(meta: dict, session: Session) -> bool:
    """Check if user can edit/delete this playlist. Only owner can edit."""
    owner = meta.get("owner") or meta.get("created_by", "")
    return owner == session.username


@router.get("", response_model=PlaylistIndexOut)
async def list_playlists(
    visibility: Optional[Visibility] = Query(None, description="Filter by visibility"),
    owner: Optional[str] = Query(None, description="Filter by owner username"),
    mine: bool = Query(False, description="Show only my playlists"),
    session: Session = Depends(require_session),
    kv=Depends(get_kv),
) -> PlaylistIndexOut:
    """List playlists with optional filtering by visibility and owner."""
    index = await kv.get_json(BUCKET_PLAYLISTS, "playlists/index")
    playlists: dict[str, Any] = {}
    if isinstance(index, dict):
        playlists = index.get("playlists") or {}

    refs = []
    for playlist_id, meta in (playlists or {}).items():
        if not isinstance(meta, dict):
            continue
        
        # Apply visibility filter based on access control
        if not _can_view_playlist(meta, session):
            continue
        
        # Apply query filters
        if mine and (meta.get("owner") or meta.get("created_by", "")) != session.username:
            continue
        if owner and (meta.get("owner") or meta.get("created_by", "")) != owner:
            continue
        if visibility and meta.get("visibility", "private") != visibility:
            continue
        
        updated_raw = meta.get("updated_at") or meta.get("created_at")
        try:
            updated_at = parse_iso(updated_raw) if isinstance(updated_raw, str) else utcnow()
        except ValueError:
            updated_at = utcnow()
        refs.append(
            PlaylistRefOut(
                playlist_id=str(playlist_id),
                name=str(meta.get("name") or ""),
                visibility=meta.get("visibility", "private"),
                owner=meta.get("owner") or meta.get("created_by", ""),
                item_count=int(meta.get("item_count", 0)),
                forked_from_owner=meta.get("forked_from_owner"),
                updated_at=updated_at,
            )
        )

    refs.sort(key=lambda r: r.updated_at, reverse=True)
    return PlaylistIndexOut(playlists=refs, total=len(refs))


@router.post("", response_model=PlaylistCreateOut)
async def create_playlist(
    payload: PlaylistCreateIn,
    session: Session = Depends(require_session),
    kv=Depends(get_kv),
) -> PlaylistCreateOut:
    """Create a new playlist with visibility setting."""
    require_blessed(session)

    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Playlist name is required")

    now = utcnow()
    created_at = isoformat(now)

    index = await kv.get_json(BUCKET_PLAYLISTS, "playlists/index")
    if not isinstance(index, dict):
        index = {"playlists": {}, "schema_version": CURRENT_SCHEMA_VERSION}

    playlists: dict[str, Any] = index.get("playlists") or {}
    
    # Enforce uniqueness per owner (not global)
    for meta in playlists.values():
        if not isinstance(meta, dict):
            continue
        meta_owner = meta.get("owner") or meta.get("created_by", "")
        if meta_owner == session.username and str(meta.get("name") or "").strip() == name:
            raise HTTPException(status_code=409, detail="You already have a playlist with this name")

    playlist_id = secrets.token_urlsafe(12)

    playlist_doc = {
        "playlist_id": playlist_id,
        "name": name,
        "visibility": payload.visibility,
        "owner": session.username,
        "items": [{"video_id": it.video_id} for it in payload.items],
        "forked_from": None,
        "created_by": session.username,
        "created_at": created_at,
        "updated_at": created_at,
        "schema_version": CURRENT_SCHEMA_VERSION,
    }

    playlists[playlist_id] = {
        "name": name,
        "visibility": payload.visibility,
        "owner": session.username,
        "created_by": session.username,
        "created_at": created_at,
        "updated_at": created_at,
        "item_count": len(payload.items),
        "forked_from_owner": None,
    }
    index["playlists"] = playlists
    index["schema_version"] = CURRENT_SCHEMA_VERSION

    await kv.put_json(BUCKET_PLAYLISTS, f"playlists/{playlist_id}", playlist_doc)
    await kv.put_json(BUCKET_PLAYLISTS, "playlists/index", index)

    return PlaylistCreateOut(playlist_id=playlist_id)


@router.get("/{playlist_id}", response_model=PlaylistDetailOut)
async def get_playlist(
    playlist_id: str,
    session: Session = Depends(require_session),
    kv=Depends(get_kv),
    sqlite_conn=Depends(get_sqlite),
) -> PlaylistDetailOut:
    """Get a playlist by ID with visibility enforcement."""
    doc = await kv.get_json(BUCKET_PLAYLISTS, f"playlists/{playlist_id}")
    if not doc:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Check visibility access
    if not _can_view_playlist(doc, session):
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Parse timestamps
    try:
        created_at = parse_iso(doc.get("created_at")) if doc.get("created_at") else utcnow()
    except ValueError:
        created_at = utcnow()
    try:
        updated_at = parse_iso(doc.get("updated_at")) if doc.get("updated_at") else utcnow()
    except ValueError:
        updated_at = utcnow()
    
    # Parse forked_from if present
    forked_from = None
    if doc.get("forked_from"):
        ff = doc["forked_from"]
        try:
            forked_at = parse_iso(ff.get("forked_at")) if ff.get("forked_at") else utcnow()
        except ValueError:
            forked_at = utcnow()
        forked_from = {
            "playlist_id": ff.get("playlist_id", ""),
            "owner": ff.get("owner", ""),
            "forked_at": forked_at,
        }
    
    # Parse items and enrich with catalog metadata
    items = []
    catalog_repo = CatalogRepository(sqlite_conn)
    
    # Get all video IDs from items
    video_ids = []
    for item in doc.get("items", []):
        if isinstance(item, dict) and item.get("video_id"):
            video_ids.append(item["video_id"])
    
    # Fetch catalog metadata for all video IDs
    catalog_items = await catalog_repo.get_items_by_video_ids(video_ids)
    
    # Build enriched items
    for item in doc.get("items", []):
        if isinstance(item, dict):
            video_id = item.get("video_id", "")
            catalog_item = catalog_items.get(video_id, {})
            
            items.append(PlaylistItemOut(
                video_id=video_id,
                title=catalog_item.get("title") or item.get("title") or video_id,
                duration_seconds=catalog_item.get("duration_seconds") or item.get("duration_seconds"),
            ))
    
    return PlaylistDetailOut(
        playlist_id=doc.get("playlist_id", playlist_id),
        name=doc.get("name", ""),
        visibility=doc.get("visibility", "private"),
        owner=doc.get("owner") or doc.get("created_by", ""),
        items=items,
        forked_from=forked_from,
        created_by=doc.get("created_by", ""),
        created_at=created_at,
        updated_at=updated_at,
        schema_version=doc.get("schema_version", 1),
    )


@router.put("/{playlist_id}")
async def update_playlist(
    playlist_id: str,
    payload: PlaylistUpdateIn,
    session: Session = Depends(require_session),
    kv=Depends(get_kv),
):
    """Update a playlist. Only the owner can update."""
    require_blessed(session)

    existing = await kv.get_json(BUCKET_PLAYLISTS, f"playlists/{playlist_id}")
    if not existing:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Only owner can edit
    if not _can_edit_playlist(existing, session):
        raise HTTPException(status_code=403, detail="Only the playlist owner can edit")

    index = await kv.get_json(BUCKET_PLAYLISTS, "playlists/index")
    if not isinstance(index, dict):
        index = {"playlists": {}, "schema_version": CURRENT_SCHEMA_VERSION}
    playlists: dict[str, Any] = index.get("playlists") or {}

    # Handle name update with per-owner uniqueness
    if payload.name is not None:
        name = payload.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Playlist name is required")
        
        old_name = str(existing.get("name") or "").strip()
        if name != old_name:
            for pid, meta in playlists.items():
                if str(pid) == playlist_id:
                    continue
                if not isinstance(meta, dict):
                    continue
                meta_owner = meta.get("owner") or meta.get("created_by", "")
                if meta_owner == session.username and str(meta.get("name") or "").strip() == name:
                    raise HTTPException(status_code=409, detail="You already have a playlist with this name")
        existing["name"] = name

    # Handle visibility update
    if payload.visibility is not None:
        existing["visibility"] = payload.visibility

    # Handle items update
    if payload.items is not None:
        existing["items"] = [{"video_id": it.video_id} for it in payload.items]

    now = utcnow()
    updated_at = isoformat(now)
    existing["updated_at"] = updated_at
    
    # Ensure owner field exists (migration from v1)
    if "owner" not in existing:
        existing["owner"] = existing.get("created_by", session.username)
    if "visibility" not in existing:
        existing["visibility"] = "private"
    existing["schema_version"] = CURRENT_SCHEMA_VERSION

    # Update index entry
    playlists[playlist_id] = {
        "name": existing.get("name", ""),
        "visibility": existing.get("visibility", "private"),
        "owner": existing.get("owner") or existing.get("created_by", ""),
        "created_by": existing.get("created_by") or session.username,
        "created_at": existing.get("created_at") or updated_at,
        "updated_at": updated_at,
        "item_count": len(existing.get("items", [])),
        "forked_from_owner": existing.get("forked_from", {}).get("owner") if existing.get("forked_from") else None,
    }
    index["playlists"] = playlists
    index["schema_version"] = CURRENT_SCHEMA_VERSION

    await kv.put_json(BUCKET_PLAYLISTS, f"playlists/{playlist_id}", existing)
    await kv.put_json(BUCKET_PLAYLISTS, "playlists/index", index)
    return {"status": "ok"}


@router.delete("/{playlist_id}")
async def delete_playlist(
    playlist_id: str,
    session: Session = Depends(require_session),
    kv=Depends(get_kv),
):
    """Delete a playlist. Only the owner can delete."""
    require_blessed(session)

    existing = await kv.get_json(BUCKET_PLAYLISTS, f"playlists/{playlist_id}")
    if not existing:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Only owner can delete
    if not _can_edit_playlist(existing, session):
        raise HTTPException(status_code=403, detail="Only the playlist owner can delete")

    # Best-effort delete doc first.
    await kv.delete(BUCKET_PLAYLISTS, f"playlists/{playlist_id}")

    index = await kv.get_json(BUCKET_PLAYLISTS, "playlists/index")
    if isinstance(index, dict):
        playlists: dict[str, Any] = index.get("playlists") or {}
        if playlist_id in playlists:
            playlists.pop(playlist_id, None)
            index["playlists"] = playlists
            await kv.put_json(BUCKET_PLAYLISTS, "playlists/index", index)

    return {"status": "ok"}


@router.post("/{playlist_id}/fork", response_model=PlaylistCreateOut)
async def fork_playlist(
    playlist_id: str,
    payload: PlaylistForkIn = None,
    session: Session = Depends(require_session),
    kv=Depends(get_kv),
) -> PlaylistCreateOut:
    """Fork a shared/public playlist to create your own editable copy."""
    require_blessed(session)

    # Get the source playlist
    source = await kv.get_json(BUCKET_PLAYLISTS, f"playlists/{playlist_id}")
    if not source:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Check if the playlist is forkable (shared or public, and not your own)
    visibility = source.get("visibility", "private")
    owner = source.get("owner") or source.get("created_by", "")
    
    if owner == session.username:
        raise HTTPException(status_code=400, detail="Cannot fork your own playlist")
    
    if visibility == "private":
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Determine name for the fork
    source_name = source.get("name", "Untitled")
    if payload and payload.name:
        fork_name = payload.name.strip()
    else:
        fork_name = f"{source_name} (fork)"
    
    # Check for name collision with user's existing playlists
    index = await kv.get_json(BUCKET_PLAYLISTS, "playlists/index")
    if not isinstance(index, dict):
        index = {"playlists": {}, "schema_version": CURRENT_SCHEMA_VERSION}
    playlists: dict[str, Any] = index.get("playlists") or {}
    
    base_name = fork_name
    suffix = 1
    while True:
        collision = False
        for meta in playlists.values():
            if not isinstance(meta, dict):
                continue
            meta_owner = meta.get("owner") or meta.get("created_by", "")
            if meta_owner == session.username and str(meta.get("name") or "").strip() == fork_name:
                collision = True
                break
        if not collision:
            break
        suffix += 1
        fork_name = f"{base_name} ({suffix})"
    
    now = utcnow()
    created_at = isoformat(now)
    new_playlist_id = secrets.token_urlsafe(12)

    # Create the forked playlist document
    forked_doc = {
        "playlist_id": new_playlist_id,
        "name": fork_name,
        "visibility": "private",  # Forks start as private
        "owner": session.username,
        "items": source.get("items", []),  # Copy items
        "forked_from": {
            "playlist_id": playlist_id,
            "owner": owner,
            "forked_at": created_at,
        },
        "created_by": session.username,
        "created_at": created_at,
        "updated_at": created_at,
        "schema_version": CURRENT_SCHEMA_VERSION,
    }

    # Update index
    playlists[new_playlist_id] = {
        "name": fork_name,
        "visibility": "private",
        "owner": session.username,
        "created_by": session.username,
        "created_at": created_at,
        "updated_at": created_at,
        "item_count": len(source.get("items", [])),
        "forked_from_owner": owner,
    }
    index["playlists"] = playlists
    index["schema_version"] = CURRENT_SCHEMA_VERSION

    await kv.put_json(BUCKET_PLAYLISTS, f"playlists/{new_playlist_id}", forked_doc)
    await kv.put_json(BUCKET_PLAYLISTS, "playlists/index", index)

    return PlaylistCreateOut(playlist_id=new_playlist_id)
