from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request

from kryten_playlist.domain.schemas import CatalogItemOut, CatalogSearchOut, CategoriesOut, PendingCountOut
from kryten_playlist.storage.catalog_repo import CatalogRepository
from kryten_playlist.web.deps import get_config, get_sqlite, require_session, Session

router = APIRouter()


@router.get("/pending-count", response_model=PendingCountOut)
async def get_pending_count(
    request: Request,
    session: Optional[Session] = Depends(require_session),
) -> PendingCountOut:
    """Get count of items waiting for enrichment."""
    # Only admins or blessed users typically care, but we'll allow anyone to see the count
    # if it's just for a UI indicator.
    conn = get_sqlite(request)
    repo = CatalogRepository(conn)
    count = await repo.get_pending_count()
    return PendingCountOut(count=count)


@router.get("/search", response_model=CatalogSearchOut)
async def search(
    request: Request,
    q: Optional[str] = None,
    category: list[str] = Query(default=[]),
    series: Optional[str] = None,
    title: Optional[str] = None,
    theme: Optional[str] = None,
    actor: Optional[str] = None,
    director: Optional[str] = None,
    genre: Optional[str] = None,
    mood: Optional[str] = None,
    era: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    session: Optional[Session] = Depends(require_session),
) -> CatalogSearchOut:
    if limit < 1:
        limit = 1
    if limit > 200:
        limit = 200
    if offset < 0:
        offset = 0

    conn = get_sqlite(request)
    repo = CatalogRepository(conn)
    config = get_config(request)

    # Determine access level
    include_uncategorized = False
    if session:
        if session.role == "admin":
            include_uncategorized = True
        elif session.username in config.blessed_users:
            include_uncategorized = True

    res = await repo.search(
        q=q,
        categories=category,
        limit=limit,
        offset=offset,
        series=series,
        title=title,
        theme=theme,
        actor=actor,
        director=director,
        genre=genre,
        mood=mood,
        era=era,
        include_uncategorized=include_uncategorized,
    )

    items: list[CatalogItemOut] = []
    for raw in res.items:
        items.append(
            CatalogItemOut(
                video_id=str(raw.get("video_id") or ""),
                title=str(raw.get("title") or ""),
                genre=raw.get("genre"),
                mood=raw.get("mood"),
                era=raw.get("era"),
                year=raw.get("year"),
                synopsis=raw.get("synopsis"),
                duration_seconds=raw.get("duration_seconds"),
                thumbnail_url=raw.get("thumbnail_url"),
            )
        )

    return CatalogSearchOut(snapshot_id=res.snapshot_id, items=items, total=res.total)

    return CatalogSearchOut(snapshot_id=res.snapshot_id, items=items, total=res.total)


@router.get("/categories", response_model=CategoriesOut)
async def categories(
    request: Request,
) -> CategoriesOut:
    conn = get_sqlite(request)
    repo = CatalogRepository(conn)
    cats = await repo.get_categories()
    return CategoriesOut(categories=cats)
