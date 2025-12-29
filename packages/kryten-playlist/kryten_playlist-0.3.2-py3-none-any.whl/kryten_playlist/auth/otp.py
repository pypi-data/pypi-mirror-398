from __future__ import annotations

import hashlib
import secrets
import string
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

_ALPHANUM = string.ascii_uppercase + string.digits


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def isoformat(dt: datetime) -> str:
    # Always store UTC ISO timestamps.
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def parse_iso(dt: str) -> datetime:
    # datetime.fromisoformat handles offsets; stored values are UTC.
    parsed = datetime.fromisoformat(dt)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def generate_otp_code(length: int = 8) -> str:
    if length < 6:
        raise ValueError("OTP length too short")
    return "".join(secrets.choice(_ALPHANUM) for _ in range(length))


def generate_salt(length: int = 16) -> str:
    # urlsafe characters; stored in KV.
    return secrets.token_urlsafe(length)


def hash_otp(otp: str, salt: str) -> str:
    # Simple salted SHA256; no OTP is stored in plaintext.
    h = hashlib.sha256()
    h.update(salt.encode("utf-8"))
    h.update(b":")
    h.update(otp.strip().encode("utf-8"))
    return h.hexdigest()


@dataclass(frozen=True)
class OtpPolicy:
    ttl_seconds: int = 300
    max_attempts: int = 3
    lockout_seconds: int = 3600
    otp_length: int = 8


@dataclass(frozen=True)
class SessionPolicy:
    ttl_seconds: int = 60 * 60 * 12


def expires_at(now: datetime, seconds: int) -> datetime:
    return now + timedelta(seconds=seconds)
