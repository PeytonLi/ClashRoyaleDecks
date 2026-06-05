"""
Utilities for Clash Royale deck special forms.

The ML model still treats a deck as 8 base cards, while this module carries
the active Evolution, Hero, and Champion metadata needed to validate and
display current deck-slot rules.
"""

from __future__ import annotations

import re
from typing import Any, Optional, TypedDict

FORM_BASE = "base"
FORM_EVOLUTION = "evolution"
FORM_HERO = "hero"
FORM_CHAMPION = "champion"

SLOT_NORMAL = "normal"
SLOT_EVOLUTION = "evolution"
SLOT_HERO = "hero"
SLOT_WILD = "wild"

FORM_VALUES = {FORM_BASE, FORM_EVOLUTION, FORM_HERO, FORM_CHAMPION}
SPECIAL_FORMS = {FORM_EVOLUTION, FORM_HERO, FORM_CHAMPION}

EVOLUTION_SLOT_TROPHIES = 600
HERO_SLOT_TROPHIES = 1300
WILD_SLOT_TROPHIES = 3000


class DeckSlot(TypedDict):
    card_key: str
    form: str
    slot_type: str


class RequiredCardSpec(TypedDict):
    card_key: str
    form: Optional[str]


class ParsedCardInput(TypedDict):
    query: str
    form: Optional[str]


def card_key_from_name(value: str) -> str:
    """Convert a display/card name into the repo's canonical card key format."""
    return re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")


def card_search_aliases(sc_key: str, name: Optional[str] = None) -> set[str]:
    """Generate all searchable aliases for fuzzy card-name matching.

    Produces variants: lowercase, slug, slug-with-spaces, compact.
    Callers can use these to build lookup tables for user-entered card names.
    """
    values = {sc_key}
    if name:
        values.add(name)

    aliases: set[str] = set()
    for value in values:
        clean = value.strip().lower()
        if not clean:
            continue
        slug = card_key_from_name(clean)
        compact = re.sub(r"[^a-z0-9]", "", clean)
        aliases.update({clean, slug, slug.replace("-", " "), compact})
    return aliases


def display_card_name(card_key: str) -> str:
    """Convert a canonical card key into a human-readable display name."""
    return card_key.replace("-", " ").title()


def parse_card_input(value: str) -> ParsedCardInput:
    """Parse optional special prefixes from user/API card labels."""
    raw = value.strip()
    lowered = raw.lower()

    prefix_match = re.match(
        r"^(evolution|evo|evolved|hero|champion|champ)[\s:_-]+(.+)$",
        lowered,
    )
    if prefix_match:
        prefix, rest = prefix_match.groups()
        form = {
            "evolution": FORM_EVOLUTION,
            "evo": FORM_EVOLUTION,
            "evolved": FORM_EVOLUTION,
            "hero": FORM_HERO,
            "champion": FORM_CHAMPION,
            "champ": FORM_CHAMPION,
        }[prefix]
        return {"query": rest.strip(), "form": form}

    suffix_match = re.match(
        r"^(.+?)[\s:_-]+(evolution|evo|evolved|hero)$",
        lowered,
    )
    if suffix_match:
        rest, suffix = suffix_match.groups()
        form = (
            FORM_EVOLUTION if suffix in {"evolution", "evo", "evolved"} else FORM_HERO
        )
        return {"query": rest.strip(), "form": form}

    return {"query": raw, "form": None}


def make_base_slots(card_keys: list[str]) -> list[DeckSlot]:
    """Build normal slots for an old-style 8-card deck."""
    return [
        {
            "card_key": card_key_from_name(card_key),
            "form": FORM_BASE,
            "slot_type": SLOT_NORMAL,
        }
        for card_key in card_keys
    ]


def _normalize_form(value: Any) -> str:
    form = str(value or FORM_BASE).lower()
    if form not in FORM_VALUES:
        raise ValueError(f"Unsupported deck slot form: {value}")
    return form


def _normalize_slot(slot: dict[str, Any]) -> DeckSlot:
    raw_card = slot.get("card_key") or slot.get("card") or slot.get("name")
    card_key = card_key_from_name(str(raw_card or ""))
    if not card_key:
        raise ValueError("Deck slot is missing card_key")
    return {
        "card_key": card_key,
        "form": _normalize_form(slot.get("form")),
        "slot_type": SLOT_NORMAL,
    }


def assign_slot_types(slots: list[DeckSlot]) -> list[DeckSlot]:
    """
    Assign current special slot types.

    Legal special layouts are:
    - 1 Evolution
    - 1 Hero/Champion
    - plus 1 Wild holding one additional Evolution, Hero, or Champion
    """
    normalized = [{**slot, "slot_type": SLOT_NORMAL} for slot in slots]
    evolution_indices = [
        idx for idx, slot in enumerate(normalized) if slot["form"] == FORM_EVOLUTION
    ]
    hero_like_indices = [
        idx
        for idx, slot in enumerate(normalized)
        if slot["form"] in {FORM_HERO, FORM_CHAMPION}
    ]

    if len(evolution_indices) > 2:
        raise ValueError("A deck can use at most two active Evolutions")
    if len(hero_like_indices) > 2:
        raise ValueError("A deck can use at most two active Heroes/Champions")
    if len(evolution_indices) + len(hero_like_indices) > 3:
        raise ValueError("A deck can use at most three active special forms")

    if evolution_indices:
        normalized[evolution_indices[0]]["slot_type"] = SLOT_EVOLUTION
    if hero_like_indices:
        normalized[hero_like_indices[0]]["slot_type"] = SLOT_HERO

    wild_candidates = evolution_indices[1:] + hero_like_indices[1:]
    if len(wild_candidates) > 1:
        raise ValueError("Only one active special form can use the Wild slot")
    if wild_candidates:
        normalized[wild_candidates[0]]["slot_type"] = SLOT_WILD

    return normalized


def normalize_deck_slots(
    card_keys: Optional[list[str]] = None,
    deck_slots: Optional[list[dict[str, Any]]] = None,
) -> list[DeckSlot]:
    """Return 8 legal, normalized deck slots."""
    slots: list[DeckSlot]
    if deck_slots:
        slots = [_normalize_slot(slot) for slot in deck_slots]
    else:
        slots = make_base_slots(card_keys or [])

    if len(slots) != 8:
        raise ValueError("A Clash Royale deck must contain exactly 8 cards")

    return assign_slot_types(slots)


def base_card_keys_from_slots(deck_slots: list[DeckSlot]) -> list[str]:
    return [slot["card_key"] for slot in deck_slots]


def deck_has_special_forms(deck_slots: list[DeckSlot]) -> bool:
    return any(slot["form"] in SPECIAL_FORMS for slot in deck_slots)


def int_from_api(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def base_card_key_from_api_card(card: dict[str, Any]) -> str:
    parsed = parse_card_input(str(card.get("name", "")))
    return card_key_from_name(parsed["query"])


def infer_active_form_from_api_card(card: dict[str, Any]) -> str:
    """Infer the active form used in a battle-log deck card object."""
    parsed = parse_card_input(str(card.get("name", "")))
    if parsed["form"]:
        return parsed["form"]

    rarity = str(card.get("rarity", "")).lower()
    if rarity == FORM_CHAMPION:
        return FORM_CHAMPION
    if rarity == FORM_HERO:
        return FORM_HERO

    if int_from_api(card.get("evolutionLevel")) > 0:
        return FORM_EVOLUTION
    if card.get("evolved") is True or card.get("isEvolution") is True:
        return FORM_EVOLUTION

    return FORM_BASE


def slots_from_api_cards(cards: list[dict[str, Any]]) -> list[DeckSlot]:
    slots = [
        {
            "card_key": base_card_key_from_api_card(card),
            "form": infer_active_form_from_api_card(card),
            "slot_type": SLOT_NORMAL,
        }
        for card in cards
    ]
    return normalize_deck_slots(deck_slots=slots)


def supports_evolution_from_api_card(card: dict[str, Any]) -> bool:
    return (
        int_from_api(card.get("maxEvolutionLevel")) > 0
        or int_from_api(card.get("evolutionLevel")) > 0
        or parse_card_input(str(card.get("name", "")))["form"] == FORM_EVOLUTION
    )


def supports_hero_from_api_card(card: dict[str, Any]) -> bool:
    parsed = parse_card_input(str(card.get("name", "")))
    return (
        parsed["form"] == FORM_HERO
        or str(card.get("rarity", "")).lower() == FORM_HERO
        or int_from_api(card.get("heroLevel")) > 0
        or int_from_api(card.get("maxHeroLevel")) > 0
    )


def extract_special_unlocks(cards: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Extract special-form unlocks from a player profile card list."""
    unlocks = {"evolutions": [], "heroes": [], "champions": []}

    for card in cards:
        card_key = base_card_key_from_api_card(card)
        if not card_key:
            continue

        rarity = str(card.get("rarity", "")).lower()
        parsed_form = parse_card_input(str(card.get("name", "")))["form"]

        if int_from_api(card.get("evolutionLevel")) > 0:
            unlocks["evolutions"].append(card_key)
        if (
            parsed_form == FORM_HERO
            or rarity == FORM_HERO
            or int_from_api(card.get("heroLevel")) > 0
        ):
            unlocks["heroes"].append(card_key)
        if parsed_form == FORM_CHAMPION or rarity == FORM_CHAMPION:
            unlocks["champions"].append(card_key)

    return normalize_special_unlocks(unlocks)


def normalize_special_unlocks(
    unlocks: Optional[dict[str, Any]],
) -> dict[str, list[str]]:
    normalized = {"evolutions": [], "heroes": [], "champions": []}
    if not unlocks:
        return normalized

    for key in normalized:
        seen: set[str] = set()
        for value in unlocks.get(key, []) or []:
            card_key = card_key_from_name(str(value))
            if card_key and card_key not in seen:
                normalized[key].append(card_key)
                seen.add(card_key)

    return normalized


def slot_is_unlocked(
    slot: DeckSlot,
    special_unlocks: dict[str, list[str]],
    player_trophies: int,
) -> bool:
    form = slot["form"]
    if form == FORM_BASE:
        return True

    if (
        slot["slot_type"] == SLOT_EVOLUTION
        and player_trophies < EVOLUTION_SLOT_TROPHIES
    ):
        return False
    if slot["slot_type"] == SLOT_HERO and player_trophies < HERO_SLOT_TROPHIES:
        return False
    if slot["slot_type"] == SLOT_WILD and player_trophies < WILD_SLOT_TROPHIES:
        return False

    unlock_key = {
        FORM_EVOLUTION: "evolutions",
        FORM_HERO: "heroes",
        FORM_CHAMPION: "champions",
    }.get(form)
    return bool(unlock_key and slot["card_key"] in special_unlocks.get(unlock_key, []))


def deck_is_playable(
    card_keys: list[str],
    deck_slots: Optional[list[dict[str, Any]]],
    special_unlocks: Optional[dict[str, Any]],
    player_trophies: int,
) -> bool:
    try:
        slots = normalize_deck_slots(card_keys, deck_slots)
    except ValueError:
        return False

    unlocks = normalize_special_unlocks(special_unlocks)
    return all(slot_is_unlocked(slot, unlocks, player_trophies) for slot in slots)


def normalize_required_card_specs(
    required_cards: Optional[list[Any]],
) -> list[RequiredCardSpec]:
    specs: list[RequiredCardSpec] = []
    seen: set[tuple[str, Optional[str]]] = set()

    for item in required_cards or []:
        if isinstance(item, dict):
            card_key = card_key_from_name(
                str(item.get("card_key") or item.get("key") or "")
            )
            form = item.get("form")
            form = _normalize_form(form) if form else None
        else:
            parsed = parse_card_input(str(item))
            card_key = card_key_from_name(parsed["query"])
            form = parsed["form"]

        if not card_key:
            continue

        key = (card_key, form)
        if key not in seen:
            specs.append({"card_key": card_key, "form": form})
            seen.add(key)

    return specs


def required_spec_matches_deck(
    spec: RequiredCardSpec,
    card_keys: list[str],
    deck_slots: Optional[list[dict[str, Any]]],
) -> bool:
    if spec["form"] is None:
        return spec["card_key"] in set(card_keys)

    try:
        slots = normalize_deck_slots(card_keys, deck_slots)
    except ValueError:
        return False

    return any(
        slot["card_key"] == spec["card_key"] and slot["form"] == spec["form"]
        for slot in slots
    )


def display_required_card(spec: RequiredCardSpec | str) -> str:
    if isinstance(spec, str):
        return display_card_name(spec)

    base_name = display_card_name(spec["card_key"])
    if spec.get("form") == FORM_EVOLUTION:
        return f"Evolution {base_name}"
    if spec.get("form") == FORM_HERO:
        return f"Hero {base_name}"
    if spec.get("form") == FORM_CHAMPION:
        return f"Champion {base_name}"
    return base_name


def display_slot_label(slot: DeckSlot) -> str:
    base_name = display_card_name(slot["card_key"])
    prefix = {
        FORM_EVOLUTION: "Evolution",
        FORM_HERO: "Hero",
        FORM_CHAMPION: "Champion",
    }.get(slot["form"])
    if not prefix:
        return base_name
    if slot["slot_type"] == SLOT_WILD:
        return f"{prefix} {base_name} in the Wild slot"
    return f"{prefix} {base_name}"
