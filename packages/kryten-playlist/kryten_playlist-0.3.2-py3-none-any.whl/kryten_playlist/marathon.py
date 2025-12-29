"""Marathon generation algorithms."""

from __future__ import annotations

import hashlib
import random
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MarathonItem:
    video_id: str
    title: str

    def to_dict(self) -> dict[str, Any]:
        return {"video_id": self.video_id, "title": self.title}


@dataclass
class MarathonSource:
    label: str
    items: list[MarathonItem] = field(default_factory=list)


@dataclass
class MarathonResult:
    items: list[MarathonItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": [it.to_dict() for it in self.items],
            "warnings": list(self.warnings),
        }


# --------------------------------------------------------------------------- #
# Episode parsing (best-effort)
# --------------------------------------------------------------------------- #

_EP_PATTERNS = [
    re.compile(r"[Ss](\d{1,3})\s*[Ee](\d{1,4})"),      # S01E04, S01 E04
    re.compile(r"[Ss](\d{1,3})\.?[Ee](\d{1,4})"),      # s01.e04
    re.compile(r"(\d{1,2})x(\d{1,4})"),                # 1x04
]


def parse_episode(title: str) -> tuple[int, int] | None:
    """Extract (season, episode) from title if possible.

    Returns None when no pattern matches.
    """
    for pat in _EP_PATTERNS:
        m = pat.search(title)
        if m:
            try:
                s = int(m.group(1))
                e = int(m.group(2))
                return (s, e)
            except ValueError:
                continue
    return None


def sort_items_by_episode(items: list[MarathonItem]) -> list[MarathonItem]:
    """Sort items by (season, episode) when parseable, otherwise retain order."""
    keyed: list[tuple[tuple[int, int] | None, int, MarathonItem]] = []
    for idx, it in enumerate(items):
        ep = parse_episode(it.title)
        keyed.append((ep, idx, it))

    # Sort: parseable first (by season then episode), then unparsed in original order
    def sort_key(t: tuple[tuple[int, int] | None, int, MarathonItem]) -> tuple[int, int, int, int]:
        ep, orig, _ = t
        if ep is None:
            return (1, 0, 0, orig)  # unparsed keep relative order after parsed
        return (0, ep[0], ep[1], orig)

    keyed.sort(key=sort_key)
    return [it for (_, _, it) in keyed]


# --------------------------------------------------------------------------- #
# Pattern parsing
# --------------------------------------------------------------------------- #

_TOKEN_RE = re.compile(r"([A-Z])(\d*)")


@dataclass
class PatternToken:
    label: str
    count: int = 1


def parse_pattern(pattern: str, valid_labels: set[str]) -> list[PatternToken]:
    """Parse interleave pattern string into tokens.

    Raises ValueError on invalid syntax or unknown labels.
    """
    pattern = pattern.upper().strip()
    if not pattern:
        raise ValueError("pattern_empty")

    tokens: list[PatternToken] = []
    for m in _TOKEN_RE.finditer(pattern):
        label = m.group(1)
        count_str = m.group(2)
        count = int(count_str) if count_str else 1
        if count < 1:
            raise ValueError(f"invalid_count:{label}{count_str}")
        if label not in valid_labels:
            raise ValueError(f"unknown_label:{label}")
        tokens.append(PatternToken(label=label, count=count))

    if not tokens:
        raise ValueError("no_tokens_parsed")

    return tokens


# --------------------------------------------------------------------------- #
# Marathon generators
# --------------------------------------------------------------------------- #


def _seeded_rng(seed: str | None) -> random.Random:
    if seed is None:
        return random.Random()
    h = hashlib.sha256(seed.encode()).digest()
    return random.Random(int.from_bytes(h[:8], "big"))


def concatenate(
    sources: list[MarathonSource],
    *,
    preserve_episode_order: bool = False,
) -> MarathonResult:
    """Concatenate sources in label order."""
    items: list[MarathonItem] = []
    for src in sorted(sources, key=lambda s: s.label):
        src_items = src.items
        if preserve_episode_order:
            src_items = sort_items_by_episode(src_items)
        items.extend(src_items)
    return MarathonResult(items=items)


def shuffle(
    sources: list[MarathonSource],
    *,
    seed: str | None = None,
    preserve_episode_order: bool = False,
) -> MarathonResult:
    """Shuffle combined items, optionally deterministically."""
    all_items: list[MarathonItem] = []
    for src in sources:
        src_items = src.items
        if preserve_episode_order:
            src_items = sort_items_by_episode(src_items)
        all_items.extend(src_items)

    rng = _seeded_rng(seed)
    rng.shuffle(all_items)
    return MarathonResult(items=all_items)


def interleave(
    sources: list[MarathonSource],
    pattern: str,
    *,
    preserve_episode_order: bool = False,
) -> MarathonResult:
    """Interleave sources according to pattern until all exhausted."""
    by_label = {src.label: list(src.items) for src in sources}
    if preserve_episode_order:
        by_label = {
            label: sort_items_by_episode(items) for label, items in by_label.items()
        }

    tokens = parse_pattern(pattern, set(by_label.keys()))

    result_items: list[MarathonItem] = []
    warnings: list[str] = []

    exhausted: set[str] = set()
    while len(exhausted) < len(by_label):
        for tok in tokens:
            if tok.label in exhausted:
                continue
            bucket = by_label[tok.label]
            for _ in range(tok.count):
                if not bucket:
                    exhausted.add(tok.label)
                    break
                result_items.append(bucket.pop(0))

    return MarathonResult(items=result_items, warnings=warnings)


def generate_marathon(
    sources: list[MarathonSource],
    *,
    method: str = "concatenate",
    shuffle_seed: str | None = None,
    interleave_pattern: str | None = None,
    preserve_episode_order: bool = False,
) -> MarathonResult:
    """High-level dispatcher for marathon generation."""
    method = (method or "concatenate").lower().strip()

    if method == "concatenate":
        return concatenate(sources, preserve_episode_order=preserve_episode_order)

    if method == "shuffle":
        return shuffle(sources, seed=shuffle_seed, preserve_episode_order=preserve_episode_order)

    if method == "interleave":
        if not interleave_pattern:
            # Default round-robin: A B C ...
            labels = " ".join(src.label for src in sorted(sources, key=lambda s: s.label))
            interleave_pattern = labels
        return interleave(sources, interleave_pattern, preserve_episode_order=preserve_episode_order)

    return MarathonResult(items=[], warnings=[f"unknown_method:{method}"])
