from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from kryten_playlist.nats.kv import BUCKET_PLAYLISTS, KvJson
from kryten_playlist.storage.catalog_repo import CatalogRepository
from kryten_playlist.catalog.models import generate_manifest_url


QueueApplyMode = Literal["preserve_current", "append", "hard_replace", "insert_next"]


@dataclass(frozen=True)
class QueueApplyResult:
    status: Literal["ok", "error"]
    enqueued_count: int = 0
    failed: list[dict] | None = None
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "enqueued_count": int(self.enqueued_count or 0),
            "failed": list(self.failed or []),
            "error": self.error,
        }


async def _load_playlist_doc(kv: KvJson, playlist_id: str) -> dict[str, Any] | None:
    pid = (playlist_id or "").strip()
    if not pid:
        return None
    doc = await kv.get_json(BUCKET_PLAYLISTS, f"playlists/{pid}")
    return doc if isinstance(doc, dict) else None


def _extract_video_ids(playlist_doc: dict[str, Any]) -> list[str]:
    items = playlist_doc.get("items")
    if not isinstance(items, list):
        return []

    out: list[str] = []
    for it in items:
        if isinstance(it, dict):
            vid = str(it.get("video_id") or "").strip()
            if vid:
                out.append(vid)
    return out


async def _get_current_uid_from_robot_state(
    client: Any,
    *,
    channel: str,
) -> str | None:
    getter = getattr(client, "get_state_current_uid", None)
    if callable(getter):
        return await getter(channel)
    return None


async def _get_playlist_items_from_robot_state(
    client: Any,
    *,
    channel: str,
) -> list[dict[str, Any]]:
    getter = getattr(client, "get_state_playlist_items", None)
    if callable(getter):
        items = await getter(channel)
        return items if isinstance(items, list) else []
    return []


async def apply_playlist_to_queue(
    *,
    client: Any,
    kv: KvJson,
    sqlite_conn: Any,
    channel: str,
    playlist_id: str,
    mode: QueueApplyMode,
) -> QueueApplyResult:
    playlist_doc = await _load_playlist_doc(kv, playlist_id)
    if not playlist_doc:
        return QueueApplyResult(status="error", error="Playlist not found", failed=[])

    video_ids = _extract_video_ids(playlist_doc)
    if not video_ids:
        return QueueApplyResult(status="ok", enqueued_count=0, failed=[])

    repo = CatalogRepository(sqlite_conn)
    by_id = await repo.get_items_by_video_ids(video_ids)

    failed: list[dict] = []
    manifest_urls: list[str] = []
    for vid in video_ids:
        item = by_id.get(vid)
        
        # If the item is not in the catalog, we might still be able to generate a manifest URL if we trust the video_id.
        # However, it's safer to only allow items that are in our catalog.
        
        if not item:
            failed.append({"video_id": vid, "error": "Item not found in catalog"})
            continue

        manifest_url = generate_manifest_url(vid)
        
        if not manifest_url:
            failed.append({"video_id": vid, "error": "Could not generate manifest URL"})
            continue

        manifest_urls.append(manifest_url)

    # Apply mode behavior
    if mode == "hard_replace":
        await client.send_command(service="robot", type="clear", body={}, channel=channel)

    elif mode == "preserve_current":
        current_uid = await _get_current_uid_from_robot_state(client, channel=channel)
        # If no current item, treat as hard_replace.
        if not current_uid:
            await client.send_command(service="robot", type="clear", body={}, channel=channel)
        else:
            items = await _get_playlist_items_from_robot_state(client, channel=channel)
            for it in items:
                uid = it.get("uid")
                if uid is None:
                    continue
                uid_str = str(uid).strip()
                if not uid_str or uid_str == current_uid:
                    continue
                try:
                    uid_int = int(uid_str)
                except ValueError:
                    failed.append({"video_id": "", "reason": f"cannot_delete_uid:{uid_str}"})
                    continue
                
                await client.send_command(
                    service="robot",
                    type="rmvideo",
                    body={"uid": uid_int},
                    channel=channel
                )

    # mode == "append" => nothing to do before enqueue

    position = "end"
    if mode == "insert_next":
        manifest_urls.reverse()
        position = "next"

    enqueued = 0
    for url in manifest_urls:
        # MediaCMS items are queued as custom media (cm) using a manifest URL.
        await client.send_command(
            service="robot",
            type="addvideo",
            body={
                "type": "cm",
                "id": url,
                "pos": position,
                "temp": False
            },
            channel=channel
        )
        enqueued += 1

    return QueueApplyResult(
        status="ok",
        enqueued_count=enqueued,
        failed=failed,
    )
