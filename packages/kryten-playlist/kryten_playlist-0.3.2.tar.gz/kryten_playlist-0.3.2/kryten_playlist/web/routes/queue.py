from __future__ import annotations

import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Request

from kryten_playlist.domain.schemas import (
    QueueApplyIn,
    QueueApplyOut,
    QueueCurrentOut,
    QueueItemOut,
    QueueMediaOut,
    QueueStateOut,
    QueueMoveIn,
    QueueAddIn,
    QueueAddOut,
)
from kryten_playlist.catalog.models import generate_manifest_url
from kryten_playlist.queue_apply import apply_playlist_to_queue
from kryten_playlist.storage.catalog_repo import CatalogRepository
from kryten_playlist.web.deps import (
    Session,
    get_client,
    get_config,
    get_kv,
    get_service,
    get_sqlite,
    require_admin,
    require_blessed,
    require_session,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=QueueStateOut)
async def get_queue(
    session: Session = Depends(require_session),
    service=Depends(get_service),
    client=Depends(get_client),
) -> QueueStateOut:
    """Get the current CyTube queue (playlist) state."""
    logger.debug(f"DEBUG: get_queue called with session: {session.session_id}, role: {session.role}")
    """Get the current CyTube queue (playlist) state.
    
    Note: The playlist bucket is managed by kryten-robot, not this service.
    We access it directly via the client's kv_get method, not through the
    KvJson wrapper which applies namespace prefixing.
    """
    channel = service.resolved_channel
    if not channel:
        logger.warning("No resolved channel available")
        return QueueStateOut(items=[], current=None, total_seconds=0)

    bucket = f"kryten_{channel}_playlist"
    logger.debug(f"Fetching queue from bucket: {bucket}")

    try:
        # Fetch items and current from KV (directly via client, not KvJson wrapper)
        items_raw = await client.kv_get(bucket, "items", default=[], parse_json=True) or []
        current_raw = await client.kv_get(bucket, "current", default=None, parse_json=True)
        
        logger.debug(f"Fetched {len(items_raw)} items from KV, current={current_raw is not None}")

        # Parse items
        items: list[QueueItemOut] = []
        total_seconds = 0
        for item in items_raw:
            media_data = item.get("media", item)
            media = QueueMediaOut(
                id=str(media_data.get("id", "")),
                title=media_data.get("title", "Unknown"),
                seconds=media_data.get("seconds", 0),
                type=media_data.get("type", ""),
            )
            total_seconds += media.seconds
            items.append(
                QueueItemOut(
                    uid=str(item.get("uid", 0)),
                    media=media,
                    queueby=item.get("queueby", ""),
                    temp=item.get("temp", False),
                )
            )

        # Parse current
        current = None
        if current_raw:
            current = QueueCurrentOut(
                uid=str(current_raw.get("uid")) if current_raw.get("uid") else None,
                id=current_raw.get("id"),
                title=current_raw.get("title"),
                seconds=current_raw.get("seconds"),
                currentTime=current_raw.get("currentTime"),
                paused=current_raw.get("paused", False),
            )

        return QueueStateOut(items=items, current=current, total_seconds=total_seconds)
    except Exception as e:
        logger.exception("Error fetching queue state")
        raise HTTPException(status_code=500, detail=f"Queue fetch error: {str(e)}")


@router.post("/apply", response_model=QueueApplyOut)
async def apply_to_queue(
    payload: QueueApplyIn,
    session: Session = Depends(require_session),
    client=Depends(get_client),
    service=Depends(get_service),
    kv=Depends(get_kv),
    sqlite_conn=Depends(get_sqlite),
) -> QueueApplyOut:
    require_blessed(session)
    if payload.mode == "hard_replace":
        require_admin(session)

    result = await apply_playlist_to_queue(
        client=client,
        kv=kv,
        sqlite_conn=sqlite_conn,
        channel=service.resolved_channel,
        playlist_id=payload.playlist_id,
        mode=payload.mode,
    )

    if result.status != "ok":
        # Keep HTTP semantics consistent with existing endpoints.
        status = 404 if (result.error or "").lower().strip() == "playlist not found" else 400
        raise HTTPException(status_code=status, detail=result.error or "Queue apply failed")

    return QueueApplyOut(
        status="ok",
        enqueued_count=result.enqueued_count,
        failed=result.failed or [],
    )


@router.post("/add", response_model=QueueAddOut)
async def add_to_queue(
    payload: QueueAddIn,
    session: Session = Depends(require_blessed),
    client=Depends(get_client),
    service=Depends(get_service),
    sqlite=Depends(get_sqlite),
) -> QueueAddOut:
    """Add a single item to the queue."""
    channel = service.resolved_channel
    if not channel:
        raise HTTPException(status_code=503, detail="No resolved channel")

    repo = CatalogRepository(sqlite)
    try:
        item = await repo.get_item(payload.video_id)
    except Exception as e:
        logger.exception(f"Error fetching item {payload.video_id} from catalog")
        raise HTTPException(status_code=500, detail=f"Catalog error: {str(e)}")
    
    if not item:
        return QueueAddOut(status="error", error="Item not found")

    manifest_url = generate_manifest_url(item["video_id"])
    
    if not manifest_url:
        return QueueAddOut(status="error", error="Could not generate manifest URL")
    
    # "next" position means "after current"
    # client.add_media handles "next" correctly if supported, or we use "end"
    position = payload.position
    
    try:
        await client.add_media(channel, "cm", manifest_url, position=position)
    except Exception as e:
        logger.exception(f"Error adding media {payload.video_id} to queue")
        raise HTTPException(status_code=500, detail=f"Robot error: {str(e)}")
    
    return QueueAddOut(status="ok")


@router.post("/move")
async def move_queue_item(
    payload: QueueMoveIn = Body(...),
    session: Session = Depends(require_blessed),
    client=Depends(get_client),
    service=Depends(get_service),
):
    """Move an item in the queue."""
    # print(f"DEBUG: move_queue_item called with payload: {payload}")
    # raise Exception("DEBUG: Forced exception to verify execution")
    try:
        channel = service.resolved_channel
        if not channel:
            raise HTTPException(status_code=503, detail="No resolved channel")

        # Resolve inputs - payload.uid is the CyTube UID of the item to move
        uid_to_move = payload.uid
        logger.debug(f"Move request received - uid: {uid_to_move}, after_uid: {payload.after_uid}")
        
        if not uid_to_move:
            raise HTTPException(status_code=400, detail="Missing uid parameter")
        
        # Validate UID is a valid integer
        try:
            uid_int = int(uid_to_move)
            if uid_int < 0:
                raise ValueError("UID must be non-negative")
        except ValueError:
            logger.warning(f"Invalid UID: {uid_to_move}")
            raise HTTPException(status_code=400, detail="Invalid UID format")

        # Handle after_uid - can be a UID string, "prepend", or None/null
        after_uid = payload.after_uid
        after_uid_int = None
        if after_uid is not None and after_uid != "prepend":
            try:
                after_uid_int = int(after_uid)
                if after_uid_int < 0:
                    raise ValueError("After UID must be non-negative")
            except ValueError:
                logger.warning(f"Invalid after_uid: {after_uid}")
                raise HTTPException(status_code=400, detail="Invalid after_uid format")

        # Pass the after_uid directly to client.move_media
        # The client and robot expect 'after' to be a UID (int) or "prepend" (str)
        # Note: client.move_media argument is named 'position' but maps to 'after' in the payload
        
        target = "prepend"
        if after_uid_int is not None:
            target = after_uid_int
        elif after_uid == "prepend":
            target = "prepend"
            
        logger.debug(f"Moving item with UID {uid_int} after {target} on channel {channel}")
        try:
            await client.move_media(channel, uid_int, target)
            logger.debug(f"Move command sent for UID {uid_int} after {target}")
        except Exception as e:
            logger.exception(f"Error moving item with UID {uid_int}")
            raise HTTPException(status_code=500, detail=f"Robot error: {str(e)}")

        return {"status": "ok"}
    except Exception as e:
        logger.exception(f"Exception in move_queue_item: {e}")
        raise


@router.delete("/clear")
async def clear_queue(
    session: Session = Depends(require_admin),
    client=Depends(get_client),
    service=Depends(get_service),
):
    """Clear the entire queue."""
    channel = service.resolved_channel
    if not channel:
        raise HTTPException(status_code=503, detail="No resolved channel")

    logger.debug(f"Clearing queue for channel {channel}")
    await client.clear_playlist(channel)
    return {"status": "ok"}


@router.delete("/{uid}")
async def remove_queue_item(
    uid: str,
    session: Session = Depends(require_blessed),
    client=Depends(get_client),
    service=Depends(get_service),
):
    """Remove an item from the queue by its UID."""
    channel = service.resolved_channel
    if not channel:
        raise HTTPException(status_code=503, detail="No resolved channel")

    logger.debug(f"Removing queue item with UID {uid} from channel {channel}")
    
    # Validate UID is a valid integer
    try:
        uid_int = int(uid)
        if uid_int < 0:
            raise ValueError("UID must be non-negative")
    except ValueError:
        logger.warning(f"Invalid UID: {uid}")
        raise HTTPException(status_code=400, detail="Invalid UID format")

    logger.debug(f"Sending delete_media for UID {uid_int}")
    try:
        await client.delete_media(channel, uid_int)
        logger.debug(f"Delete command sent for UID {uid_int}")
    except Exception as e:
        logger.exception(f"Error deleting item with UID {uid_int}")
        raise HTTPException(status_code=500, detail=f"Robot error: {str(e)}")

    return {"status": "ok"}

