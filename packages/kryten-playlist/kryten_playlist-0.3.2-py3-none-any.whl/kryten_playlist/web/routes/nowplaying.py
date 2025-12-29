"""Now Playing API endpoint.

Provides a simple endpoint to get the currently playing item on the channel.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from kryten_playlist.web.deps import (
    Session,
    get_client,
    get_service,
    require_session,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class NowPlayingOut(BaseModel):
    """Current playing item information."""
    uid: Optional[int] = None
    id: Optional[str] = None
    title: Optional[str] = None
    seconds: Optional[int] = None
    currentTime: Optional[float] = None
    paused: bool = False


@router.get("", response_model=Optional[NowPlayingOut])
async def get_nowplaying(
    session: Session = Depends(require_session),
    service=Depends(get_service),
    client=Depends(get_client),
) -> Optional[NowPlayingOut]:
    """Get the currently playing item.
    
    Returns the current item being played on the CyTube channel,
    or null if nothing is playing.
    """
    channel = service.resolved_channel
    if not channel:
        logger.warning("No resolved channel available")
        return None

    bucket = f"kryten_{channel}_playlist"
    
    # Fetch current from KV
    current_raw = await client.kv_get(bucket, "current", default=None, parse_json=True)
    
    if not current_raw:
        return None
    
    return NowPlayingOut(
        uid=current_raw.get("uid"),
        id=current_raw.get("id"),
        title=current_raw.get("title"),
        seconds=current_raw.get("seconds"),
        currentTime=current_raw.get("currentTime"),
        paused=current_raw.get("paused", False),
    )
