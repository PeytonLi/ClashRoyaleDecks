"""Utilities for normalizing and resolving Clash Royale player tags."""

from __future__ import annotations

VALID_TAG_CHARS = set("0289PYLQGRJCUV")
AMBIGUOUS_INPUT_CHARS = {"O"}
MIN_TAG_LEN = 3
MAX_TAG_LEN = 15


def normalize_tag_input(tag: str) -> str:
    """Normalize user input while allowing ambiguous characters that can be resolved."""
    clean = tag.strip().upper()
    if clean.startswith("#"):
        clean = clean[1:]

    if not clean:
        raise ValueError("Please enter a player tag.")

    if len(clean) < MIN_TAG_LEN or len(clean) > MAX_TAG_LEN:
        raise ValueError(
            f"Invalid player tag format. Tag length must be between {MIN_TAG_LEN} and {MAX_TAG_LEN} characters."
        )

    allowed_input_chars = VALID_TAG_CHARS | AMBIGUOUS_INPUT_CHARS
    invalid_chars = sorted({ch for ch in clean if ch not in allowed_input_chars})
    if invalid_chars:
        raise ValueError(
            "Invalid player tag format. Use only Clash tag characters "
            "(0289PYLQGRJCUV). Tip: use 0 not O."
        )

    return clean


def build_tag_candidates(normalized_tag: str) -> list[str]:
    """Build canonical candidate tags in priority order for ambiguous input."""
    candidates: list[str] = [normalized_tag]

    if "O" in normalized_tag:
        candidates.append(normalized_tag.replace("O", "0"))

    deduped: list[str] = []
    seen: set[str] = set()
    allowed_candidate_chars = VALID_TAG_CHARS | AMBIGUOUS_INPUT_CHARS

    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)

        if any(ch not in allowed_candidate_chars for ch in candidate):
            continue

        deduped.append(candidate)

    if not deduped:
        raise ValueError(
            "Invalid player tag format. Use only Clash tag characters "
            "(0289PYLQGRJCUV). Tip: use 0 not O."
        )

    return deduped


def to_hash_tag(candidate: str) -> str:
    """Convert a normalized candidate tag to canonical '#TAG' format."""
    return f"#{candidate}"
