"""Export playlists to Markdown format with enhanced metadata."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import aiosqlite


async def export_playlist_markdown(
    db_path: str,
    items: list[dict[str, Any]],
    playlist_name: str,
    *,
    include_synopsis: bool = True,
    include_duration: bool = True,
    include_tags: bool = True,
) -> str:
    """Export a playlist to annotated Markdown format.

    Args:
        db_path: Path to the enhanced catalog database.
        items: List of dicts with at least {"video_id": str}.
        playlist_name: Name for the playlist header.
        include_synopsis: Include LLM-generated synopsis.
        include_duration: Include duration info.
        include_tags: Include tags.

    Returns:
        Markdown formatted string.
    """
    video_ids = [it.get("video_id") for it in items if it.get("video_id")]
    if not video_ids:
        return f"# {playlist_name}\n\n*Empty playlist*\n"

    placeholders = ",".join("?" * len(video_ids))

    lines = [
        f"# {playlist_name}",
        "",
        f"*Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
    ]

    total_duration = 0

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row

        # Fetch item details
        cursor = await conn.execute(
            f"""
            SELECT
                video_id,
                sanitized_title,
                raw_title,
                is_tv,
                duration_seconds,
                synopsis,
                genre,
                era,
                mood,
                cast_list,
                director
            FROM catalog_item
            WHERE video_id IN ({placeholders})
            """,
            video_ids,
        )
        rows = {row["video_id"]: dict(row) for row in await cursor.fetchall()}

        # Fetch tags for items
        tags_by_video: dict[str, list[str]] = {}
        if include_tags:
            cursor = await conn.execute(
                f"""
                SELECT cit.video_id, ct.name
                FROM catalog_item_tag cit
                JOIN catalog_tag ct ON cit.tag_id = ct.id
                WHERE cit.video_id IN ({placeholders})
                ORDER BY cit.confidence DESC
                """,
                video_ids,
            )
            for row in await cursor.fetchall():
                tags_by_video.setdefault(row[0], []).append(row[1])

    # Generate markdown in playlist order
    lines.append("## Lineup")
    lines.append("")

    for idx, item in enumerate(items, 1):
        video_id = item.get("video_id")
        if not video_id or video_id not in rows:
            lines.append(f"{idx}. *Unknown item: {video_id}*")
            lines.append("")
            continue

        row = rows[video_id]
        title = row["sanitized_title"] or row["raw_title"] or video_id
        is_tv = row["is_tv"]
        duration = row["duration_seconds"]
        synopsis = row["synopsis"]
        genre = row["genre"]
        era = row["era"]
        mood = row["mood"]
        cast_list = row["cast_list"]
        director = row["director"]
        tags = tags_by_video.get(video_id, [])

        # Type icon
        icon = "📺" if is_tv else "🎬"

        # Duration string
        dur_str = ""
        if include_duration and duration:
            total_duration += duration
            hours = duration // 3600
            mins = (duration % 3600) // 60
            if hours:
                dur_str = f" ({hours}h {mins}m)"
            else:
                dur_str = f" ({mins}m)"

        lines.append(f"### {idx}. {icon} {title}{dur_str}")
        lines.append("")

        # Metadata line
        meta_parts = []
        if genre:
            meta_parts.append(f"**Genre:** {genre}")
        if era:
            meta_parts.append(f"**Era:** {era}")
        if mood:
            meta_parts.append(f"**Mood:** {mood}")
        if director:
            meta_parts.append(f"**Director:** {director}")

        if meta_parts:
            lines.append(" | ".join(meta_parts))
            lines.append("")

        # Synopsis
        if include_synopsis and synopsis:
            lines.append(f"> {synopsis}")
            lines.append("")

        # Cast
        if cast_list:
            lines.append(f"**Cast:** {cast_list}")
            lines.append("")

        # Tags
        if include_tags and tags:
            tag_str = " ".join(f"`{t}`" for t in tags[:8])
            lines.append(f"**Tags:** {tag_str}")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Total items:** {len(items)}")
    if total_duration:
        hours = total_duration // 3600
        mins = (total_duration % 3600) // 60
        lines.append(f"- **Total runtime:** {hours}h {mins}m")
    lines.append("")

    return "\n".join(lines)


async def export_simple_markdown(
    items: list[dict[str, Any]],
    playlist_name: str,
) -> str:
    """Export a playlist to simple Markdown (no database lookup).

    Useful when you don't have an enhanced catalog or just need a quick list.
    """
    lines = [
        f"# {playlist_name}",
        "",
        f"*Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
    ]

    for idx, item in enumerate(items, 1):
        title = item.get("title") or item.get("video_id") or "Unknown"
        lines.append(f"{idx}. {title}")

    lines.append("")
    lines.append(f"*{len(items)} items*")

    return "\n".join(lines)
