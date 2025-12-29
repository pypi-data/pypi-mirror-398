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
SYSTEM_PROMPT = """You are a movie and TV show metadata expert. Given a title, provide structured metadata.

IMPORTANT RULES:
1. For synopsis, write 1-2 sentences that capture the essence without spoilers.
2. For cast_list, provide up to 10 actors. Include supporting cast if known, but strictly exclude any uncertain names to avoid hallucinations.
3. For tags, include 3-8 relevant tags covering genre, themes, tone, and notable aspects.
4. For era, use decade format like "1980s", "2010s", or "classic" for pre-1970.
5. For mood, choose from: dark, light, comedic, dramatic, thrilling, heartwarming, disturbing, nostalgic, action-packed, cerebral, absurd, campy.
6. For content_rating, use MPAA (G, PG, PG-13, R, NC-17) for movies or TV ratings (TV-G, TV-PG, TV-14, TV-MA) for shows.

Respond ONLY with valid JSON matching this schema:
{
    "synopsis": "Brief 1-2 sentence description",
    "cast_list": ["Actor 1", "Actor 2", "Actor 3"],
    "director": "Director Name" or null,
    "genre": "Primary genre",
    "mood": "One of the mood options",
    "era": "Decade like 1990s",
    "content_rating": "Rating like R or TV-MA",
    "tags": ["tag1", "tag2", ...],
    "notes": "Any interesting trivia or context" or null
}"""


@dataclass
class EnrichmentResult:
    """Result of enriching a single item."""

    video_id: str
    title: str
    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None

    def display(self, compact: bool = False) -> str:
        """Format for display."""
        if not self.success:
            return f"❌ {self.title}\n   Error: {self.error}"

        d = self.data or {}

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
            f"   Genre: {d.get('genre', '?')} | Mood: {d.get('mood', '?')} | Era: {d.get('era', '?')} | Rating: {d.get('content_rating', '?')}",
            f"   Synopsis: {d.get('synopsis', 'N/A')}",
            f"   Tags: {', '.join(d.get('tags', []))}",
        ]
        if d.get("director"):
            lines.append(f"   Director: {d['director']}")
        if d.get("cast_list"):
            lines.append(f"   Cast: {', '.join(d['cast_list'][:4])}")
        if d.get("notes"):
            lines.append(f"   Notes: {d['notes'][:100]}")
        return "\n".join(lines)


import re

def sanitize_json_string(s: str) -> str:
    """Remove control characters that are invalid in JSON."""
    # JSON standard (RFC 8259) requires control characters (U+0000 through U+001F) 
    # to be escaped in strings.
    # Newlines (\n, \r) and tabs (\t) are technically valid whitespace outside strings,
    # but INSIDE strings they must be escaped as \\n, \\r, \\t.
    # LLMs often return raw unescaped newlines inside JSON strings, which breaks parsers.
    
    # Strategy:
    # 1. Remove truly garbage control chars (0x00-0x08, 0x0b, 0x0c, 0x0e-0x1f) globally.
    # 2. Handle \r, \n, \t by escaping them if they appear raw.
    
    # Step 1: Strip non-printable garbage
    s = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', s)
    
    # Step 2: Handle raw newlines/tabs. 
    # A robust approach without a full parser is tricky, but often LLM output 
    # is "mostly" valid JSON with just unescaped newlines in text fields.
    # We can try to escape them.
    # HOWEVER, raw newlines are valid JSON *formatting* (outside strings).
    # Replacing ALL \n with \\n breaks the JSON structure itself.
    
    # Given the logs show errors like "Invalid control character at... line 2",
    # it implies the parser sees a raw newline inside a string literal.
    
    # Simple, aggressive fix for "uncensored" models that are messy:
    # Replace raw \r\n, \r, \n with just a space or \\n?
    # Replacing with space is safest for metadata fields (synopsis) to avoid breaking JSON structure.
    # But we must be careful not to merge words.
    
    # Better approach for this specific issue (control char in string):
    # Use a regex to find control chars that are NOT part of JSON whitespace.
    # But standard python json.loads allows newlines between tokens.
    
    # The error "Invalid control character at..." specifically comes from unescaped 
    # control characters INSIDE a string.
    
    # Let's use a specialized function to escape control characters within strings only?
    # That's hard with regex.
    
    # Pragmatic fix:
    # Most LLMs output formatted JSON. 
    # If we strip all newlines, we might break it if it relies on newlines for separation (unlikely for valid JSON).
    # But wait, json.loads() handles whitespace fine. 
    # The error happens when \n is INSIDE a quote.
    
    # Let's try `strict=False` in json.loads if possible? 
    # Python's json module usually allows control characters if `strict=False`... 
    # actually no, strict=False allows non-standard numbers etc, but spec still bans unescaped controls.
    
    # Aggressive fix that usually works for metadata:
    # Replace raw newlines with escaped newlines.
    # BUT we can't distinguish between formatting-newlines and content-newlines easily.
    
    # Alternative: The user logs show raw \n (int 10).
    # "synopsis": "...\n\nIn this episode..."
    # This is definitely an unescaped newline in a string.
    
    # We will replace raw \n with \\n. 
    # Wait, if we replace ALL \n with \\n, then:
    # {
    #   "key": "val"
    # }
    # becomes {\n  "key": "val"\n} which is INVALID JSON because braces can't contain escaped newlines as tokens.
    
    # Compromise:
    # Since we are dealing with simple metadata, maybe we can just strip ALL raw newlines and tabs?
    # JSON doesn't require newlines for formatting.
    # "synopsis": "Line 1\nLine 2" -> "synopsis": "Line 1 Line 2"
    # This is acceptable for this use case.
    
    s = s.replace('\r', ' ')
    s = s.replace('\n', ' ')
    s = s.replace('\t', ' ')
    
    # Step 3: Handle invalid backslash escapes (like \') which LLMs often output for apostrophes.
    # JSON strings only allow specific escapes: \" \\ \/ \b \f \n \r \t \uXXXX
    # \' is NOT a valid JSON escape sequence.
    
    # We replace \' with just ' (apostrophe)
    s = s.replace("\\'", "'")

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

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 500,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.api_base}/chat/completions",
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

    async def enrich(self, title: str, is_tv: bool, year: int | None = None, verify: bool = False) -> dict[str, Any]:
        """Call LLM to get enrichment data for a title."""
        media_type = "TV episode" if is_tv else "movie"
        year_hint = f" ({year})" if year else ""
        user_prompt = f"Provide metadata for this {media_type}: {title}{year_hint}"

        logger.info("Enriching %s with model %s at %s", title, self.model, self.api_base)
        
        # First pass
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        content = await self._call_llm(messages)
        data = self._parse_json_content(content)
        
        # Optional verification pass
        if verify:
            logger.info("Verifying metadata for %s...", title)
            verify_prompt = (
                f"Review the following metadata for '{title}' {year_hint}. "
                "Correct any factual errors (e.g. wrong director, cast, year, genre). "
                "STRICTLY VERIFY the cast list: remove any actors who were not in this specific production. Add missing key actors if known. "
                "Ensure the JSON schema is preserved. Return ONLY the corrected JSON.\n\n"
                f"{json.dumps(data, indent=2)}"
            )
            
            verify_messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": verify_prompt}
            ]
            content = await self._call_llm(verify_messages)
            data = self._parse_json_content(content)

        return data

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
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning("Standard JSON parse failed: %s. Attempting repair with json_repair...", e)
            
            try:
                # json_repair is much more robust at handling unescaped quotes, missing braces, etc.
                repaired_obj = json_repair.loads(content)
                logger.info("JSON successfully repaired.")
                return repaired_obj
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


async def enrich_item(
    conn: aiosqlite.Connection,
    llm: LLMClient,
    video_id: str,
    title: str,
    is_tv: bool,
    year: int | None,
    dry_run: bool = False,
    verify: bool = False,
) -> EnrichmentResult:
    """Enrich a single catalog item."""
    try:
        data = await llm.enrich(title, is_tv, year, verify=verify)
        
        # Check if we need to fix the TV flag
        content_rating = str(data.get("content_rating", "")).upper()
        is_tv_corrected = False
        is_movie_corrected = False
        
        movie_ratings = ["G", "PG", "PG-13", "R", "NC-17", "X"]
        
        if content_rating.startswith("TV-") and not is_tv:
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

            await conn.commit()

        return EnrichmentResult(video_id=video_id, title=title, success=True, data=data)

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
) -> None:
    """Enrich a random sample of items."""
    async with aiosqlite.connect(db_path) as conn:
        # Build query
        conditions = []
        if unenriched_only:
            conditions.append("llm_enriched_at IS NULL")
        if tv_only:
            conditions.append("is_tv = 1")
        if movies_only:
            conditions.append("is_tv = 0")

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        cursor = await conn.execute(
            f"""
            SELECT video_id, sanitized_title, is_tv, year
            FROM catalog_item
            {where_clause}
            ORDER BY RANDOM()
            LIMIT ?
            """,
            (count,),
        )
        rows = await cursor.fetchall()

        if not rows:
            print("No matching items found.")
            return

        print(f"\n📋 Enriching {len(rows)} items {'[DRY RUN]' if dry_run else ''}\n")

        success_count = 0
        for i, (video_id, title, is_tv, year) in enumerate(rows, 1):
            print(f"[{i}/{len(rows)}] Processing: {title[:60]}...")
            result = await enrich_item(conn, llm, video_id, title, bool(is_tv), year, dry_run)
            print(result.display())
            print()

            if result.success:
                success_count += 1

            # Small delay to avoid rate limits
            if i < len(rows):
                await asyncio.sleep(0.5)

        print(f"\n{'='*60}")
        print(f"Complete: {success_count}/{len(rows)} items enriched successfully")


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
    """
    async with aiosqlite.connect(db_path) as conn:
        # Count total
        conditions = []
        if not force_all:
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
        if dry_run:
            print("   [DRY RUN] Changes will NOT be saved")
        print()

        order_clause = "ORDER BY RANDOM()" if random_order else "ORDER BY sanitized_title"

        cursor = await conn.execute(
            f"""
            SELECT video_id, sanitized_title, is_tv, year
            FROM catalog_item
            {where_clause}
            {order_clause}
            {limit_clause}
            """
        )
        rows = await cursor.fetchall()

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
                if idx > 0 and delay > 0:
                    await asyncio.sleep(delay * (idx % concurrency) / concurrency)

                result = await enrich_item(conn, llm, video_id, title, bool(is_tv), year, dry_run=dry_run, verify=verify)

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
                    # If the title already ends with (YYYY), don't append it again
                    if year and not title.strip().endswith(f"({year})"):
                        year_str = f"({year})"
                    else:
                        year_str = ""
                    
                    print(f"\n[{completed}/{actual_count}] {media_type} {title} {year_str}")

                    if result.success:
                        d = result.data or {}
                        
                        if d.get("_is_tv_corrected"):
                             print(f"   ✨ FIXED: Content rating is {d.get('content_rating')}, switching type to TV Show")
                        
                        if d.get("_is_movie_corrected"):
                             print(f"   🎬 FIXED: Content rating is {d.get('content_rating')}, switching type to Movie")

                        print(f"   Genre: {d.get('genre', '?')} | Mood: {d.get('mood', '?')} | Era: {d.get('era', '?')} | Rating: {d.get('content_rating', '?')}")
                        synopsis = d.get('synopsis') or 'N/A'
                        
                        # Intelligently truncate synopsis at the nearest word boundary
                        display_limit = 160
                        if len(synopsis) > display_limit:
                            truncated = synopsis[:display_limit]
                            # Try to cut at the last space to avoid splitting words
                            last_space = truncated.rfind(' ')
                            if last_space > display_limit // 2:  # Only cut at space if it's not too early
                                truncated = truncated[:last_space]
                            print(f"   Synopsis: {truncated}...")
                        else:
                            print(f"   Synopsis: {synopsis}")
                            
                        print(f"   Tags: {', '.join(d.get('tags', []))}")
                        if d.get('director'):
                            print(f"   Director: {d['director']}")
                        if d.get('cast_list'):
                            print(f"   Cast: {', '.join(d['cast_list'][:4])}")
                    else:
                        print(f"   ❌ Error: {result.error[:60] if result.error else 'Unknown error'}")

                    # Progress every 50 items
                    if completed % 50 == 0:
                        print(f"\n{'='*70}")
                        print(f"   📊 Progress: {completed}/{actual_count} ({100*completed/actual_count:.1f}%) | Success: {success_count} | Errors: {error_count} | ETA: {eta/60:.1f}m")
                        print(f"{'='*70}")

                return result

        # Process items concurrently
        if concurrency > 1:
            # Create tasks for all items
            tasks = [
                process_item(i, video_id, title, is_tv, year)
                for i, (video_id, title, is_tv, year) in enumerate(rows)
            ]
            await asyncio.gather(*tasks)
        else:
            # Sequential processing (original behavior)
            for i, (video_id, title, is_tv, year) in enumerate(rows):
                await process_item(i, video_id, title, is_tv, year)
                if i < len(rows) - 1:
                    await asyncio.sleep(delay)

        elapsed = datetime.now() - start_time
        total_seconds = elapsed.total_seconds()
        items_per_second = completed / max(total_seconds, 1)
        seconds_per_item = total_seconds / max(completed, 1)
        avg_ms = seconds_per_item * 1000

        print(f"\n{'='*60}")
        print(f"Batch complete!")
        print(f"   Enriched: {success_count}")
        print(f"   Errors: {error_count}")
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

    # Batch
    batch_parser = subparsers.add_parser("batch", help="Enrich all unenriched items")
    batch_parser.add_argument("--tv-only", action="store_true", help="Only TV episodes")
    batch_parser.add_argument("--movies-only", action="store_true", help="Only movies")
    batch_parser.add_argument("--limit", type=int, help="Max items to process")
    batch_parser.add_argument("--delay", type=float, default=0.5, help="Delay between API calls (default: 0.5s)")
    batch_parser.add_argument("--concurrency", "-c", type=int, default=1, help="Number of concurrent API requests (default: 1)")

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
            )
        )


if __name__ == "__main__":
    main()
