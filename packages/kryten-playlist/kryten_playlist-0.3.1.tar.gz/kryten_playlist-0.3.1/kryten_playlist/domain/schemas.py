from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

Role = Literal["viewer", "blessed", "admin"]
Visibility = Literal["private", "shared", "public"]


class ErrorEnvelope(BaseModel):
    error: dict


class OtpRequestIn(BaseModel):
    username: str = Field(min_length=1)


class OtpRequestOut(BaseModel):
    status: Literal["sent"]
    expires_in_seconds: int


class OtpVerifyIn(BaseModel):
    username: str = Field(min_length=1)
    otp: str = Field(min_length=1)


class OtpVerifyOkOut(BaseModel):
    status: Literal["ok"]
    role: Role


class OtpVerifyUnrequestedOut(BaseModel):
    status: Literal["unrequested"]
    can_block_ip: bool
    default_block_hours: int


class OtpVerifyInvalidOut(BaseModel):
    status: Literal["invalid"]
    attempts_remaining: int


class OtpVerifyLockedOut(BaseModel):
    status: Literal["locked"]
    retry_after_seconds: int


class IpBlockIn(BaseModel):
    action: Literal["block"]
    hours: int = Field(ge=1, le=24 * 30)


class IpBlockOut(BaseModel):
    status: Literal["blocked"]
    blocked_until: datetime


class SessionOut(BaseModel):
    username: str
    role: Role
    expires_at: str


class CatalogItemOut(BaseModel):
    video_id: str
    title: str
    genre: Optional[str] = None
    mood: Optional[str] = None
    era: Optional[str] = None
    year: Optional[int] = None
    synopsis: Optional[str] = None
    duration_seconds: Optional[int] = None
    thumbnail_url: Optional[str] = None


class CatalogSearchOut(BaseModel):
    snapshot_id: str
    items: list[CatalogItemOut]
    total: int


class CategoriesOut(BaseModel):
    categories: list[str]


class PendingCountOut(BaseModel):
    count: int



# ---------------------------------------------------------------------------
# Playlist Schemas (Schema Version 2)
# ---------------------------------------------------------------------------


class ForkedFromOut(BaseModel):
    """Attribution for forked playlists."""
    playlist_id: str
    owner: str
    forked_at: datetime


class PlaylistRefOut(BaseModel):
    """Playlist list item with visibility and owner."""
    playlist_id: str
    name: str
    visibility: Visibility = "private"
    owner: str = ""
    item_count: int = 0
    forked_from_owner: Optional[str] = None
    updated_at: datetime


class PlaylistIndexOut(BaseModel):
    playlists: list[PlaylistRefOut]
    total: int = 0


class PlaylistItemIn(BaseModel):
    video_id: str


class PlaylistItemOut(BaseModel):
    """Playlist item with optional cached metadata."""
    video_id: str
    title: Optional[str] = None
    duration_seconds: Optional[int] = None


class PlaylistDetailOut(BaseModel):
    """Full playlist document for GET /playlists/{id}."""
    playlist_id: str
    name: str
    visibility: Visibility = "private"
    owner: str = ""
    items: list[PlaylistItemOut] = Field(default_factory=list)
    forked_from: Optional[ForkedFromOut] = None
    created_by: str = ""
    created_at: datetime
    updated_at: datetime
    schema_version: int = 2


class PlaylistCreateIn(BaseModel):
    """Request body for creating a playlist."""
    name: str = Field(min_length=1, max_length=200)
    visibility: Visibility = "private"
    items: list[PlaylistItemIn] = Field(default_factory=list)


class PlaylistUpdateIn(BaseModel):
    """Request body for updating a playlist (partial updates allowed)."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    visibility: Optional[Visibility] = None
    items: Optional[list[PlaylistItemIn]] = None


class PlaylistForkIn(BaseModel):
    """Request body for forking a playlist."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)


class PlaylistCreateOut(BaseModel):
    playlist_id: str


class QueueApplyIn(BaseModel):
    playlist_id: str
    mode: Literal["preserve_current", "append", "hard_replace", "insert_next"]


class QueueApplyOut(BaseModel):
    status: Literal["ok", "error"]
    enqueued_count: int = 0
    failed: list[dict] = Field(default_factory=list)
    error: Optional[str] = None


class QueueMoveIn(BaseModel):
    uid: int | str
    after_uid: int | str | None = None


class QueueAddIn(BaseModel):
    video_id: str
    position: Literal["end", "next"] = "end"


class QueueAddOut(BaseModel):
    status: Literal["ok", "error"]
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Analytics & Likes
# ---------------------------------------------------------------------------


class LikeCurrentOut(BaseModel):
    status: Literal["ok", "duplicate", "error"]
    video_id: Optional[str] = None
    like_count: int = 0
    error: Optional[str] = None


class StatsItemOut(BaseModel):
    video_id: str
    title: str
    count: int
    thumbnail_url: Optional[str] = None


class TopPlayedOut(BaseModel):
    items: list[StatsItemOut]


class TopLikedOut(BaseModel):
    items: list[StatsItemOut]


class CurrentVideoOut(BaseModel):
    video_id: Optional[str] = None
    title: Optional[str] = None
    playing: bool = False


# ---------------------------------------------------------------------------
# Queue (CyTube Playlist) Schemas
# ---------------------------------------------------------------------------


class QueueMediaOut(BaseModel):
    """Media object within a queue item."""
    id: str = ""
    title: str = ""
    seconds: int = 0
    type: str = ""


class QueueItemOut(BaseModel):
    """Single item in the CyTube queue."""
    uid: str
    media: QueueMediaOut
    queueby: str = ""
    temp: bool = False


class QueueCurrentOut(BaseModel):
    """Currently playing media info."""
    uid: Optional[str] = None
    id: Optional[str] = None
    title: Optional[str] = None
    seconds: Optional[int] = None
    currentTime: Optional[float] = None
    paused: bool = False


class QueueStateOut(BaseModel):
    """Full queue state response."""
    items: list[QueueItemOut] = Field(default_factory=list)
    current: Optional[QueueCurrentOut] = None
    total_seconds: int = 0

