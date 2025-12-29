"""MediaCMS connector for fetching catalog items from MediaCMS REST API."""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Any, AsyncIterator

import httpx

from kryten_playlist.catalog.models import CatalogItem

logger = logging.getLogger(__name__)


@dataclass
class MediaCMSConnector:
    """Connector that fetches catalog items from a MediaCMS instance.

    Uses the REST API:
    - GET /api/v1/media - list all media items
    - GET /api/v1/categories - list all categories

    The manifest URL format for Cytube is:
    {base_url}/api/v1/media/cytube/{friendly_token}.json
    """

    base_url: str
    """Base URL of the MediaCMS instance, e.g. https://media.example.com"""

    timeout: float = 30.0
    """HTTP request timeout in seconds."""

    page_size: int = 100
    """Number of items to fetch per page (if API supports pagination)."""

    concurrency: int = 24
    """Number of concurrent requests for item details."""

    async def iter_items(self) -> AsyncIterator[CatalogItem]:
        """Yield CatalogItems from the MediaCMS API.

        Fetches all media items, paginating if necessary.
        """
        base = self.base_url.rstrip("/")
        sem = asyncio.Semaphore(self.concurrency)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Fetch categories first to map IDs to names
            category_map = await self._fetch_category_map(client, base)

            # Helper to process a single item with concurrency limit
            async def process_item(item: dict[str, Any]) -> CatalogItem | None:
                async with sem:
                    # Fetch extended details if needed for category info
                    details = await self._fetch_item_details(client, item)
                    if details:
                        # Merge details into item, preferring details
                        item.update(details)
                    
                    return self._parse_item(item, category_map)

            # Fetch media pages
            page = 1
            while True:
                url = f"{base}/api/v1/media"
                params: dict[str, Any] = {"page": page}

                try:
                    resp = await client.get(url, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                except httpx.HTTPStatusError as e:
                    logger.error("MediaCMS API error: %s", e)
                    break
                except Exception as e:
                    logger.error("MediaCMS request failed: %s", e)
                    break

                # MediaCMS may return a list directly or paginated dict
                items = self._extract_items(data)
                if not items:
                    break

                # Process items in parallel
                tasks = [process_item(item) for item in items]
                for future in asyncio.as_completed(tasks):
                    catalog_item = await future
                    if catalog_item:
                        yield catalog_item

                # Check for more pages
                if not self._has_next_page(data, len(items)):
                    break

                page += 1

    async def _fetch_item_details(
        self, client: httpx.AsyncClient, item: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Fetch extended details for a single item using its API URL."""
        api_url = item.get("api_url")
        if not api_url:
            return None

        # Handle relative or absolute URLs
        if not api_url.startswith("http"):
            base = self.base_url.rstrip("/")
            api_url = f"{base}{api_url}" if api_url.startswith("/") else f"{base}/{api_url}"

        try:
            resp = await client.get(api_url)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"Failed to fetch details for item {item.get('friendly_token')}: {e}")
            return None

    async def _fetch_category_map(
        self, client: httpx.AsyncClient, base: str
    ) -> dict[int, str]:
        """Fetch categories and return id->name mapping."""
        try:
            resp = await client.get(f"{base}/api/v1/categories")
            resp.raise_for_status()
            data = resp.json()

            # Categories may be a list of dicts with id and title/name
            result: dict[int, str] = {}
            for cat in data if isinstance(data, list) else []:
                cat_id = cat.get("id")
                cat_name = cat.get("title") or cat.get("name") or ""
                if cat_id is not None and cat_name:
                    result[int(cat_id)] = str(cat_name)
            return result
        except Exception as e:
            logger.warning("Failed to fetch categories: %s", e)
            return {}

    def _extract_items(self, data: Any) -> list[dict[str, Any]]:
        """Extract media item list from API response."""
        # MediaCMS might return:
        # - A list of items directly
        # - A dict with "results" key (DRF pagination)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("results") or data.get("items") or []
        return []

    def _has_next_page(self, data: Any, fetched_count: int) -> bool:
        """Determine if there are more pages to fetch."""
        if isinstance(data, dict):
            # DRF-style pagination
            if data.get("next"):
                return True
            # Or count-based
            total = data.get("count") or data.get("total")
            if total is not None:
                # If we have fewer than total, there might be more
                # But we'd need to track offset - simpler: rely on empty page
                pass
        # If we got items, there might be more; if empty, we're done
        return fetched_count > 0

    def _sanitize_category(self, category: str | None) -> str | None:
        """Remove leading numbers and dots from category names.
        
        Example: "1.Family Comedies" -> "Family Comedies"
        """
        if not category:
            return category
            
        # Match pattern like "1. ", "02.", "5." at the start
        # ^\d+\.\s* matches start of string, one or more digits, a dot, and optional whitespace
        return re.sub(r'^\d+\.\s*', '', category)

    def _parse_item(
        self, item: dict[str, Any], category_map: dict[int, str]
    ) -> CatalogItem | None:
        """Parse a single media item dict into a CatalogItem."""
        # The video_id is the friendly_token
        video_id = item.get("friendly_token") or item.get("uid") or item.get("id")
        if not video_id:
            return None

        video_id = str(video_id)
        title = item.get("title") or video_id

        # Categories: might be list of IDs, names, or objects
        raw_cats = item.get("categories") or item.get("category") or []
        categories: list[str] = []
        mediacms_category: str | None = None

        # Check for extended categories_info first (most reliable for MediaCMS)
        categories_info = item.get("categories_info")
        if isinstance(categories_info, list) and categories_info:
            # Extract title from first category info
            first_cat = categories_info[0]
            if isinstance(first_cat, dict):
                cat_title = first_cat.get("title")
                if cat_title:
                    categories.append(str(cat_title))
                    mediacms_category = str(cat_title)

        # Fallback to standard categories if extended info didn't yield anything
        if not categories:
            if isinstance(raw_cats, list):
                for c in raw_cats:
                    if isinstance(c, str):
                        categories.append(c)
                    elif isinstance(c, int):
                        # Look up in category map
                        name = category_map.get(c)
                        if name:
                            categories.append(name)
                    elif isinstance(c, dict):
                        cat_name = c.get("title") or c.get("name")
                        if cat_name:
                            categories.append(str(cat_name))
            elif isinstance(raw_cats, int):
                name = category_map.get(raw_cats)
                if name:
                    categories.append(name)

        # Set the primary category if not already set by extended info
        if categories and not mediacms_category:
            mediacms_category = categories[0]

        # Sanitize category
        sanitized_category = self._sanitize_category(mediacms_category)

        # Duration: might be in seconds or as a string
        duration = item.get("duration") or item.get("duration_seconds")
        duration_seconds: int | None = None
        if duration is not None:
            try:
                duration_seconds = int(float(duration))
            except (ValueError, TypeError):
                pass

        # Thumbnail
        thumbnail_url = item.get("thumbnail_url") or item.get("poster_url")

        return CatalogItem(
            video_id=video_id,
            title=str(title),
            categories=categories,
            mediacms_category=mediacms_category,
            sanitized_category=sanitized_category,
            duration_seconds=duration_seconds,
            thumbnail_url=str(thumbnail_url) if thumbnail_url else None,
        )


def cytube_manifest_url(base_url: str, video_id: str) -> str:
    """Construct the Cytube manifest URL for a MediaCMS video.

    MediaCMS exposes Cytube manifests at:
    /api/v1/media/cytube/{friendly_token}.json
    """
    base = base_url.rstrip("/")
    return f"{base}/api/v1/media/cytube/{video_id}.json"
