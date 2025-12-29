"""Title sanitization and parsing utilities.

Transforms messy filenames into clean, structured titles:
- "Movie.Name.2020.1080p.BluRay.x264.mkv" → "Movie Name (2020)"
- "Show.Name.S01E04.Episode.Title.720p.HDTV.mp4" → "Show Name - S01E04 - Episode Title"
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


# Common patterns to strip from titles
_EXTENSIONS = re.compile(r"\.(mkv|mp4|avi|mov|wmv|flv|webm|m4v|ts|m2ts)$", re.I)
_ENCODING = re.compile(
    r"[\[\(]?"
    r"(x264|x265|h\.?264|h\.?265|hevc|avc|xvid|divx|"
    r"1080p|720p|480p|2160p|4k|uhd|"
    r"bluray|blu-ray|bdrip|brrip|dvdrip|hdtv|webrip|web-dl|webdl|hdrip|"
    r"aac|ac3|dts|flac|mp3|"
    r"5\.1|7\.1|"
    r"repack|proper|extended|unrated|directors\.?cut|"
    r"yify|yts|rarbg|ettv|eztv|lol|dimension|"
    r"\d{3,4}mb)"
    r"[\]\)]?",
    re.I,
)
_YEAR_PATTERN = re.compile(r"[\.\s\-_\[\(]*((?:19|20)\d{2})[\.\s\-_\]\)]*")
_EPISODE_PATTERN = re.compile(
    r"[.\s\-_]*[Ss](\d{1,2})[.\s\-_]*[Ee](\d{1,3})[.\s\-_]*",
)
_EPISODE_PATTERN_ALT = re.compile(r"[.\s\-_]*(\d{1,2})x(\d{1,3})[.\s\-_]*")
_TRAILING_JUNK = re.compile(r"[\s\.\-_]+$")
_LEADING_JUNK = re.compile(r"^[\s\.\-_]+")
_MULTI_SPACE = re.compile(r"\s{2,}")


@dataclass
class ParsedTitle:
    """Result of parsing a raw title."""

    raw: str
    """Original title as received."""

    sanitized: str
    """Clean, human-readable title."""

    title_base: str
    """Base title without year/episode info."""

    year: int | None = None
    """Release year if detected (for movies)."""

    season: int | None = None
    """Season number if detected (for TV)."""

    episode: int | None = None
    """Episode number if detected (for TV)."""

    episode_title: str | None = None
    """Episode title if detected (for TV)."""

    is_tv: bool = False
    """True if this appears to be a TV episode."""

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw": self.raw,
            "sanitized": self.sanitized,
            "title_base": self.title_base,
            "year": self.year,
            "season": self.season,
            "episode": self.episode,
            "episode_title": self.episode_title,
            "is_tv": self.is_tv,
        }


def _clean_separators(s: str) -> str:
    """Replace dots/underscores with spaces, collapse multiple spaces."""
    s = s.replace(".", " ").replace("_", " ")
    s = _MULTI_SPACE.sub(" ", s)
    return s.strip()


def _strip_encoding(s: str) -> str:
    """Remove encoding/quality markers."""
    # Iteratively strip encoding patterns
    prev = ""
    while prev != s:
        prev = s
        s = _ENCODING.sub(" ", s)
    return s


def _extract_year(s: str) -> tuple[str, int | None]:
    """Extract year from string, return (remaining, year)."""
    match = _YEAR_PATTERN.search(s)
    if match:
        year = int(match.group(1))
        # Only accept reasonable years
        if 1900 <= year <= 2099:
            # Remove the year from string
            s = s[: match.start()] + " " + s[match.end() :]
            return s, year
    return s, None


def _extract_episode(s: str) -> tuple[str, int | None, int | None, str | None]:
    """Extract season/episode from string.

    Returns (remaining, season, episode, episode_title).
    """
    # Try S01E01 format
    match = _EPISODE_PATTERN.search(s)
    if match:
        season = int(match.group(1))
        episode = int(match.group(2))
        before = s[: match.start()]
        after = s[match.end() :]
        # After the episode marker is usually the episode title
        episode_title = _clean_separators(_strip_encoding(after))
        episode_title = _TRAILING_JUNK.sub("", episode_title)
        episode_title = _LEADING_JUNK.sub("", episode_title)
        if len(episode_title) < 2:
            episode_title = None
        return before, season, episode, episode_title

    # Try 1x01 format
    match = _EPISODE_PATTERN_ALT.search(s)
    if match:
        season = int(match.group(1))
        episode = int(match.group(2))
        before = s[: match.start()]
        after = s[match.end() :]
        episode_title = _clean_separators(_strip_encoding(after))
        episode_title = _TRAILING_JUNK.sub("", episode_title)
        episode_title = _LEADING_JUNK.sub("", episode_title)
        if len(episode_title) < 2:
            episode_title = None
        return before, season, episode, episode_title

    return s, None, None, None


def parse_title(raw: str) -> ParsedTitle:
    """Parse a raw title into structured components.

    Examples:
        >>> parse_title("Movie.Name.2020.1080p.BluRay.x264.mkv")
        ParsedTitle(sanitized="Movie Name (2020)", ...)

        >>> parse_title("Show.Name.S01E04.Episode.Title.720p.HDTV.mp4")
        ParsedTitle(sanitized="Show Name - S01E04 - Episode Title", ...)
    """
    s = raw

    # Strip file extension
    s = _EXTENSIONS.sub("", s)

    # Strip encoding markers
    s = _strip_encoding(s)

    # Try to extract episode info first (before year, as some shows have years)
    before_ep, season, episode, episode_title = _extract_episode(s)

    if season is not None and episode is not None:
        # This is a TV show
        title_base = _clean_separators(before_ep)
        title_base = _TRAILING_JUNK.sub("", title_base)

        ep_code = f"S{season:02d}E{episode:02d}"
        if episode_title:
            sanitized = f"{title_base} - {ep_code} - {episode_title}"
        else:
            sanitized = f"{title_base} - {ep_code}"

        return ParsedTitle(
            raw=raw,
            sanitized=sanitized,
            title_base=title_base,
            season=season,
            episode=episode,
            episode_title=episode_title,
            is_tv=True,
        )

    # Not a TV show, try to extract year (movie)
    s, year = _extract_year(s)
    title_base = _clean_separators(s)
    title_base = _TRAILING_JUNK.sub("", title_base)
    title_base = _LEADING_JUNK.sub("", title_base)

    if year:
        sanitized = f"{title_base} ({year})"
    else:
        sanitized = title_base

    return ParsedTitle(
        raw=raw,
        sanitized=sanitized,
        title_base=title_base,
        year=year,
        is_tv=False,
    )


def sanitize_title(raw: str) -> str:
    """Convenience function to just get the sanitized title string."""
    return parse_title(raw).sanitized
