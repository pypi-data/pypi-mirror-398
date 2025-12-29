"""LLM enrichment CLI for catalog items.

Usage:
    # Test on a single item
    python -m kryten_playlist.catalog.enrich single "The Matrix" --db catalog.db

    # Test on 5 random items (dry run - don't save)
    python -m kryten_playlist.catalog.enrich sample --count 5 --dry-run --db catalog.db

    # Enrich 10 random unenriched items
    python -m kryten_playlist.catalog.enrich sample --count 10 --db catalog.db

    # Enrich ALL unenriched items
    python -m kryten_playlist.catalog.enrich batch --db catalog.db

    # Enrich only TV shows
    python -m kryten_playlist.catalog.enrich batch --tv-only --db catalog.db

    # Enrich only movies
    python -m kryten_playlist.catalog.enrich batch --movies-only --db catalog.db

Environment variables:
    LLM_API_KEY      - API key for the LLM service
    LLM_API_BASE     - Base URL (default: https://api.openai.com/v1)
    LLM_MODEL        - Model name (default: gpt-4o-mini)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import random
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite
import httpx
import json_repair

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# System prompt for consistent LLM output
SYSTEM_PROMPT = """You are a movie and TV show metadata expert. Your task is to provide accurate, structured metadata for the EXACT title provided.

CRITICAL INSTRUCTIONS:
1. ACCURACY IS PARAMOUNT. Do not guess. If you are not 100% sure about the specific movie/show, return null for uncertain fields.
2. STRICT DISAMBIGUATION:
   - YEAR: If a year is provided (e.g. "Title (1988)"), you MUST provide metadata for THAT specific version. Do NOT provide data for a modern reboot (e.g. 2024) or an earlier original.
   - MEDIUM: Distinguish between Animated and Live-Action. If the title is an animated series, do NOT list the cast of a live-action movie adaptation (and vice versa).
   - TYPE: 
     * "TV Movie" (made for television) is TV content.
     * "Miniseries" is TV content.
     * "Movie" implies a theatrical release.
3. SYNOPSIS: Write 1-2 sentences capturing the essence. No spoilers.
4. CAST: List up to 10 MAIN actors. Verify they were actually in THIS specific version (check the year!).
5. DIRECTOR: REQUIRED for movies. If unknown, use null.
6. RATINGS: Use standard MPAA (G, PG, PG-13, R, NC-17) for movies or TV ratings (TV-G, TV-14, TV-MA) for shows.
7. MOOD: Choose one: dark, light, comedic, dramatic, thrilling, heartwarming, disturbing, nostalgic, action-packed, cerebral, absurd, campy.

Respond ONLY with valid JSON matching this schema:
{
    "media_type": "Movie" | "TV Series" | "TV Movie" | "TV Special" | "Miniseries",
    "synopsis": "Brief 1-2 sentence description",
    "cast_list": ["Actor 1", "Actor 2", "Actor 3"],
    "director": "Director Name" or null,
    "genre": "Primary genre",
    "mood": "One of the mood options",
    "era": "Decade like 1990s",
    "content_rating": "Rating like R or TV-MA",
    "tags": ["tag1", "tag2", ...],
    "notes": "Brief context about this specific version (e.g. '1988 original series', 'Animated series')" or null
}"""


@dataclass
class EnrichmentResult:
    """Result of enriching a single item."""

    video_id: str
    title: str
    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    original_llm_data: dict[str, Any] | None = None  # Data before verification

    def display(self, compact: bool = False, original_data: dict[str, Any] | None = None) -> str:
        """Format for display."""
        if not self.success:
            return f"❌ {self.title}\n   Error: {self.error}"

        d = self.data or {}
        
        # Prepare comparison if original data is provided
        diff_lines = []
        if original_data:
            changes = []
            
            # Helper to format value
            def fmt_val(v: Any) -> str:
                if v is None: return "None"
                if isinstance(v, list): return ", ".join(str(x) for x in v[:3]) + ("..." if len(v)>3 else "")
                return str(v)

            # Compare key fields
            fields = ["genre", "mood", "era", "content_rating", "synopsis", "director", "cast_list", "tags"]
            for field in fields:
                old_val = original_data.get(field)
                new_val = d.get(field)
                
                # Normalize for comparison
                old_cmp = str(old_val).strip() if old_val else ""
                new_cmp = str(new_val).strip() if new_val else ""
                
                if field == "synopsis":
                    # For synopsis, just check if it changed significantly (length or content)
                    if old_cmp and new_cmp and old_cmp != new_cmp:
                         changes.append(f"   📝 Synopsis updated")
                elif old_cmp != new_cmp and (old_cmp or new_cmp):
                    changes.append(f"   🔄 {field.title()}: {fmt_val(old_val)} -> {fmt_val(new_val)}")
            
            if changes:
                diff_lines.append("\n   --- Changes from previous data ---")
                diff_lines.extend(changes)

        # Show verification changes if available
        if self.original_llm_data:
             ver_changes = []
             for k, v in self.original_llm_data.items():
                 if k in d and d[k] != v:
                     # Skip minor formatting differences
                     if str(d[k]).strip() == str(v).strip():
                         continue
                     ver_changes.append(f"   🕵️ Verified {k}: {str(v)} -> {str(d[k])}")
             
             if ver_changes:
                 diff_lines.append("\n   --- Verification Corrections ---")
                 diff_lines.extend(ver_changes)

        if compact:
            # One-line format for batch mode
            genre = d.get('genre', '?')
            mood = d.get('mood', '?')
            tags = ', '.join(d.get('tags', [])[:3])
            return f"✅ {genre} | {mood} | {tags}"

        # Full format
        lines = [
            f"\n{'='*70}",
            f"📌 {self.title}",
        ]
        
        media_type_label = d.get("media_type", "Unknown")
        
        if d.get("_is_tv_corrected"):
             lines.append(f"   ✨ FIXED: Identified as '{media_type_label}' (Rating: {d.get('content_rating')}), switching type to TV Show")
        
        if d.get("_is_movie_corrected"):
             lines.append(f"   🎬 FIXED: Identified as '{media_type_label}' (Rating: {d.get('content_rating')}), switching type to Movie")

        lines.append(f"   Type: {media_type_label} | Genre: {d.get('genre', '?')} | Mood: {d.get('mood', '?')} | Era: {d.get('era', '?')} | Rating: {d.get('content_rating', '?')}")
        
        synopsis = d.get('synopsis') or 'N/A'
        lines.append(f"   Synopsis: {synopsis}")

        tags = d.get('tags', [])
        if not isinstance(tags, list):
            tags = []
        lines.append(f"   Tags: {', '.join(str(t) for t in tags)}")
        
        if d.get("director"):
            lines.append(f"   Director: {d['director']}")
        if d.get("cast_list"):
            cast = d['cast_list']
            if isinstance(cast, list):
                lines.append(f"   Cast: {', '.join(str(c) for c in cast[:4])}")
            else:
                lines.append(f"   Cast: {cast}")
        if d.get("notes"):
            lines.append(f"   Notes: {d['notes'][:100]}")
            
        # Add comparison if available
        lines.extend(diff_lines)
            
        return "\n".join(lines)


import re

def sanitize_json_string(s: str) -> str:
    """Aggressively sanitize JSON string by removing all special characters."""
    # 1. Strip non-printable garbage (0x00-0x1F except \n \r \t which we handle next)
    # We remove ALL control characters including \n \r \t because they break JSON if unescaped
    # and we don't need formatting in the raw string for metadata.
    # We replace them with spaces to preserve word separation.
    
    # Replace common whitespace controls with space
    s = s.replace('\r', ' ')
    s = s.replace('\n', ' ')
    s = s.replace('\t', ' ')
    
    # Remove all other control characters
    s = re.sub(r'[\x00-\x1f\x7f]', '', s)
    
    # Handle invalid backslash escapes often produced by LLMs
    # \' -> '
    s = s.replace("\\'", "'")
    
    # Some models produce fancy quotes
    s = s.replace('“', '"').replace('”', '"')
    s = s.replace("‘", "'").replace("’", "'")
    
    return s

    # Step 4: Handle unescaped quotes inside strings.
    # The error "Expecting ',' delimiter: line 1 column 172" usually happens when a string ends prematurely
    # because of an unescaped double quote inside it, e.g. "synopsis": "The "best" movie".
    # This is extremely hard to fix perfectly with regex without a parser.
    # But for common cases like titles with quotes, we can try.
    # For now, we rely on the LLM being mostly correct, but if we see this error, it's usually unrecoverable 
    # without complex heuristics.
    
    return s


@dataclass
class LLMClient:
    """Client for calling LLM APIs."""

    api_key: str
    api_base: str = ""
    model: str = ""
    timeout: float = 240.0  # used in httpx.AsyncClient(timeout=...)

    async def _call_llm(self, messages: list[dict[str, str]]) -> str:
        """Helper to call LLM and return raw content."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if "openrouter.ai" in self.api_base:
            headers["HTTP-Referer"] = "https://github.com/grobertson/kryten-playlist"
            headers["X-Title"] = "kryten-playlist"

        # Special handling for OpenRouter: ensure the URL is correct
        # OpenRouter expects https://openrouter.ai/api/v1/chat/completions
        url = f"{self.api_base}/chat/completions"
        if "openrouter.ai" in self.api_base and not url.endswith("/chat/completions"):
             # If base is just https://openrouter.ai/api/v1, the f-string handles it.
             # If base is https://openrouter.ai, we need to add api/v1
             if "/api/v1" not in self.api_base:
                 url = f"{self.api_base}/api/v1/chat/completions"
        
        # If the user provided the full endpoint URL in api_base (e.g. /chat/completions), use it directly
        if self.api_base.endswith("/chat/completions"):
            url = self.api_base

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 500,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                )
                if resp.status_code != 200:
                    logger.error("LLM Request Failed!")
                    logger.error("URL: %s", resp.url)
                    logger.error("Status: %s", resp.status_code)
                    logger.error("Response Body: %s", resp.text)
                    resp.raise_for_status()
                
                data = resp.json()
                
                if "choices" not in data or not data["choices"]:
                    logger.error("Invalid LLM response format: %s", json.dumps(data))
                    raise ValueError("LLM response missing 'choices'")
                    
                return data["choices"][0]["message"]["content"]
                
        except httpx.RequestError as e:
            logger.error("Network error while calling LLM: %s", e)
            raise

    async def enrich(self, title: str, is_tv: bool, year: int | None = None, verify: bool = False, verifier_client: LLMClient | None = None, alternate_client: LLMClient | None = None) -> tuple[dict[str, Any], dict[str, Any] | None]:
        """Call LLM to get enrichment data for a title.
        
        Returns:
            Tuple of (final_data, original_data_if_verified)
        """
        media_type = "TV episode" if is_tv else "movie"
        year_hint = f" ({year})" if year else ""
        
        # Enhanced user prompt for disambiguation
        user_prompt = (
            f"Provide metadata for this {media_type}: '{title}'{year_hint}. "
            f"STRICTLY MATCH THE YEAR: {year if year else 'Unknown'}. "
            "If this is an older show/movie, do NOT provide data for a modern reboot. "
            "If this is an animated series, do NOT provide data for a live-action movie. "
            "Verify the cast list matches THIS specific version."
        )

        logger.info("Enriching %s with model %s at %s", title, self.model, self.api_base)
        
        # First pass
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        
        try:
            content = await self._call_llm(messages)
            data = self._parse_json_content(content)
        except (ValueError, Exception) as e:
            # If primary fails and we have an alternate, try it
            if alternate_client:
                logger.warning("Primary model failed for %s: %s. Trying alternate model %s...", title, e, alternate_client.model)
                try:
                    content = await alternate_client._call_llm(messages)
                    data = self._parse_json_content(content)
                except Exception as alt_e:
                    logger.error("Alternate model also failed for %s: %s", title, alt_e)
                    raise e # Raise original error or alt error? Probably original is more relevant if both fail, but let's just re-raise.
            else:
                raise e

        original_data = None
        
        # Optional verification pass
        if verify:
            original_data = data.copy() # Keep copy of original
            
            # Use the verifier client if provided, otherwise self
            v_client = verifier_client if verifier_client else self
            v_model_name = v_client.model
            
            logger.info("Verifying metadata for %s with model %s...", title, v_model_name)
            verify_prompt = (
                f"Review the following metadata for '{title}' {year_hint}. "
                "1. Check for hallucinations: Did you confuse this with a more popular movie/show? "
                "2. Verify the Cast: Ensure all listed actors were actually in this specific production. "
                "3. Verify the Director: Ensure the director is correct. "
                "4. Verify the Plot: Does the synopsis match this specific title/year? "
                "5. Verify the Media Type: Is this a 'Movie' (Theatrical) or 'TV Movie'/'TV Special'? "
                "   - If it is a TV Movie, Special, or Miniseries, set media_type accordingly. "
                "   - REMEMBER: TV Movies are TV content, NOT theatrical Movies. "
                "Return ONLY the corrected JSON.\n\n"
                f"{json.dumps(data, indent=2)}"
            )
            
            verify_messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": verify_prompt}
            ]
            
            try:
                content = await v_client._call_llm(verify_messages)
                data = self._parse_json_content(content)
            except Exception as e:
                logger.warning("Verification failed: %s. Keeping original data.", e)
                # If verification fails, we just keep the original data, but we might want to flag it?
                # For now, just logging warning and proceeding with unverified data is safer than failing.
                pass

        return data, original_data

    def _parse_json_content(self, content: str) -> dict[str, Any]:
        """Parse and sanitize JSON content."""
        if not content or not content.strip():
            logger.error("Empty content received from LLM")
            raise ValueError("LLM returned empty content")

        # Handle markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        else:
            # If no code blocks, look for the first '{' and last '}'
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                content = content[start_idx : end_idx + 1]
        
        # Sanitize content before parsing
        content = sanitize_json_string(content.strip())
        
        if not content:
            logger.error("Content became empty after sanitization")
            raise ValueError("Content became empty after sanitization")

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning("Standard JSON parse failed: %s. Attempting repair with json_repair...", e)
            
            try:
                # json_repair is much more robust at handling unescaped quotes, missing braces, etc.
                parsed = json_repair.loads(content)
                logger.info("JSON successfully repaired.")
            except Exception as repair_error:
                logger.error("Failed to repair JSON: %s", repair_error)
                
                # Log detailed debug info for the original error
                logger.error("Original JSON Error: %s", e)
                logger.error("Error at position %d, line %d, col %d", e.pos, e.lineno, e.colno)
                
                # Extract context around the error
                start = max(0, e.pos - 20)
                end = min(len(content), e.pos + 20)
                context = content[start:end]
                logger.error("Context around error: ...%s...", repr(context))
                
                # Log the character causing the issue if possible
                if e.pos < len(content):
                    bad_char = content[e.pos]
                    logger.error("Bad character code: %r (int: %d)", bad_char, ord(bad_char))
                
                logger.error("Raw content: %s", content)
                raise ValueError(f"Failed to parse LLM response as JSON (even after repair): {e}")

        # Ensure the result is a dictionary
        if not isinstance(parsed, dict):
             logger.error("LLM returned a non-dict JSON object: %s (type: %s)", parsed, type(parsed))
             raise ValueError(f"LLM returned invalid JSON type: {type(parsed).__name__}. Expected dict/object.")
             
        return parsed


async def enrich_item(
    conn: aiosqlite.Connection,
    llm: LLMClient,
    video_id: str,
    title: str,
    is_tv: bool,
    year: int | None,
    dry_run: bool = False,
    verify: bool = False,
    verifier_client: LLMClient | None = None,
    alternate_client: LLMClient | None = None,
) -> EnrichmentResult:
    """Enrich a single catalog item."""
    try:
        data, original_llm_data = await llm.enrich(title, is_tv, year, verify=verify, verifier_client=verifier_client, alternate_client=alternate_client)
        
        # Check if we need to fix the TV flag
        content_rating = str(data.get("content_rating", "")).upper()
        media_type = str(data.get("media_type", "")).lower()
        
        is_tv_corrected = False
        is_movie_corrected = False
        
        movie_ratings = ["G", "PG", "PG-13", "R", "NC-17", "R-17", "X", "NR", "UNRATED"]
        tv_types = ["tv series", "tv movie", "tv special", "miniseries"]
        
        # Priority 1: Media Type explicitly returned by LLM
        if media_type in tv_types and not is_tv:
             is_tv_corrected = True
             data["_is_tv_corrected"] = True
        elif media_type == "movie" and is_tv:
             is_movie_corrected = True
             data["_is_movie_corrected"] = True
        
        # Priority 2: Fallback to Content Rating if Media Type is ambiguous/missing
        elif content_rating.startswith("TV-") and not is_tv:
            is_tv_corrected = True
            # Update data to reflect this change for display
            data["_is_tv_corrected"] = True
        elif content_rating in movie_ratings and is_tv:
            is_movie_corrected = True
            data["_is_movie_corrected"] = True
            
        if not dry_run:
            # Update the database
            now = datetime.now(timezone.utc).isoformat()
            
            # If we detected it's a TV show but it wasn't marked as one, fix it
            if is_tv_corrected:
                await conn.execute(
                    "UPDATE catalog_item SET is_tv = 1 WHERE video_id = ?",
                    (video_id,)
                )
            
            # If we detected it's a Movie but it was marked as TV, fix it
            if is_movie_corrected:
                await conn.execute(
                    "UPDATE catalog_item SET is_tv = 0 WHERE video_id = ?",
                    (video_id,)
                )

            await conn.execute(
                """
                UPDATE catalog_item SET
                    synopsis = ?,
                    cast_list = ?,
                    director = ?,
                    genre = ?,
                    mood = ?,
                    era = ?,
                    content_rating = ?,
                    llm_notes = ?,
                    llm_enriched_at = ?,
                    updated_at = ?
                WHERE video_id = ?
                """,
                (
                    data.get("synopsis"),
                    json.dumps(data.get("cast_list")) if data.get("cast_list") else None,
                    data.get("director"),
                    data.get("genre"),
                    data.get("mood"),
                    data.get("era"),
                    data.get("content_rating"),
                    data.get("notes"),
                    now,
                    now,
                    video_id,
                ),
            )

            # Handle tags
            tags = data.get("tags", [])
            for tag_name in tags:
                # Ensure tag exists
                await conn.execute(
                    "INSERT OR IGNORE INTO catalog_tag (name, is_llm_generated) VALUES (?, 1)",
                    (tag_name.lower(),),
                )
                cursor = await conn.execute(
                    "SELECT id FROM catalog_tag WHERE name = ?", (tag_name.lower(),)
                )
                row = await cursor.fetchone()
                if row:
                    await conn.execute(
                        "INSERT OR IGNORE INTO catalog_item_tag (video_id, tag_id, confidence) VALUES (?, ?, 1.0)",
                        (video_id, row[0]),
                    )

            # We DO NOT commit here anymore to allow batch transaction management by the caller
            # await conn.commit()

        return EnrichmentResult(video_id=video_id, title=title, success=True, data=data, original_llm_data=original_llm_data)

    except Exception as e:
        logger.error("Error enriching %s: %s", title, e)
        return EnrichmentResult(video_id=video_id, title=title, success=False, error=str(e))


async def enrich_single(
    db_path: str,
    search_query: str,
    llm: LLMClient,
    dry_run: bool = False,
) -> None:
    """Enrich a single item by searching for it."""
    async with aiosqlite.connect(db_path) as conn:
        cursor = await conn.execute(
            """
            SELECT video_id, sanitized_title, is_tv, year
            FROM catalog_item
            WHERE sanitized_title LIKE ? OR title_base LIKE ?
            LIMIT 1
            """,
            (f"%{search_query}%", f"%{search_query}%"),
        )
        row = await cursor.fetchone()

        if not row:
            print(f"No item found matching '{search_query}'")
            return

        video_id, title, is_tv, year = row
        print(f"\n🔍 Found: {title}")
        print(f"   Type: {'TV' if is_tv else 'Movie'}, Year: {year or 'Unknown'}")
        print(f"   {'[DRY RUN]' if dry_run else ''}\n")
        print("Calling LLM...")

        result = await enrich_item(conn, llm, video_id, title, bool(is_tv), year, dry_run)
        print(result.display())


async def enrich_sample(
    db_path: str,
    count: int,
    llm: LLMClient,
    dry_run: bool = False,
    tv_only: bool = False,
    movies_only: bool = False,
    unenriched_only: bool = True,
    concurrency: int = 1,
    batch_size: int = 100,
    enriched_only: bool = False,
    verifier_client: LLMClient | None = None,
    alternate_client: LLMClient | None = None,
    delay: float = 0.5,
    jitter: int = 0,
) -> None:
    """Enrich a random sample of items."""
    # We can reuse enrich_batch logic by setting limit=count, random_order=True
    # and properly setting the filters.
    
    await enrich_batch(
        db_path=db_path,
        llm=llm,
        tv_only=tv_only,
        movies_only=movies_only,
        limit=count,
        delay=delay, # Use provided delay
        concurrency=concurrency,
        dry_run=dry_run,
        force_all=not unenriched_only, 
        raw_output=False,
        random_order=True,
        verify=verifier_client is not None, # Auto-enable verify if client provided
        batch_size=batch_size,
        enriched_only=enriched_only,
        verifier_client=verifier_client,
        alternate_client=alternate_client,
        jitter=jitter,
    )


def format_time_human(td: datetime.timedelta) -> str:
    """Format timedelta to human readable string (e.g. 2m 22s)."""
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or hours > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    
    if not parts:
        return "0s"
    return " ".join(parts)


def format_rate(rate_per_sec: float) -> str:
    """Format rate (items/sec) to human readable string."""
    if rate_per_sec >= 1.0:
        return f"{rate_per_sec:.1f} items/sec"
    
    rate_per_min = rate_per_sec * 60
    if rate_per_min >= 1.0:
        return f"{rate_per_min:.1f} items/min"
        
    rate_per_hour = rate_per_min * 60
    return f"{rate_per_hour:.1f} items/hour"


def format_avg_time(seconds_per_item: float) -> str:
    """Format average time per item to human readable string."""
    if seconds_per_item < 0.001:
        return f"{seconds_per_item*1000*1000:.0f} µs/item"
    if seconds_per_item < 1.0:
        return f"{seconds_per_item*1000:.0f} ms/item"
    if seconds_per_item < 60.0:
        return f"{seconds_per_item:.1f} s/item"
    
    minutes = seconds_per_item / 60
    return f"{minutes:.1f} m/item"


async def enrich_batch(
    db_path: str,
    llm: LLMClient,
    tv_only: bool = False,
    movies_only: bool = False,
    limit: int | None = None,
    delay: float = 0.5,
    concurrency: int = 1,
    dry_run: bool = False,
    force_all: bool = False,
    raw_output: bool = False,
    random_order: bool = False,
    verify: bool = False,
    batch_size: int = 100,
    enriched_only: bool = False,
    verifier_client: LLMClient | None = None,
    alternate_client: LLMClient | None = None,
    jitter: int = 0,
) -> None:
    """Enrich items with optional concurrency.
    
    Args:
        db_path: Path to SQLite database
        llm: LLM client instance
        tv_only: Only process TV episodes
        movies_only: Only process movies
        limit: Maximum items to process
        delay: Delay between API calls (per worker)
        concurrency: Number of concurrent API requests (default 1 = sequential)
        dry_run: If True, do not save changes to DB
        force_all: If True, process ALL items including already enriched ones
        raw_output: If True, output raw numbers instead of human-readable formats
        random_order: If True, process items in random order
        verify: If True, verify and correct the LLM response
        batch_size: Number of items to process before committing transaction
        enriched_only: If True, only process items that have already been enriched
        verifier_client: Optional second LLM client for verification
        alternate_client: Optional second LLM client for retrying failed enrichments
        jitter: Random jitter in milliseconds to add to delay
    """
    async with aiosqlite.connect(db_path) as conn:
        # Count total
        conditions = []
        if enriched_only:
            conditions.append("llm_enriched_at IS NOT NULL")
        elif not force_all:
            conditions.append("llm_enriched_at IS NULL")
            
        if tv_only:
            conditions.append("is_tv = 1")
        if movies_only:
            conditions.append("is_tv = 0")

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        cursor = await conn.execute(
            f"SELECT COUNT(*) FROM catalog_item {where_clause}"
        )
        total = (await cursor.fetchone())[0]

        if total == 0:
            print("No items found matching criteria.")
            return

        limit_clause = f"LIMIT {limit}" if limit else ""
        actual_count = min(total, limit) if limit else total

        print(f"\n🚀 Starting batch enrichment")
        print(f"   Total matching: {total}")
        print(f"   Processing: {actual_count}")
        print(f"   Mode: {'RE-PROCESS ALL' if force_all else 'Unenriched only'}")
        print(f"   Order: {'RANDOM' if random_order else 'Title'}")
        print(f"   Concurrency: {concurrency} worker{'s' if concurrency > 1 else ''}")
        print(f"   Delay between items: {delay}s")
        print(f"   Batch size: {batch_size}")
        if dry_run:
            print("   [DRY RUN] Changes will NOT be saved")
        print()

        order_clause = "ORDER BY RANDOM()" if random_order else "ORDER BY sanitized_title"

        # Use cursor iteration instead of fetchall to handle large datasets
        # But for concurrency, we need to buffer some items
        # Strategy: Fetch in chunks of batch_size
        
        # Shared state for progress tracking
        completed = 0
        success_count = 0
        error_count = 0
        tv_corrected_count = 0
        movie_corrected_count = 0
        start_time = datetime.now()
        lock = asyncio.Lock()
        semaphore = asyncio.Semaphore(concurrency)

        async def process_item(idx: int, video_id: str, title: str, is_tv: int, year: int | None) -> EnrichmentResult:
            """Process a single item with semaphore control."""
            nonlocal completed, success_count, error_count, tv_corrected_count, movie_corrected_count

            async with semaphore:
                # Add delay to spread out requests
                # Initial startup delay (staggered)
                if idx < concurrency and concurrency > 1:
                     await asyncio.sleep(0.5 * idx)
                
                # Rate limit delay
                if delay > 0 or jitter > 0:
                    wait_time = delay
                    if jitter > 0:
                        wait_time += random.uniform(0, jitter / 1000.0)
                    
                    if wait_time > 0:
                        await asyncio.sleep(wait_time)

                # Fetch existing data for comparison if verification or force_all is on
                original_data = None
                if force_all or verify:
                    cursor = await conn.execute(
                        "SELECT genre, mood, era, content_rating, synopsis, director, cast_list FROM catalog_item WHERE video_id = ?",
                        (video_id,)
                    )
                    row = await cursor.fetchone()
                    if row:
                        # aiosqlite.Row can be converted to dict if row_factory is set, but sometimes it behaves like a tuple
                        # if accessed directly. Let's be safe.
                        if isinstance(row, dict):
                            original_data = row
                        else:
                            # It's likely a sqlite3.Row object which behaves like a dict but dict() constructor might fail
                            # if it iterates keys as tuples? No, dict(row) should work for sqlite3.Row.
                            # The error "dictionary update sequence element #0 has length 15; 2 is required" implies
                            # dict() is iterating over something that isn't (key, value) pairs.
                            # This happens if 'row' is just a tuple of values, not a Row object with keys.
                            # But we set conn.row_factory in other places. Let's check if it's set here.
                            # It's not explicitly set in enrich_batch.
                            
                            # Fallback: manual mapping
                            keys = ["genre", "mood", "era", "content_rating", "synopsis", "director", "cast_list"]
                            original_data = {k: row[i] for i, k in enumerate(keys)}

                        # cast_list is stored as JSON string
                        if original_data.get("cast_list"):
                            try:
                                original_data["cast_list"] = json.loads(original_data["cast_list"])
                            except:
                                pass

                result = await enrich_item(conn, llm, video_id, title, bool(is_tv), year, dry_run=dry_run, verify=verify, verifier_client=verifier_client, alternate_client=alternate_client)

                async with lock:
                    completed += 1
                    if result.success:
                        success_count += 1
                        if result.data and result.data.get("_is_tv_corrected"):
                            tv_corrected_count += 1
                        if result.data and result.data.get("_is_movie_corrected"):
                            movie_corrected_count += 1
                    else:
                        error_count += 1

                    # Calculate progress
                    elapsed = datetime.now() - start_time
                    rate = completed / max(elapsed.total_seconds(), 1)
                    eta = (actual_count - completed) / rate if rate > 0 else 0

                    media_type = "📺" if is_tv else "🎬"
                    if year and not title.strip().endswith(f"({year})"):
                        year_str = f"({year})"
                    else:
                        year_str = ""
                    
                    print(f"\n[{completed}/{actual_count}] {media_type} {title} {year_str}")
                    print(result.display(original_data=original_data))

                    # Progress every 50 items
                    if completed % 50 == 0:
                        print(f"\n{'='*70}")
                        print(f"   📊 Progress: {completed}/{actual_count} ({100*completed/actual_count:.1f}%) | Success: {success_count} | Errors: {error_count} | ETA: {eta/60:.1f}m")
                        print(f"{'='*70}")

                return result

        # Fetch in chunks
        offset = 0
        remaining = actual_count
        
        while remaining > 0:
            current_limit = min(batch_size, remaining)
            
            # Note: OFFSET can be slow for large tables, but keyset pagination requires consistent ordering logic
            # Since we might use random ordering, OFFSET is necessary.
            # However, if we are updating items (llm_enriched_at IS NOT NULL), they will fall out of the filter criteria naturally
            # if we re-run the query without OFFSET. 
            # BUT if dry_run=True, they stay.
            # AND if random_order=True, the order changes every query.
            
            # To be safe and simple for now: fetch with LIMIT/OFFSET if dry_run or force_all
            # If standard mode (unenriched only) and not dry_run, we can just grab LIMIT batch_size repeatedly?
            # No, concurrent updates might not commit immediately, so they might still show up.
            
            # Best approach: Fetch ALL IDs first (lightweight), then process in chunks.
            if offset == 0:
                # Only run the query once to get IDs
                id_cursor = await conn.execute(
                    f"""
                    SELECT video_id, sanitized_title, is_tv, year
                    FROM catalog_item
                    {where_clause}
                    {order_clause}
                    {limit_clause}
                    """
                )
                all_rows = await id_cursor.fetchall()
                # Now we iterate over this list in memory (it's list of tuples, memory efficient enough for <100k items)
            
            chunk = all_rows[offset : offset + current_limit]
            if not chunk:
                break
                
            # Process chunk concurrently
            tasks = [
                process_item(i + offset, video_id, title, is_tv, year)
                for i, (video_id, title, is_tv, year) in enumerate(chunk)
            ]
            
            await asyncio.gather(*tasks)
            
            # Commit after each batch if not dry run
            if not dry_run:
                await conn.commit()
                
            offset += len(chunk)
            remaining -= len(chunk)

        elapsed = datetime.now() - start_time
        total_seconds = elapsed.total_seconds()
        items_per_second = completed / max(total_seconds, 1)
        seconds_per_item = total_seconds / max(completed, 1)
        avg_ms = seconds_per_item * 1000
        failure_rate = (error_count / completed * 100) if completed > 0 else 0.0

        print(f"\n{'='*60}")
        print(f"Batch complete!")
        print(f"   Enriched: {success_count}")
        print(f"   Errors: {error_count} ({failure_rate:.1f}%)")
        if tv_corrected_count > 0:
            print(f"   Fixed TV Types: {tv_corrected_count}")
        if movie_corrected_count > 0:
            print(f"   Fixed Movie Types: {movie_corrected_count}")
        
        if raw_output:
            print(f"   Time: {elapsed}")
            print(f"   Rate: {items_per_second:.1f} items/sec")
            print(f"   Avg: {avg_ms:.1f} ms/item")
            if concurrency > 1:
                print(f"   Effective rate: {items_per_second:.1f} items/sec")
        else:
            print(f"   Time: {format_time_human(elapsed)}")
            print(f"   Rate: {format_rate(items_per_second)}")
            print(f"   Avg: {format_avg_time(seconds_per_item)}")
            if concurrency > 1:
                print(f"   Effective rate: {format_rate(items_per_second)}")



async def show_enriched_stats(db_path: str) -> None:
    """Show statistics about enrichment progress."""
    async with aiosqlite.connect(db_path) as conn:
        cursor = await conn.execute("SELECT COUNT(*) FROM catalog_item")
        total = (await cursor.fetchone())[0]

        cursor = await conn.execute(
            "SELECT COUNT(*) FROM catalog_item WHERE llm_enriched_at IS NOT NULL"
        )
        enriched = (await cursor.fetchone())[0]

        cursor = await conn.execute(
            "SELECT COUNT(*) FROM catalog_item WHERE llm_enriched_at IS NOT NULL AND is_tv = 1"
        )
        enriched_tv = (await cursor.fetchone())[0]

        cursor = await conn.execute(
            "SELECT COUNT(*) FROM catalog_item WHERE llm_enriched_at IS NOT NULL AND is_tv = 0"
        )
        enriched_movies = (await cursor.fetchone())[0]

        cursor = await conn.execute("SELECT COUNT(*) FROM catalog_tag WHERE is_llm_generated = 1")
        tags = (await cursor.fetchone())[0]

        cursor = await conn.execute(
            "SELECT genre, COUNT(*) as cnt FROM catalog_item WHERE genre IS NOT NULL GROUP BY genre ORDER BY cnt DESC LIMIT 10"
        )
        genres = await cursor.fetchall()

        cursor = await conn.execute(
            "SELECT mood, COUNT(*) as cnt FROM catalog_item WHERE mood IS NOT NULL GROUP BY mood ORDER BY cnt DESC LIMIT 10"
        )
        moods = await cursor.fetchall()

        print(f"\n📊 Enrichment Progress")
        print("=" * 50)
        print(f"  Total items:     {total:,}")
        print(f"  Enriched:        {enriched:,} ({100*enriched/total:.1f}%)" if total else "")
        print(f"    TV episodes:   {enriched_tv:,}")
        print(f"    Movies:        {enriched_movies:,}")
        print(f"  Remaining:       {total - enriched:,}")
        print(f"  LLM-generated tags: {tags}")
        print()

        if genres:
            print("  Top Genres:")
            for genre, cnt in genres[:5]:
                print(f"    {genre}: {cnt}")
            print()

        if moods:
            print("  Top Moods:")
            for mood, cnt in moods[:5]:
                print(f"    {mood}: {cnt}")
            print()


def get_llm_client() -> LLMClient:
    """Create LLM client from environment variables."""
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        print("Error: LLM_API_KEY environment variable is required")
        print("\nSet it with:")
        print("  $env:LLM_API_KEY = 'your-api-key'  # PowerShell")
        print("  export LLM_API_KEY='your-api-key'  # Bash")
        sys.exit(1)

    return LLMClient(
        api_key=api_key,
        api_base=os.environ.get("LLM_API_BASE", "https://api.openai.com/v1"),
        model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enrich catalog items with LLM-generated metadata",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Test on a specific movie
    python -m kryten_playlist.catalog.enrich single "The Matrix"

    # Test on 5 random items without saving
    python -m kryten_playlist.catalog.enrich sample --count 5 --dry-run

    # Enrich 20 random movies
    python -m kryten_playlist.catalog.enrich sample --count 20 --movies-only

    # Enrich all unenriched items
    python -m kryten_playlist.catalog.enrich batch

    # Check progress
    python -m kryten_playlist.catalog.enrich status
        """,
    )

    parser.add_argument(
        "--db",
        default="data/catalog.db",
        help="SQLite database path (default: data/catalog.db)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Single item
    single_parser = subparsers.add_parser("single", help="Enrich a single item by title search")
    single_parser.add_argument("query", help="Title search query")
    single_parser.add_argument("--dry-run", action="store_true", help="Don't save results")

    # Sample
    sample_parser = subparsers.add_parser("sample", help="Enrich a random sample")
    sample_parser.add_argument("--count", type=int, default=5, help="Number of items (default: 5)")
    sample_parser.add_argument("--dry-run", action="store_true", help="Don't save results")
    sample_parser.add_argument("--tv-only", action="store_true", help="Only TV episodes")
    sample_parser.add_argument("--movies-only", action="store_true", help="Only movies")
    sample_parser.add_argument("--include-enriched", action="store_true", help="Include already enriched items")
    sample_parser.add_argument("--concurrency", "-c", type=int, default=1, help="Number of concurrent API requests (default: 1)")
    sample_parser.add_argument("--batch-size", type=int, default=100, help="Batch size for DB commits (default: 100)")

    # Batch
    batch_parser = subparsers.add_parser("batch", help="Enrich all unenriched items")
    batch_parser.add_argument("--tv-only", action="store_true", help="Only TV episodes")
    batch_parser.add_argument("--movies-only", action="store_true", help="Only movies")
    batch_parser.add_argument("--limit", type=int, help="Max items to process")
    batch_parser.add_argument("--delay", type=float, default=0.5, help="Delay between API calls (default: 0.5s)")
    batch_parser.add_argument("--concurrency", "-c", type=int, default=1, help="Number of concurrent API requests (default: 1)")
    batch_parser.add_argument("--dry-run", action="store_true", help="Don't save results")
    batch_parser.add_argument("--batch-size", type=int, default=100, help="Batch size for DB commits (default: 100)")

    # Status
    subparsers.add_parser("status", help="Show enrichment progress")

    args = parser.parse_args()

    if args.command == "status":
        asyncio.run(show_enriched_stats(args.db))
        return

    # Other commands need LLM client
    llm = get_llm_client()
    print(f"Using LLM: {llm.model} @ {llm.api_base}")

    if args.command == "single":
        asyncio.run(enrich_single(args.db, args.query, llm, args.dry_run))

    elif args.command == "sample":
        asyncio.run(
            enrich_sample(
                args.db,
                args.count,
                llm,
                args.dry_run,
                args.tv_only,
                args.movies_only,
                unenriched_only=not args.include_enriched,
                concurrency=args.concurrency,
                batch_size=args.batch_size,
            )
        )

    elif args.command == "batch":
        asyncio.run(
            enrich_batch(
                args.db,
                llm,
                args.tv_only,
                args.movies_only,
                args.limit,
                args.delay,
                args.concurrency,
                dry_run=args.dry_run,
                batch_size=args.batch_size,
            )
        )


if __name__ == "__main__":
    main()
