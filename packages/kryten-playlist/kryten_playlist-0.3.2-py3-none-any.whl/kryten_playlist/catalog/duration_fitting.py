"""Duration-based playlist fitting utilities.

Build playlists that fit specific time slots or durations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import aiosqlite


@dataclass
class FitResult:
    """Result of fitting items to a duration."""

    items: list[dict[str, Any]]
    total_duration: int  # seconds
    target_duration: int  # seconds
    slack: int  # seconds (positive = under, negative = over)

    @property
    def utilization(self) -> float:
        """Percentage of target duration used."""
        if self.target_duration == 0:
            return 0.0
        return min(100.0, 100.0 * self.total_duration / self.target_duration)


async def fit_to_duration(
    conn: aiosqlite.Connection,
    target_seconds: int,
    *,
    filter_tv: bool | None = None,
    filter_tags: list[str] | None = None,
    filter_categories: list[str] | None = None,
    filter_era: str | None = None,
    filter_genre: str | None = None,
    exclude_weekend_only: bool = False,
    max_items: int = 100,
    order_by: str = "random",
) -> FitResult:
    """Select items that fit within a target duration.

    Args:
        conn: Database connection.
        target_seconds: Target total duration in seconds.
        filter_tv: If True, only TV; if False, only movies; if None, both.
        filter_tags: Only items with ALL of these tags.
        filter_categories: Only items in ANY of these categories.
        filter_era: Only items from this era (e.g., "1980s").
        filter_genre: Only items with this genre.
        exclude_weekend_only: Exclude items marked weekend_only.
        max_items: Maximum items to return.
        order_by: "random", "duration_asc", "duration_desc", "title".

    Returns:
        FitResult with selected items.
    """
    # Build query
    conditions = ["duration_seconds IS NOT NULL", "duration_seconds > 0"]
    params: list[Any] = []

    if filter_tv is True:
        conditions.append("is_tv = 1")
    elif filter_tv is False:
        conditions.append("is_tv = 0")

    if filter_era:
        conditions.append("era = ?")
        params.append(filter_era)

    if filter_genre:
        conditions.append("genre = ?")
        params.append(filter_genre)

    if exclude_weekend_only:
        conditions.append("weekend_only = 0")

    # Category filter (subquery)
    if filter_categories:
        cat_placeholders = ",".join("?" * len(filter_categories))
        conditions.append(
            f"""
            video_id IN (
                SELECT cic.video_id
                FROM catalog_item_category cic
                JOIN catalog_category cc ON cic.category_id = cc.id
                WHERE cc.name IN ({cat_placeholders})
            )
            """
        )
        params.extend(filter_categories)

    # Tag filter (subquery with ALL semantics)
    if filter_tags:
        for tag in filter_tags:
            conditions.append(
                """
                video_id IN (
                    SELECT cit.video_id
                    FROM catalog_item_tag cit
                    JOIN catalog_tag ct ON cit.tag_id = ct.id
                    WHERE ct.name = ?
                )
                """
            )
            params.append(tag)

    # Order clause
    order_clause = {
        "random": "RANDOM()",
        "duration_asc": "duration_seconds ASC",
        "duration_desc": "duration_seconds DESC",
        "title": "sanitized_title ASC",
    }.get(order_by, "RANDOM()")

    where = " AND ".join(conditions)
    query = f"""
        SELECT video_id, sanitized_title, duration_seconds
        FROM catalog_item
        WHERE {where}
        ORDER BY {order_clause}
    """

    cursor = await conn.execute(query, params)
    candidates = await cursor.fetchall()

    # Greedy selection: pick items until we hit the target
    selected: list[dict[str, Any]] = []
    total = 0

    for video_id, title, duration in candidates:
        if len(selected) >= max_items:
            break
        if total + duration <= target_seconds:
            selected.append({
                "video_id": video_id,
                "title": title,
                "duration_seconds": duration,
            })
            total += duration

    return FitResult(
        items=selected,
        total_duration=total,
        target_duration=target_seconds,
        slack=target_seconds - total,
    )


async def fit_to_end_time(
    conn: aiosqlite.Connection,
    end_time: datetime,
    *,
    start_time: datetime | None = None,
    **kwargs,
) -> FitResult:
    """Select items to fill time until a specific end time.

    Args:
        conn: Database connection.
        end_time: When the playlist should end.
        start_time: When the playlist starts (default: now).
        **kwargs: Passed to fit_to_duration.

    Returns:
        FitResult with selected items.
    """
    if start_time is None:
        start_time = datetime.now(timezone.utc)

    delta = end_time - start_time
    target_seconds = int(delta.total_seconds())

    if target_seconds <= 0:
        return FitResult(items=[], total_duration=0, target_duration=0, slack=0)

    return await fit_to_duration(conn, target_seconds, **kwargs)


def calculate_end_time(
    items: list[dict[str, Any]],
    start_time: datetime | None = None,
) -> datetime:
    """Calculate when a playlist will end based on durations.

    Args:
        items: List of items with duration_seconds.
        start_time: When the playlist starts (default: now).

    Returns:
        Estimated end time.
    """
    if start_time is None:
        start_time = datetime.now(timezone.utc)

    total = sum(it.get("duration_seconds", 0) or 0 for it in items)
    return start_time + timedelta(seconds=total)


def format_duration(seconds: int) -> str:
    """Format seconds as human-readable duration."""
    hours = seconds // 3600
    mins = (seconds % 3600) // 60
    secs = seconds % 60

    if hours:
        return f"{hours}h {mins}m {secs}s"
    elif mins:
        return f"{mins}m {secs}s"
    else:
        return f"{secs}s"
