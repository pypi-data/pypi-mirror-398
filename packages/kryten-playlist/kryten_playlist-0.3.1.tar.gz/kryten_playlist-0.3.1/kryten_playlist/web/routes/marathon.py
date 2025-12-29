"""Marathon generation API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from kryten_playlist.marathon import (
    MarathonItem,
    MarathonSource,
    generate_marathon,
)
from kryten_playlist.nats.kv import BUCKET_PLAYLISTS
from kryten_playlist.web.deps import Session, get_kv, require_blessed, require_session

router = APIRouter()


class MarathonSourceIn(BaseModel):
    label: str = Field(..., min_length=1, max_length=1, pattern=r"^[A-Za-z]$")
    playlist_id: str


class MarathonGenerateIn(BaseModel):
    sources: list[MarathonSourceIn] = Field(..., min_items=1)
    method: str = "concatenate"
    shuffle_seed: str | None = None
    interleave_pattern: str | None = None
    preserve_episode_order: bool = False


class MarathonItemOut(BaseModel):
    video_id: str
    title: str


class MarathonGenerateOut(BaseModel):
    items: list[MarathonItemOut]
    warnings: list[str]


@router.post("/generate", response_model=MarathonGenerateOut)
async def generate_marathon_endpoint(
    payload: MarathonGenerateIn,
    session: Session = Depends(require_session),
    kv=Depends(get_kv),
) -> MarathonGenerateOut:
    """Generate a marathon from multiple playlists."""
    require_blessed(session)

    sources: list[MarathonSource] = []
    for src_in in payload.sources:
        doc = await kv.get_json(BUCKET_PLAYLISTS, f"playlists/{src_in.playlist_id}")
        if not doc:
            raise HTTPException(status_code=404, detail=f"Playlist {src_in.playlist_id} not found")

        items = [
            MarathonItem(video_id=it.get("video_id", ""), title=it.get("title", it.get("video_id", "")))
            for it in (doc.get("items") or [])
            if isinstance(it, dict) and it.get("video_id")
        ]
        sources.append(MarathonSource(label=src_in.label.upper(), items=items))

    result = generate_marathon(
        sources,
        method=payload.method,
        shuffle_seed=payload.shuffle_seed,
        interleave_pattern=payload.interleave_pattern,
        preserve_episode_order=payload.preserve_episode_order,
    )

    return MarathonGenerateOut(
        items=[MarathonItemOut(video_id=it.video_id, title=it.title) for it in result.items],
        warnings=result.warnings,
    )


class MarathonSaveIn(BaseModel):
    name: str = Field(..., min_length=1)
    items: list[MarathonItemOut]


class MarathonSaveOut(BaseModel):
    playlist_id: str


@router.post("/save", response_model=MarathonSaveOut)
async def save_marathon_as_playlist(
    payload: MarathonSaveIn,
    session: Session = Depends(require_session),
    kv=Depends(get_kv),
) -> MarathonSaveOut:
    """Save generated marathon items as a new playlist."""
    require_blessed(session)

    from kryten_playlist.domain.schemas import PlaylistCreateIn, PlaylistItemIn
    from kryten_playlist.web.routes.playlists import create_playlist

    # Delegate to existing create_playlist logic
    create_in = PlaylistCreateIn(
        name=payload.name,
        items=[PlaylistItemIn(video_id=it.video_id) for it in payload.items],
    )

    # We need to pass the session and kv manually
    result = await create_playlist(create_in, session, kv)
    return MarathonSaveOut(playlist_id=result.playlist_id)
