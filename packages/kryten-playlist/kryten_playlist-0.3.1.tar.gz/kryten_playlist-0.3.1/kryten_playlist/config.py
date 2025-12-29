"""Configuration management for kryten-playlist."""

import json
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any


class Config:
    """Service configuration."""

    def __init__(self, config_path: Path):
        """Initialize configuration from file."""
        self.config_path = config_path
        self._config: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, encoding="utf-8") as f:
            self._config = json.load(f)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)

    @property
    def nats_url(self) -> str:
        """Get NATS server URL."""
        return self.get("nats_url", "nats://localhost:4222")

    @property
    def nats_subject_prefix(self) -> str:
        """Get NATS subject prefix."""
        return self.get("nats_subject_prefix", "kryten")

    @property
    def service_name(self) -> str:
        """Get service name."""
        return self.get("service_name", "playlist")

    @property
    def version(self) -> str:
        """Get installed package version (single source of truth)."""
        try:
            return version("kryten-playlist")
        except PackageNotFoundError:
            return "0.0.0"

    @property
    def cytube_domain(self) -> str:
        """CyTube domain (e.g. cytu.be)."""
        return self.get("cytube_domain", "cytu.be")

    @property
    def cytube_channel(self) -> str:
        """CyTube channel (e.g. lounge)."""
        return self.get("cytube_channel", "lounge")

    @property
    def namespace(self) -> str:
        """Get logical namespace used for KV key prefixes."""
        return self.get("namespace", "default")

    @property
    def sqlite_path(self) -> str:
        """Get SQLite catalog database path."""
        return self.get("sqlite_path", "./data/catalog.sqlite3")

    @property
    def http_host(self) -> str:
        """HTTP bind host for FastAPI (when enabled)."""
        return self.get("http_host", "127.0.0.1")

    @property
    def http_port(self) -> int:
        """HTTP bind port for FastAPI (when enabled)."""
        return int(self.get("http_port", 8088))

    @property
    def http_log_level(self) -> str:
        """HTTP server log level (debug, info, warning, error)."""
        return self.get("http_log_level", "warning")

    @property
    def disable_auth(self) -> bool:
        """Disable authentication for testing purposes (DANGEROUS: only use for local testing)."""
        return self.get("disable_auth", False)

    @property
    def otp_ttl_seconds(self) -> int:
        """OTP time-to-live in seconds."""
        return int(self.get("otp_ttl_seconds", 300))

    @property
    def otp_lockout_seconds(self) -> int:
        """Lockout duration after OTP attempts exhausted."""
        return int(self.get("otp_lockout_seconds", 3600))

    @property
    def otp_length(self) -> int:
        """Length of generated OTP code."""
        return int(self.get("otp_length", 8))

    @property
    def otp_unsolicited_block_hours_default(self) -> int:
        """Default IP block duration offered on unsolicited OTP verification."""
        return int(self.get("otp_unsolicited_block_hours_default", 72))

    @property
    def session_ttl_seconds(self) -> int:
        """Session TTL in seconds."""
        return int(self.get("session_ttl_seconds", 60 * 60 * 12))

    @property
    def catalog_refresh_watcher_enabled(self) -> bool:
        """Enable the background watcher that acks catalog_refresh markers."""
        return bool(self.get("catalog_refresh_watcher_enabled", True))

    @property
    def catalog_refresh_watcher_poll_seconds(self) -> float:
        """Polling interval for the catalog_refresh watcher."""
        return float(self.get("catalog_refresh_watcher_poll_seconds", 2.0))

    @property
    def catalog_refresh_run_on_marker(self) -> bool:
        """If True, watcher runs the actual catalog refresh pipeline when a marker is detected."""
        return bool(self.get("catalog_refresh_run_on_marker", True))

    @property
    def mediacms_manifest_base_url(self) -> str:
        """Base URL for deriving manifest URLs from video_id."""
        return self.get("mediacms_manifest_base_url", "https://mediacms.example.com/media")

    @property
    def initial_admins(self) -> list[str]:
        """List of usernames to seed as admins on startup.

        These users will be added to the admin list if not already present.
        Useful for bootstrapping a new installation.
        """
        admins = self.get("initial_admins", [])
        if isinstance(admins, list):
            return [str(u).strip() for u in admins if str(u).strip()]
        return []

    @property
    def blessed_users(self) -> list[str]:
        """List of usernames that can see uncategorized content.
        
        If empty, only admins can see uncategorized content (if implemented that way),
        or nobody can.
        """
        users = self.get("blessed_users", [])
        if isinstance(users, list):
            return [str(u).strip() for u in users if str(u).strip()]
        return []
