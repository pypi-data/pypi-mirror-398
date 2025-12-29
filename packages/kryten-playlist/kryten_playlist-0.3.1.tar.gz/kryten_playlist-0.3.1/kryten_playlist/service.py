"""Main service class for kryten-playlist."""

import asyncio
import contextlib
import logging
from pathlib import Path
from typing import Any, Optional

from kryten import KrytenClient

from kryten_playlist.config import Config
from kryten_playlist.catalog_refresh_watcher import run_catalog_refresh_watcher
from kryten_playlist.admin_cmds import (
    add_blessed,
    get_blessed,
    record_catalog_refresh_request,
    remove_blessed,
)
from kryten_playlist.nats.contracts import (
    CMD_BLESSED_ADD,
    CMD_BLESSED_LIST,
    CMD_BLESSED_REMOVE,
    CMD_CATALOG_REFRESH,
    CMD_QUEUE_APPLY,
    cmd_subject,
)
from kryten_playlist.nats.kv import KvJson, KvNamespace
from kryten_playlist.queue_apply import apply_playlist_to_queue
from kryten_playlist.storage.schema import init_catalog_schema
from kryten_playlist.storage.sqlite import SqliteConfig, SqliteDb
from kryten_playlist.web.deps import resolve_role
from kryten_playlist.web.app import create_app
from kryten_playlist.web.routes.stats import increment_play_count, set_current_video

logger = logging.getLogger(__name__)


class AuthSessionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "/api/v1/auth/session" not in record.getMessage()


class PlaylistService:
    """Kryten Playlist Service."""

    def __init__(self, config_path: Path, *, enable_web: bool = False):
        """Initialize the service."""
        self.config = Config(config_path)
        self.client = KrytenClient(
            {
                "nats": {"servers": [self.config.nats_url]},
                "channels": [
                    {
                        "domain": self.config.cytube_domain,
                        "channel": self.config.cytube_channel,
                    }
                ],
                "service": {
                    "name": self.config.service_name,
                    "version": self.config.version,
                    "enable_lifecycle": True,
                    "enable_heartbeat": True,
                    "enable_discovery": True,
                },
            }
        )
        self._shutdown_event = asyncio.Event()
        self._enable_web = enable_web
        self._web_task: Optional[asyncio.Task[None]] = None
        self._web_server: Any | None = None
        self._catalog_refresh_task: Optional[asyncio.Task[None]] = None
        self._kv: KvJson | None = None
        self._sqlite_conn: Any | None = None
        self._resolved_channel: str | None = None
        self._resolved_domain: str | None = None

    @property
    def resolved_channel(self) -> str:
        """Get the resolved channel name from robot discovery.

        Falls back to config if discovery hasn't happened yet.
        """
        return self._resolved_channel or self.config.cytube_channel

    @property
    def resolved_domain(self) -> str:
        """Get the resolved domain from robot discovery.

        Falls back to config if discovery hasn't happened yet.
        """
        return self._resolved_domain or self.config.cytube_domain

    async def _discover_channels(self) -> bool:
        """Discover available channels from kryten-robot.

        This follows the standard kryten-ecosystem lifecycle pattern where
        services poll the robot for available channels rather than relying
        solely on static configuration.

        Returns:
            True if at least one channel was discovered.
        """
        try:
            channels = await self.client.get_channels(timeout=10.0)
            if not channels:
                logger.warning("No channels discovered from robot")
                return False

            logger.info(f"Discovered {len(channels)} channel(s) from robot:")
            for ch in channels:
                domain = ch.get("domain", "unknown")
                channel = ch.get("channel", "unknown")
                connected = ch.get("connected", False)
                status = "connected" if connected else "not connected"
                logger.info(f"  - {domain}/{channel} ({status})")

            # Try to match configured channel first
            config_channel = self.config.cytube_channel.lower()
            config_domain = self.config.cytube_domain.lower()

            for ch in channels:
                ch_channel = ch.get("channel", "").lower()
                ch_domain = ch.get("domain", "").lower()

                if ch_channel == config_channel and ch_domain == config_domain:
                    self._resolved_channel = ch.get("channel")
                    self._resolved_domain = ch.get("domain")
                    logger.info(
                        f"Resolved channel from config: {self._resolved_domain}/{self._resolved_channel}"
                    )
                    return True

            # If no match, use the first connected channel
            for ch in channels:
                if ch.get("connected", False):
                    self._resolved_channel = ch.get("channel")
                    self._resolved_domain = ch.get("domain")
                    logger.warning(
                        f"Config channel '{config_domain}/{config_channel}' not found, "
                        f"using first available: {self._resolved_domain}/{self._resolved_channel}"
                    )
                    return True

            # Fall back to first channel even if not connected
            if channels:
                ch = channels[0]
                self._resolved_channel = ch.get("channel")
                self._resolved_domain = ch.get("domain")
                logger.warning(
                    f"No connected channels found, using: {self._resolved_domain}/{self._resolved_channel}"
                )
                return True

            return False

        except TimeoutError:
            logger.warning("Channel discovery timed out, using config values")
            return False
        except Exception as e:
            logger.warning(f"Channel discovery failed: {e}, using config values")
            return False

    async def _seed_initial_admins(self) -> None:
        """Seed initial admins from config.

        This enables bootstrapping a new installation by specifying
        initial_admins in config.json. Users are only added if not
        already present in the admin list.
        """
        if not self._kv:
            return

        initial_admins = self.config.initial_admins
        if not initial_admins:
            return

        from kryten_playlist.nats.kv import BUCKET_ACL

        # Get current admin list
        existing = await self._kv.get_json(BUCKET_ACL, "admins")
        if isinstance(existing, list):
            admin_list = [str(u).strip() for u in existing if str(u).strip()]
        elif isinstance(existing, dict):
            admin_list = [str(u).strip() for u in existing.get("admins", []) if str(u).strip()]
        else:
            admin_list = []

        # Add any missing admins
        added = []
        for username in initial_admins:
            if username not in admin_list:
                admin_list.append(username)
                added.append(username)

        if added:
            await self._kv.put_json(BUCKET_ACL, "admins", admin_list)
            logger.info(f"Seeded initial admins: {', '.join(added)}")
        else:
            logger.debug("All initial admins already present")

    async def start(self) -> None:
        """Start the service."""
        logger.info("Starting playlist service")

        # Connect to NATS
        await self.client.connect()

        # Discover available channels from robot (standard kryten lifecycle)
        await self._discover_channels()
        logger.info(f"Using channel: {self.resolved_domain}/{self.resolved_channel}")

        # Subscribe to robot startup - re-discover channels when robot restarts
        await self.client.subscribe(
            "kryten.lifecycle.robot.startup",
            self._handle_robot_startup,
        )
        logger.info("Subscribed to kryten.lifecycle.robot.startup")

        # Initialize KV + SQLite (shared across API + future workers)
        self._kv = KvJson(self.client, KvNamespace(self.config.namespace))
        await self._kv.ensure_buckets()

        # Seed initial admins from config (bootstrap new installations)
        await self._seed_initial_admins()

        sqlite = SqliteDb(SqliteConfig(path=Path(self.config.sqlite_path)))
        self._sqlite_conn = await sqlite.connect()
        await init_catalog_schema(self._sqlite_conn)

        # Command subjects (request/reply)
        async def _ensure_admin(
            *,
            correlation_id: str,
            namespace: str,
            requested_by: str,
        ) -> tuple[bool, dict[str, Any]]:
            if namespace and namespace != self.config.namespace:
                return False, {
                    "correlation_id": correlation_id,
                    "status": "error",
                    "error": "namespace_mismatch",
                }

            if not self._kv:
                return False, {
                    "correlation_id": correlation_id,
                    "status": "error",
                    "error": "service_not_ready",
                }

            role = await resolve_role(requested_by, self._kv)
            if role != "admin":
                return False, {
                    "correlation_id": correlation_id,
                    "status": "error",
                    "error": "forbidden",
                }

            return True, {}

        async def _handle_queue_apply_cmd(request: dict[str, Any]) -> dict[str, Any]:
            correlation_id = str(request.get("correlation_id") or "")
            namespace = str(request.get("namespace") or "")
            requested_by = str(request.get("requested_by") or "")
            playlist_id = str(request.get("playlist_id") or "")
            mode = str(request.get("mode") or "")

            if namespace and namespace != self.config.namespace:
                return {
                    "correlation_id": correlation_id,
                    "status": "error",
                    "enqueued_count": 0,
                    "failed": [],
                    "error": "namespace_mismatch",
                }

            if mode not in ("preserve_current", "append", "hard_replace"):
                return {
                    "correlation_id": correlation_id,
                    "status": "error",
                    "enqueued_count": 0,
                    "failed": [],
                    "error": "invalid_mode",
                }

            if not self._kv or not self._sqlite_conn:
                return {
                    "correlation_id": correlation_id,
                    "status": "error",
                    "enqueued_count": 0,
                    "failed": [],
                    "error": "service_not_ready",
                }

            role = await resolve_role(requested_by, self._kv)
            if role not in ("blessed", "admin"):
                return {
                    "correlation_id": correlation_id,
                    "status": "error",
                    "enqueued_count": 0,
                    "failed": [],
                    "error": "forbidden",
                }

            if mode == "hard_replace" and role != "admin":
                return {
                    "correlation_id": correlation_id,
                    "status": "error",
                    "enqueued_count": 0,
                    "failed": [],
                    "error": "forbidden",
                }

            result = await apply_playlist_to_queue(
                client=self.client,
                kv=self._kv,
                sqlite_conn=self._sqlite_conn,
                channel=self.resolved_channel,
                playlist_id=playlist_id,
                mode=mode,  # type: ignore[arg-type]
            )

            payload = result.as_dict()
            payload["correlation_id"] = correlation_id
            return payload

        async def _handle_blessed_list_cmd(request: dict[str, Any]) -> dict[str, Any]:
            correlation_id = str(request.get("correlation_id") or "")
            namespace = str(request.get("namespace") or "")
            requested_by = str(request.get("requested_by") or "")

            ok, err = await _ensure_admin(
                correlation_id=correlation_id,
                namespace=namespace,
                requested_by=requested_by,
            )
            if not ok:
                return {**err, "blessed": []}

            blessed = await get_blessed(self._kv)  # type: ignore[arg-type]
            return {
                "correlation_id": correlation_id,
                "status": "ok",
                "blessed": blessed,
            }

        async def _handle_blessed_add_cmd(request: dict[str, Any]) -> dict[str, Any]:
            correlation_id = str(request.get("correlation_id") or "")
            namespace = str(request.get("namespace") or "")
            requested_by = str(request.get("requested_by") or "")
            username = str(request.get("username") or "")

            ok, err = await _ensure_admin(
                correlation_id=correlation_id,
                namespace=namespace,
                requested_by=requested_by,
            )
            if not ok:
                return {**err, "blessed": []}

            try:
                blessed = await add_blessed(self._kv, username)  # type: ignore[arg-type]
            except ValueError as e:
                return {
                    "correlation_id": correlation_id,
                    "status": "error",
                    "error": str(e),
                    "blessed": await get_blessed(self._kv),  # type: ignore[arg-type]
                }

            return {
                "correlation_id": correlation_id,
                "status": "ok",
                "username": username.strip(),
                "blessed": blessed,
            }

        async def _handle_blessed_remove_cmd(request: dict[str, Any]) -> dict[str, Any]:
            correlation_id = str(request.get("correlation_id") or "")
            namespace = str(request.get("namespace") or "")
            requested_by = str(request.get("requested_by") or "")
            username = str(request.get("username") or "")

            ok, err = await _ensure_admin(
                correlation_id=correlation_id,
                namespace=namespace,
                requested_by=requested_by,
            )
            if not ok:
                return {**err, "blessed": []}

            try:
                blessed = await remove_blessed(self._kv, username)  # type: ignore[arg-type]
            except ValueError as e:
                return {
                    "correlation_id": correlation_id,
                    "status": "error",
                    "error": str(e),
                    "blessed": await get_blessed(self._kv),  # type: ignore[arg-type]
                }

            return {
                "correlation_id": correlation_id,
                "status": "ok",
                "username": username.strip(),
                "blessed": blessed,
            }

        async def _handle_catalog_refresh_cmd(request: dict[str, Any]) -> dict[str, Any]:
            correlation_id = str(request.get("correlation_id") or "")
            namespace = str(request.get("namespace") or "")
            requested_by = str(request.get("requested_by") or "")

            ok, err = await _ensure_admin(
                correlation_id=correlation_id,
                namespace=namespace,
                requested_by=requested_by,
            )
            if not ok:
                return err

            doc = await record_catalog_refresh_request(
                self._kv,  # type: ignore[arg-type]
                requested_by=requested_by,
                correlation_id=correlation_id,
            )
            return {
                "correlation_id": correlation_id,
                "status": "ok",
                "request": doc,
            }

        await self.client.subscribe_request_reply(
            cmd_subject(self.config.nats_subject_prefix, CMD_QUEUE_APPLY),
            _handle_queue_apply_cmd,
        )

        await self.client.subscribe_request_reply(
            cmd_subject(self.config.nats_subject_prefix, CMD_BLESSED_LIST),
            _handle_blessed_list_cmd,
        )
        await self.client.subscribe_request_reply(
            cmd_subject(self.config.nats_subject_prefix, CMD_BLESSED_ADD),
            _handle_blessed_add_cmd,
        )
        await self.client.subscribe_request_reply(
            cmd_subject(self.config.nats_subject_prefix, CMD_BLESSED_REMOVE),
            _handle_blessed_remove_cmd,
        )
        await self.client.subscribe_request_reply(
            cmd_subject(self.config.nats_subject_prefix, CMD_CATALOG_REFRESH),
            _handle_catalog_refresh_cmd,
        )

        if self.config.catalog_refresh_watcher_enabled:
            self._catalog_refresh_task = asyncio.create_task(
                run_catalog_refresh_watcher(
                    kv=self._kv,
                    shutdown_event=self._shutdown_event,
                    poll_seconds=self.config.catalog_refresh_watcher_poll_seconds,
                    sqlite_conn=self._sqlite_conn,
                    manifest_base_url=self.config.mediacms_manifest_base_url,
                    run_refresh=self.config.catalog_refresh_run_on_marker,
                )
            )

        # Subscribe to events
        @self.client.on("queue")
        async def _queue(event: Any) -> None:
            await self._handle_queue(event)

        @self.client.on("delete")
        async def _delete(event: Any) -> None:
            await self._handle_delete(event)

        @self.client.on("movevideo")
        async def _move(event: Any) -> None:
            await self._handle_move_video(event)

        @self.client.on("settemp")
        async def _temp(event: Any) -> None:
            await self._handle_set_temp(event)

        @self.client.on("changemedia")
        async def _changemedia(event: Any) -> None:
            await self._handle_change_media(event)

        if self._enable_web:
            logger.info("DEBUG: Starting web server task")
            self._web_task = asyncio.create_task(self._run_web())

        logger.info("Playlist service started")

    async def stop(self) -> None:
        """Stop the service."""
        logger.info("Stopping playlist service")
        self._shutdown_event.set()

        if self._web_server is not None:
            logger.debug("Signaling web server to exit")
            self._web_server.should_exit = True

        if self._web_task is not None:
            # Allow uvicorn to shut down gracefully
            try:
                logger.debug("Waiting for web task to finish...")
                # Reduce wait time to minimize freeze perception if it's just stuck on keep-alive
                await asyncio.wait_for(self._web_task, timeout=2.0)
                logger.debug("Web task finished gracefully")
            except (asyncio.TimeoutError, asyncio.CancelledError):
                logger.warning("Web server task timed out, forcing cancellation")
                self._web_task.cancel()
                with contextlib.suppress(Exception):
                    await self._web_task
                logger.debug("Web task cancelled")

        if self._catalog_refresh_task is not None:
            logger.debug("Cancelling catalog refresh task")
            self._catalog_refresh_task.cancel()
            with contextlib.suppress(Exception):
                await self._catalog_refresh_task
            logger.debug("Catalog refresh task cancelled")

        # Disconnect from NATS
        logger.debug("Disconnecting from NATS...")
        await self.client.disconnect()
        logger.debug("Disconnected from NATS")

        if self._sqlite_conn is not None:
            logger.debug("Closing SQLite connection...")
            await self._sqlite_conn.close()
            logger.debug("SQLite connection closed")

        logger.info("Playlist service stopped")

    async def wait_for_shutdown(self) -> None:
        """Wait for shutdown signal."""
        await self._shutdown_event.wait()

    async def _handle_queue(self, event: Any) -> None:
        """Handle queue events."""
        payload = getattr(event, "payload", {}) or {}
        item = payload.get("item", {})
        after = payload.get("after", "")
        logger.info("Video queued: %s after %s", item.get("title", "unknown"), after)

        # Future: analytics hooks and playlist state tracking.

    async def _handle_delete(self, event: Any) -> None:
        """Handle delete events."""
        payload = getattr(event, "payload", {}) or {}
        uid = payload.get("uid", "")
        logger.info("Video deleted: %s", uid)

        # Future: analytics hooks and playlist state tracking.

    async def _handle_move_video(self, event: Any) -> None:
        """Handle moveVideo events."""
        payload = getattr(event, "payload", {}) or {}
        from_pos = payload.get("from", 0)
        to_pos = payload.get("after", "")
        logger.info("Video moved from %s to after %s", from_pos, to_pos)

        # Future: analytics hooks and playlist state tracking.

    async def _handle_set_temp(self, event: Any) -> None:
        """Handle setTemp events."""
        payload = getattr(event, "payload", {}) or {}
        uid = payload.get("uid", "")
        temp = payload.get("temp", False)
        logger.info("Video %s temp status set to %s", uid, temp)

        # Future: analytics hooks and playlist state tracking.

    async def _handle_change_media(self, event: Any) -> None:
        """Handle changeMedia events - track plays and current video."""
        payload = getattr(event, "payload", {}) or {}

        # Extract video info from the event
        # changeMedia payload typically has: id, title, type, seconds, etc.
        video_id = str(payload.get("id") or "").strip()
        title = str(payload.get("title") or "").strip()

        if not video_id:
            logger.debug("changeMedia event with no video_id, skipping analytics")
            return

        logger.info("Now playing: %s (%s)", title or video_id, video_id)

        if self._kv:
            try:
                # Update current video for "like current" feature
                await set_current_video(self._kv, video_id, title)

                # Increment play count
                new_count = await increment_play_count(self._kv, video_id)
                logger.debug("Play count for %s: %d", video_id, new_count)
            except Exception as e:
                logger.warning("Failed to update analytics for %s: %s", video_id, e)

    async def _handle_robot_startup(self, msg: Any) -> None:
        """Handle robot startup event - re-discover channels.

        When kryten-robot restarts, it may have different channel configuration.
        Re-discover channels to stay in sync with the robot.
        """
        try:
            logger.info("Robot startup detected, re-discovering channels...")
            await self._discover_channels()
            logger.info(f"Channel after robot restart: {self.resolved_domain}/{self.resolved_channel}")
        except Exception as e:
            logger.error(f"Error handling robot startup: {e}", exc_info=True)

    async def _run_web(self) -> None:
        logger.info("DEBUG: _run_web method called")
        import uvicorn

        app = create_app()
        app.state.config = self.config
        app.state.client = self.client
        app.state.kv = self._kv
        app.state.sqlite = self._sqlite_conn
        # Expose service for resolved channel access
        app.state.service = self
        
        logger.info(f"DEBUG: Service config disable_auth: {self.config.disable_auth}")
        logger.info(f"DEBUG: Starting web server on {self.config.http_host}:{self.config.http_port}")

        uv_cfg = uvicorn.Config(
            app,
            host=self.config.http_host,
            port=self.config.http_port,
            log_level=self.config.http_log_level,
            timeout_keep_alive=5,
        )
        self._web_server = uvicorn.Server(uv_cfg)

        uv_cfg = uvicorn.Config(
            app,
            host=self.config.http_host,
            port=self.config.http_port,
            log_level=self.config.http_log_level,
            timeout_keep_alive=5,
        )
        self._web_server = uvicorn.Server(uv_cfg)

        # Apply log filter via log_config customization instead of monkey-patching
        # This is safer and avoids potential issues with Uvicorn internals
        # We'll just set it on the logger directly before serving, relying on Uvicorn
        # to respect existing handlers if configured correctly, or we re-apply after.
        # Actually, simpler approach: wait for server to start loop then add filter?
        # No, Uvicorn setup is synchronous before the loop.
        
        # Let's try standard logging configuration approach
        # Uvicorn uses "uvicorn.access" logger. We can just add the filter to it globally
        # BUT Uvicorn might reset it.
        # Let's revert the monkeypatch and use a standard middleware or different approach if this fails.
        # However, the user says logs are MISSING.
        # The monkeypatch might be breaking configure_logging if it expects arguments.
        
        # Let's check uvicorn source or docs... configure_logging usually takes no args in Server class usage?
        # Actually, Server.configure_logging takes no arguments.
        # But maybe it's not being called? Or raising an error inside?
        
        # Let's try to just run it without the complex wrapper first to restore functionality,
        # then add the filter in a safer way.
        
        # Reverting to simple serve, but adding filter after serve starts? 
        # No, serve blocks.
        
        # Better approach: Pass a log_config dict to uvicorn.Config?
        # Or just trust that if we set it on the library logger it might persist?
        # Uvicorn's default config usually overwrites handlers but might keep filters?
        
        # Let's try removing the wrapper which is likely the cause of the 500/silence
        # and instead apply the filter to the 'uvicorn.access' logger *before* creating Config.
        # If that fails to persist, we can try a different way.
        
        # Wait, the previous code had:
        # logging.getLogger("uvicorn.access").addFilter(...)
        # BEFORE Config.
        # And user said it didn't work (spam continued).
        
        # The wrapper approach is risky. Let's fix the wrapper to be robust.
        # If original_configure_logging failed or something, that would explain it.
        
        # Let's try removing the wrapper for now to get the server back up.
        await self._web_server.serve()
