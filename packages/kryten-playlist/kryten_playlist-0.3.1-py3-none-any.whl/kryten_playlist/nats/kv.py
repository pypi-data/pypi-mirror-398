from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

BUCKET_AUTH = "kryten_playlist_auth"
BUCKET_ACL = "kryten_playlist_acl"
BUCKET_PLAYLISTS = "kryten_playlist_playlists"
BUCKET_SNAPSHOT = "kryten_playlist_snapshot"
BUCKET_ANALYTICS = "kryten_playlist_analytics"
BUCKET_LIKES = "kryten_playlist_likes"


@dataclass(frozen=True)
class KvNamespace:
    name: str = "default"

    def key(self, suffix: str) -> str:
        suffix = suffix.lstrip("/")
        return f"ns/{self.name}/{suffix}"


class KvJson:
    def __init__(self, client: Any, namespace: KvNamespace):
        self._client = client
        self._ns = namespace

    async def ensure_buckets(self) -> None:
        # Best-effort bucket binding/creation via KrytenClient.
        # This satisfies the project-wide rule: all NATS interactions must go through KrytenClient.
        for bucket in (
            BUCKET_AUTH,
            BUCKET_ACL,
            BUCKET_PLAYLISTS,
            BUCKET_SNAPSHOT,
            BUCKET_ANALYTICS,
            BUCKET_LIKES,
        ):
            try:
                await self._client.get_kv_bucket(bucket)
                logger.debug(f"KV bucket {bucket} already exists")
            except Exception:
                # Bucket doesn't exist, but we can't create it via KrytenClient
                # This is expected behavior - buckets should be created by the robot
                logger.debug(f"KV bucket {bucket} not found, will use direct KV operations")

    async def get_json(self, bucket: str, key_suffix: str) -> Any | None:
        return await self._client.kv_get(
            bucket,
            self._ns.key(key_suffix),
            default=None,
            parse_json=True,
        )

    async def put_json(self, bucket: str, key_suffix: str, value: Any) -> None:
        await self._client.kv_put(bucket, self._ns.key(key_suffix), value, as_json=True)

    async def delete(self, bucket: str, key_suffix: str) -> None:
        await self._client.kv_delete(bucket, self._ns.key(key_suffix))

    async def keys(self, bucket: str, prefix_suffix: str = "") -> list[str]:
        # kv_store.kv_keys returns all keys for a bucket; filter to requested namespace prefix.
        all_keys = await self._client.kv_keys(bucket)
        prefix = self._ns.key(prefix_suffix)
        return [k for k in all_keys if k.startswith(prefix)]
