from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from kryten_playlist.nats.kv import BUCKET_ACL, BUCKET_SNAPSHOT, KvJson


def _normalize_username(username: str) -> str:
    return str(username or "").strip()


def _as_list(doc: Any) -> list[str]:
    if isinstance(doc, list):
        return [str(x) for x in doc]
    if isinstance(doc, dict):
        # Historical/alternate shapes supported by resolve_role.
        for k in ("admins", "blessed"):
            v = doc.get(k)
            if isinstance(v, list):
                return [str(x) for x in v]
    return []


async def get_admins(kv: KvJson) -> list[str]:
    return [u.strip() for u in _as_list(await kv.get_json(BUCKET_ACL, "admins")) if str(u).strip()]


async def get_blessed(kv: KvJson) -> list[str]:
    return [u.strip() for u in _as_list(await kv.get_json(BUCKET_ACL, "blessed")) if str(u).strip()]


def _dedupe_preserve_order(names: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for n in names:
        nn = n.strip()
        if not nn or nn in seen:
            continue
        seen.add(nn)
        out.append(nn)
    return out


async def add_blessed(kv: KvJson, username: str) -> list[str]:
    u = _normalize_username(username)
    if not u:
        raise ValueError("username_required")

    blessed = await get_blessed(kv)
    blessed = _dedupe_preserve_order([*blessed, u])
    await kv.put_json(BUCKET_ACL, "blessed", blessed)
    return blessed


async def remove_blessed(kv: KvJson, username: str) -> list[str]:
    u = _normalize_username(username)
    if not u:
        raise ValueError("username_required")

    blessed = await get_blessed(kv)
    blessed = [x for x in blessed if x.strip() != u]
    await kv.put_json(BUCKET_ACL, "blessed", blessed)
    return blessed


async def record_catalog_refresh_request(
    kv: KvJson,
    *,
    requested_by: str,
    correlation_id: str,
) -> dict[str, Any]:
    doc = {
        "requested_by": _normalize_username(requested_by),
        "correlation_id": str(correlation_id or "").strip(),
        "requested_at": datetime.now(timezone.utc).isoformat(),
    }
    await kv.put_json(BUCKET_SNAPSHOT, "catalog_refresh/last", doc)
    return doc
