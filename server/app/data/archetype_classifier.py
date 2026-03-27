"""
Archetype classifier for Clash Royale decks.

Rules-based classifier that tags decks as: cycle, beatdown, bridge_spam, control, bait.
"""
from typing import Optional

# Cards strongly associated with each archetype
BEATDOWN_TANKS = {
    "golem", "giant", "lava-hound", "elixir-golem", "royal-giant",
    "giant-skeleton",
}

BRIDGE_SPAM_CARDS = {
    "ram-rider", "battle-ram", "bandit", "royal-ghost", "dark-prince",
    "inferno-dragon", "electro-wizard", "magic-archer", "pekka",
}

BAIT_CARDS = {
    "goblin-barrel", "princess", "goblin-gang", "skeleton-army",
    "dart-goblin", "rascals", "minion-horde", "inferno-tower",
}

CONTROL_ANCHORS = {
    "pekka", "mega-knight", "bowler", "cannon-cart", "sparky",
    "inferno-tower", "bomb-tower",
}

CYCLE_CHEAP_CARDS = {
    "ice-spirit", "fire-spirit", "electro-spirit", "skeletons",
    "ice-golem", "bats", "goblins", "spear-goblins",
}

WIN_CONDITIONS = {
    "hog-rider", "ram-rider", "battle-ram", "goblin-barrel",
    "golem", "giant", "lava-hound", "royal-giant", "elixir-golem",
    "graveyard", "miner", "balloon", "x-bow", "mortar",
    "three-musketeers", "wall-breakers", "skeleton-barrel",
}

# Card elixir costs (subset, will be enriched from DB)
DEFAULT_ELIXIR: dict[str, int] = {
    "skeletons": 1, "ice-spirit": 1, "fire-spirit": 1, "electro-spirit": 1,
    "bats": 2, "goblins": 2, "ice-golem": 2, "the-log": 2, "zap": 2,
    "spear-goblins": 2, "wall-breakers": 2, "snowball": 2,
    "knight": 3, "archers": 3, "minions": 3, "cannon": 3, "goblin-barrel": 3,
    "skeleton-army": 3, "goblin-gang": 3, "princess": 3, "miner": 3,
    "dart-goblin": 3, "guards": 3, "mega-minion": 3, "bandit": 3,
    "hog-rider": 4, "musketeer": 4, "fireball": 4, "tesla": 4,
    "valkyrie": 4, "dark-prince": 4, "battle-ram": 4, "poison": 4,
    "inferno-dragon": 4, "electro-wizard": 4, "magic-archer": 4,
    "barbarians": 5, "giant": 5, "balloon": 5, "wizard": 5,
    "bowler": 5, "ram-rider": 5, "royal-ghost": 4,
    "royal-giant": 6, "pekka": 7, "mega-knight": 7,
    "golem": 8, "lava-hound": 7, "three-musketeers": 9,
    "x-bow": 6, "mortar": 4, "graveyard": 5, "elixir-golem": 3,
}


def compute_avg_elixir(card_keys: list[str], elixir_lookup: Optional[dict[str, int]] = None) -> float:
    """Compute average elixir cost of a deck."""
    lookup = elixir_lookup or DEFAULT_ELIXIR
    costs = [lookup.get(key, 4) for key in card_keys]  # default 4 if unknown
    return sum(costs) / len(costs) if costs else 4.0


def classify_archetype(
    card_keys: list[str],
    elixir_lookup: Optional[dict[str, int]] = None,
) -> str:
    """
    Classify a deck's archetype based on its card composition.

    Priority order (first match wins):
    1. Beatdown — contains a heavy tank
    2. Bait — contains ≥3 bait-able cards
    3. Bridge Spam — contains ≥3 bridge spam cards
    4. Cycle — avg elixir ≤ 3.1 and has cheap cycle cards
    5. Control — contains a control anchor card
    6. Default to "control" as catch-all

    Args:
        card_keys: List of 8 card sc_keys (lowercase, hyphenated)
        elixir_lookup: Optional dict mapping card key → elixir cost

    Returns:
        One of: "beatdown", "bait", "bridge_spam", "cycle", "control"
    """
    card_set = set(card_keys)
    avg_elixir = compute_avg_elixir(card_keys, elixir_lookup)

    # 1. Beatdown: has a heavy tank
    beatdown_count = len(card_set & BEATDOWN_TANKS)
    if beatdown_count >= 1:
        return "beatdown"

    # 2. Bait: ≥3 bait-able cards
    bait_count = len(card_set & BAIT_CARDS)
    if bait_count >= 3:
        return "bait"

    # 3. Bridge Spam: ≥3 bridge spam cards
    bridge_spam_count = len(card_set & BRIDGE_SPAM_CARDS)
    if bridge_spam_count >= 3:
        return "bridge_spam"

    # 4. Cycle: low avg elixir + cheap cycle cards + a win condition
    cycle_count = len(card_set & CYCLE_CHEAP_CARDS)
    has_win_con = len(card_set & WIN_CONDITIONS) >= 1
    if avg_elixir <= 3.1 and cycle_count >= 2 and has_win_con:
        return "cycle"

    # 5. Control: has a control anchor
    control_count = len(card_set & CONTROL_ANCHORS)
    if control_count >= 1:
        return "control"

    # 6. Default — classify based on elixir cost
    if avg_elixir <= 3.3:
        return "cycle"
    return "control"
