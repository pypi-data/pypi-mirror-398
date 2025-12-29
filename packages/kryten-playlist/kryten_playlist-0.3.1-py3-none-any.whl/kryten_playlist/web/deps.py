from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, HTTPException, Request

logger = logging.getLogger(__name__)

from kryten_playlist.auth.otp import parse_iso, utcnow
from kryten_playlist.domain.schemas import Role
from kryten_playlist.nats.kv import BUCKET_ACL, BUCKET_AUTH, KvJson


@dataclass(frozen=True)
class Session:
    session_id: str
    username: str
    role: Role
    expires_at: datetime


def get_config(request: Request) -> Any:
    cfg = getattr(request.app.state, "config", None)
    logger.debug(f"DEBUG: get_config called, cfg: {cfg}")
    if cfg is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    logger.debug(f"DEBUG: config.disable_auth: {cfg.disable_auth}")
    return cfg


def get_service(request: Request) -> Any:
    """Get the PlaylistService instance for resolved channel access."""
    service = getattr(request.app.state, "service", None)
    if service is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    return service


def get_client(request: Request) -> Any:
    client = getattr(request.app.state, "client", None)
    if client is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    return client


def get_kv(request: Request) -> KvJson:
    kv = getattr(request.app.state, "kv", None)
    if kv is None:
        raise HTTPException(status_code=503, detail="KV not initialized")
    return kv


def get_sqlite(request: Request) -> Any:
    conn = getattr(request.app.state, "sqlite", None)
    if conn is None:
        raise HTTPException(status_code=503, detail="SQLite not initialized")
    return conn


def get_request_ip(request: Request) -> str:
    # For now, trust direct client connection.
    host = request.client.host if request.client else ""
    return host or "0.0.0.0"


async def is_ip_blocked(request: Request, kv: KvJson) -> tuple[bool, int]:
    ip = get_request_ip(request)
    doc = await kv.get_json(BUCKET_AUTH, f"ipblock/{ip}")
    if not doc:
        return False, 0

    blocked_until_raw = doc.get("blocked_until")
    if not blocked_until_raw:
        return False, 0

    blocked_until = parse_iso(blocked_until_raw)
    now = utcnow()
    if blocked_until <= now:
        # Expired; best-effort cleanup.
        try:
            await kv.delete(BUCKET_AUTH, f"ipblock/{ip}")
        except RuntimeError:
            pass
        return False, 0

    retry_after = int((blocked_until - now).total_seconds())
    return True, max(1, retry_after)


async def get_current_session(request: Request, kv: KvJson) -> Session:
    session_id = request.cookies.get("kryten_playlist_session")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    doc = await kv.get_json(BUCKET_AUTH, f"session/{session_id}")
    if not doc:
        raise HTTPException(status_code=401, detail="Not authenticated")

    expires_at_raw = doc.get("expires_at")
    if not expires_at_raw:
        raise HTTPException(status_code=401, detail="Not authenticated")

    exp = parse_iso(expires_at_raw)
    now = utcnow()
    if exp <= now:
        try:
            await kv.delete(BUCKET_AUTH, f"session/{session_id}")
        except RuntimeError:
            pass
        raise HTTPException(status_code=401, detail="Session expired")

    role = doc.get("role") or "viewer"
    if role not in ("viewer", "blessed", "admin"):
        role = "viewer"

    return Session(
        session_id=session_id,
        username=str(doc.get("username") or ""),
        role=role,  # type: ignore[assignment]
        expires_at=exp,
    )


async def require_session(request: Request) -> Session:
    config = get_config(request)
    
    # Check if authentication is disabled for testing
    logger.debug(f"DEBUG: disable_auth config value: {config.disable_auth}")
    if config.disable_auth:
        logger.debug("DEBUG: Authentication disabled, returning test session")
        # Return a mock session for testing
        return Session(
            session_id="test_session",
            username="test_user",
            role="admin",  # Give admin privileges for testing
            expires_at=datetime.now(timezone.utc).replace(year=2099)  # Far future expiry
        )
    
    logger.debug("DEBUG: Authentication enabled, proceeding with normal auth")
    kv = get_kv(request)
    return await get_current_session(request, kv)


def require_role(session: Session, allowed: set[Role]) -> Session:
    if session.role not in allowed:
        raise HTTPException(status_code=403, detail="Forbidden")
    return session


def require_blessed(session: Session = Depends(require_session)) -> Session:
    logger.debug(f"DEBUG: require_blessed called with session: {session.session_id}, role: {session.role}")
    return require_role(session, {"blessed", "admin"})


def require_admin(session: Session = Depends(require_session)) -> Session:
    return require_role(session, {"admin"})


async def get_user_from_channel_userlist(
    channel: str,
    username: str,
    client: Any,
) -> dict[str, Any] | None:
    """Look up a user in the channel's userlist from KV.

    The userlist is maintained by kryten-robot in bucket
    `kryten_{channel}_userlist` with key `users`.

    Args:
        channel: Channel name (e.g., "420grindhouse")
        username: Username to look up
        client: KrytenClient instance for KV access

    Returns:
        User dict with 'name', 'rank', etc. or None if not found
    """
    bucket = f"kryten_{channel}_userlist"
    try:
        users = await client.kv_get(bucket, "users", default=[], parse_json=True)
        if not isinstance(users, list):
            return None

        username_lower = username.strip().lower()
        for user in users:
            if isinstance(user, dict):
                name = user.get("name", "")
                if str(name).strip().lower() == username_lower:
                    return user
        return None
    except Exception:
        return None


def rank_to_role(rank: int, blessed_list: list[str], username: str) -> Role:
    """Map CyTube rank to playlist role.

    CyTube ranks:
      - 5: Channel owner
      - 4: Admin
      - 3: Moderator+
      - 2: Moderator
      - 1: Regular user

    Playlist roles:
      - admin: Rank 4-5 (channel admins/owners)
      - blessed: Rank 2-3 (moderators) OR rank 1 users explicitly in blessed list
      - viewer: Rank 1 users not in blessed list
    """
    if rank >= 4:
        return "admin"
    if rank >= 2:
        return "blessed"
    # Rank 1: check if explicitly blessed
    username_norm = username.strip().lower()
    if any(str(u).strip().lower() == username_norm for u in blessed_list or []):
        return "blessed"
    return "viewer"


async def resolve_role_from_userlist(
    username: str,
    channel: str,
    client: Any,
    kv: KvJson,
) -> Role | None:
    """Resolve user role from channel userlist and blessed list.

    Returns None if user is not in the channel userlist (should deny access).

    Args:
        username: CyTube username
        channel: Channel name
        client: KrytenClient for KV access
        kv: Playlist KV store for blessed list

    Returns:
        Role or None if user not in channel
    """
    # First, check if user is an Admin in the ACL
    # Admins are allowed to login even if not currently in the channel (e.g. maintenance)
    admins = await kv.get_json(BUCKET_ACL, "admins")
    admin_list = admins if isinstance(admins, list) else (
        admins.get("admins") if isinstance(admins, dict) else []
    )
    username_norm = username.strip().lower()
    if any(str(u).strip().lower() == username_norm for u in admin_list or []):
        return "admin"

    # Get user from channel userlist
    user = await get_user_from_channel_userlist(channel, username, client)
    if user is None:
        return None

    rank = user.get("rank", 1)
    if not isinstance(rank, int):
        try:
            rank = int(rank)
        except (ValueError, TypeError):
            rank = 1

    # Get blessed list for rank 1 users who may have been explicitly granted access
    blessed = await kv.get_json(BUCKET_ACL, "blessed")
    blessed_list = blessed if isinstance(blessed, list) else (
        blessed.get("blessed") if isinstance(blessed, dict) else []
    )

    return rank_to_role(rank, blessed_list, username)


async def resolve_role(username: str, kv: KvJson) -> Role:
    """Legacy role resolution from ACL lists only.

    Used for session role lookup (user already authenticated).
    For OTP requests, use resolve_role_from_userlist instead.
    """
    admins = await kv.get_json(BUCKET_ACL, "admins")
    blessed = await kv.get_json(BUCKET_ACL, "blessed")

    admin_list = admins if isinstance(admins, list) else (admins.get("admins") if isinstance(admins, dict) else [])
    blessed_list = blessed if isinstance(blessed, list) else (blessed.get("blessed") if isinstance(blessed, dict) else [])

    username_norm = username.strip()
    if any(str(u).strip() == username_norm for u in admin_list or []):
        return "admin"
    if any(str(u).strip() == username_norm for u in blessed_list or []):
        return "blessed"
    return "viewer"


def cookie_is_secure(request: Request) -> bool:
    # Avoid setting Secure cookies on http://localhost.
    return request.url.scheme == "https"


def as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
