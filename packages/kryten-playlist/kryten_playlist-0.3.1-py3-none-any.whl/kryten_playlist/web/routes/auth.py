from __future__ import annotations

from datetime import timedelta
from typing import Union

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from kryten_playlist.auth.otp import (
    OtpPolicy,
    SessionPolicy,
    expires_at,
    generate_otp_code,
    generate_salt,
    hash_otp,
    isoformat,
    parse_iso,
    utcnow,
)
from kryten_playlist.domain.schemas import (
    IpBlockIn,
    IpBlockOut,
    OtpRequestIn,
    OtpRequestOut,
    OtpVerifyIn,
    OtpVerifyInvalidOut,
    OtpVerifyLockedOut,
    OtpVerifyOkOut,
    OtpVerifyUnrequestedOut,
    SessionOut,
)
from kryten_playlist.nats.kv import BUCKET_AUTH
from kryten_playlist.web.deps import (
    cookie_is_secure,
    get_client,
    get_config,
    get_kv,
    get_request_ip,
    get_service,
    is_ip_blocked,
    resolve_role,
    resolve_role_from_userlist,
)

router = APIRouter()


@router.post("/otp/request", response_model=OtpRequestOut)
async def otp_request(
    payload: OtpRequestIn,
    request: Request,
    kv=Depends(get_kv),
    cfg=Depends(get_config),
    client=Depends(get_client),
    service=Depends(get_service),
) -> OtpRequestOut:
    blocked, retry_after = await is_ip_blocked(request, kv)
    if blocked:
        raise HTTPException(
            status_code=403,
            detail=f"IP blocked. Retry after {retry_after}s.",
        )

    username = payload.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")

    # Check if user is in the channel userlist and has sufficient rank
    # This prevents OTP requests from users not currently in the channel
    # or users with rank 1 (regular users) who aren't explicitly blessed
    role = await resolve_role_from_userlist(
        username=username,
        channel=service.resolved_channel,
        client=client,
        kv=kv,
    )

    if role is None:
        # User not in channel - silently deny (return success but don't send OTP)
        # This prevents user enumeration and confusion
        return OtpRequestOut(status="sent", expires_in_seconds=300)

    if role == "viewer":
        # User is in channel but rank 1 and not blessed - silently deny
        return OtpRequestOut(status="sent", expires_in_seconds=300)

    policy = OtpPolicy(
        ttl_seconds=cfg.otp_ttl_seconds,
        max_attempts=3,
        lockout_seconds=cfg.otp_lockout_seconds,
        otp_length=cfg.otp_length,
    )

    otp = generate_otp_code(policy.otp_length)
    salt = generate_salt()
    otp_hash = hash_otp(otp, salt)

    now = utcnow()
    exp = expires_at(now, policy.ttl_seconds)

    await kv.put_json(
        BUCKET_AUTH,
        f"otp/request/{username}",
        {
            "requested_at": isoformat(now),
            "expires_at": isoformat(exp),
            "request_ip": get_request_ip(request),
            "request_user_agent": request.headers.get("user-agent", ""),
            "otp_salt": salt,
            "otp_hash": otp_hash,
            "attempts_remaining": policy.max_attempts,
            "locked_until": None,
            "schema_version": 1,
            "resolved_role": role,  # Store resolved role for session creation
        },
    )

    # Send OTP via Cytube PM using Kryten-Robot command path.
    # Use the resolved channel from robot discovery (standard kryten lifecycle)
    message = f"Your kryten-playlist OTP is: {otp} (expires in {policy.ttl_seconds}s)"
    await client.send_pm(
        service.resolved_channel,
        username,
        message,
        domain=service.resolved_domain,
    )

    return OtpRequestOut(status="sent", expires_in_seconds=policy.ttl_seconds)


@router.post(
    "/otp/verify",
    response_model=Union[
        OtpVerifyOkOut,
        OtpVerifyUnrequestedOut,
        OtpVerifyInvalidOut,
        OtpVerifyLockedOut,
    ],
)
async def otp_verify(
    payload: OtpVerifyIn,
    request: Request,
    response: Response,
    kv=Depends(get_kv),
    cfg=Depends(get_config),
) -> Union[OtpVerifyOkOut, OtpVerifyUnrequestedOut, OtpVerifyInvalidOut, OtpVerifyLockedOut]:
    blocked, retry_after = await is_ip_blocked(request, kv)
    if blocked:
        return OtpVerifyLockedOut(status="locked", retry_after_seconds=retry_after)

    policy = OtpPolicy(
        ttl_seconds=cfg.otp_ttl_seconds,
        max_attempts=3,
        lockout_seconds=cfg.otp_lockout_seconds,
        otp_length=cfg.otp_length,
    )
    session_policy = SessionPolicy(ttl_seconds=cfg.session_ttl_seconds)

    username = payload.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")

    otp_doc = await kv.get_json(BUCKET_AUTH, f"otp/request/{username}")
    if not otp_doc:
        # Unsolicited verification attempt.
        ip = get_request_ip(request)
        now = utcnow()
        intent_exp = now + timedelta(minutes=5)
        await kv.put_json(
            BUCKET_AUTH,
            f"ipblock_intent/{ip}",
            {
                "created_at": isoformat(now),
                "expires_at": isoformat(intent_exp),
                "reason": "otp_unsolicited",
                "schema_version": 1,
            },
        )
        return OtpVerifyUnrequestedOut(
            status="unrequested",
            can_block_ip=True,
            default_block_hours=cfg.otp_unsolicited_block_hours_default,
        )

    now = utcnow()
    exp_raw = otp_doc.get("expires_at")
    if not exp_raw:
        return OtpVerifyLockedOut(status="locked", retry_after_seconds=policy.lockout_seconds)

    exp = parse_iso(exp_raw)
    if exp <= now:
        # Expired.
        try:
            await kv.delete(BUCKET_AUTH, f"otp/request/{username}")
        except Exception:
            pass
        return OtpVerifyLockedOut(status="locked", retry_after_seconds=0)

    locked_until_raw = otp_doc.get("locked_until")
    if locked_until_raw:
        locked_until = parse_iso(locked_until_raw)
        if locked_until > now:
            return OtpVerifyLockedOut(
                status="locked", retry_after_seconds=int((locked_until - now).total_seconds())
            )

    attempts_remaining = int(otp_doc.get("attempts_remaining") or policy.max_attempts)
    if attempts_remaining <= 0:
        locked_until = expires_at(now, policy.lockout_seconds)
        otp_doc["locked_until"] = isoformat(locked_until)
        await kv.put_json(BUCKET_AUTH, f"otp/request/{username}", otp_doc)
        return OtpVerifyLockedOut(status="locked", retry_after_seconds=policy.lockout_seconds)

    salt = str(otp_doc.get("otp_salt") or "")
    expected_hash = str(otp_doc.get("otp_hash") or "")
    if not salt or not expected_hash:
        return OtpVerifyLockedOut(status="locked", retry_after_seconds=policy.lockout_seconds)

    provided_hash = hash_otp(payload.otp, salt)
    if provided_hash != expected_hash:
        attempts_remaining -= 1
        otp_doc["attempts_remaining"] = attempts_remaining
        if attempts_remaining <= 0:
            otp_doc["locked_until"] = isoformat(expires_at(now, policy.lockout_seconds))
        await kv.put_json(BUCKET_AUTH, f"otp/request/{username}", otp_doc)

        if attempts_remaining <= 0:
            return OtpVerifyLockedOut(status="locked", retry_after_seconds=policy.lockout_seconds)
        return OtpVerifyInvalidOut(status="invalid", attempts_remaining=attempts_remaining)

    # Success: create session.
    # Use the role resolved during OTP request (from channel userlist)
    role = otp_doc.get("resolved_role")
    if not role or role not in ("admin", "blessed", "viewer"):
        # Fallback to legacy resolution if not stored (shouldn't happen for new OTPs)
        role = await resolve_role(username, kv)

    session_id = generate_salt(24)
    sess_exp = expires_at(now, session_policy.ttl_seconds)
    await kv.put_json(
        BUCKET_AUTH,
        f"session/{session_id}",
        {
            "username": username,
            "role": role,
            "created_at": isoformat(now),
            "expires_at": isoformat(sess_exp),
            "ip": get_request_ip(request),
            "schema_version": 1,
        },
    )
    # Single-use OTP.
    await kv.delete(BUCKET_AUTH, f"otp/request/{username}")

    response.set_cookie(
        "kryten_playlist_session",
        session_id,
        httponly=True,
        samesite="lax",
        secure=cookie_is_secure(request),
        max_age=session_policy.ttl_seconds,
        path="/",
    )
    return OtpVerifyOkOut(status="ok", role=role)


@router.post("/ipblock", response_model=IpBlockOut)
async def ipblock(
    payload: IpBlockIn,
    request: Request,
    kv=Depends(get_kv),
    cfg=Depends(get_config),
) -> IpBlockOut:
    ip = get_request_ip(request)
    intent = await kv.get_json(BUCKET_AUTH, f"ipblock_intent/{ip}")

    # Allow if there is a fresh intent (from unsolicited verify). Admin override can be added in PR-05.
    if not intent or not intent.get("expires_at"):
        raise HTTPException(status_code=403, detail="IP block not authorized")

    if parse_iso(intent["expires_at"]) <= utcnow():
        try:
            await kv.delete(BUCKET_AUTH, f"ipblock_intent/{ip}")
        except Exception:
            pass
        raise HTTPException(status_code=403, detail="IP block not authorized")

    hours = payload.hours or cfg.otp_unsolicited_block_hours_default
    now = utcnow()
    blocked_until = now + timedelta(hours=hours)

    await kv.put_json(
        BUCKET_AUTH,
        f"ipblock/{ip}",
        {
            "blocked_until": isoformat(blocked_until),
            "reason": "otp_unsolicited",
            "created_at": isoformat(now),
            "schema_version": 1,
        },
    )
    try:
        await kv.delete(BUCKET_AUTH, f"ipblock_intent/{ip}")
    except Exception:
        pass
    return IpBlockOut(status="blocked", blocked_until=blocked_until)


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    kv=Depends(get_kv),
) -> dict:
    # Best-effort delete current session.
    session_id = request.cookies.get("kryten_playlist_session")
    if session_id:
        try:
            await kv.delete(BUCKET_AUTH, f"session/{session_id}")
        except Exception:
            pass
    response.delete_cookie("kryten_playlist_session", path="/")
    return {"status": "ok"}


@router.get("/session", response_model=SessionOut)
async def get_session(
    request: Request,
    kv=Depends(get_kv),
) -> SessionOut:
    """Get current session information."""
    session_id = request.cookies.get("kryten_playlist_session")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session_doc = await kv.get_json(BUCKET_AUTH, f"session/{session_id}")
    if not session_doc:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Check if session is expired
    exp_raw = session_doc.get("expires_at")
    if not exp_raw:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    exp = parse_iso(exp_raw)
    if exp <= utcnow():
        # Session expired, clean it up
        try:
            await kv.delete(BUCKET_AUTH, f"session/{session_id}")
        except Exception:
            pass
        raise HTTPException(status_code=401, detail="Session expired")
    
    return SessionOut(
        username=session_doc.get("username", ""),
        role=session_doc.get("role", "viewer"),
        expires_at=exp_raw,
    )
