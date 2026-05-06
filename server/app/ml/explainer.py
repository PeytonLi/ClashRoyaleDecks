"""
Explanation generator for deck recommendations.

Produces detailed, human-readable explanations covering:
- Win rate context
- Card level advantages/disadvantages
- Archetype match reasoning
- Key card synergies
- Meta stability
"""

from itertools import combinations
from typing import Optional


def generate_explanation(
    deck: dict,
    scores: dict,
    player_card_levels: dict[str, int],
    player_trophies: int,
    archetype_pref: Optional[str],
    required_cards: Optional[list[str]],
    synergy_map: dict[tuple, float],
) -> str:
    """
    Generate a detailed explanation for why a deck was recommended.

    Args:
        deck: Meta deck dict (card_keys, archetype, win_rate, etc.)
        scores: Score breakdown dict (overall, cf, cb, level_fit, win_rate)
        player_card_levels: Player's card levels
        player_trophies: Player's current trophies
        archetype_pref: Player's archetype preference (if any)
        required_cards: Card keys the user asked to include (if any)
        synergy_map: Card pair synergy scores

    Returns:
        Multi-sentence explanation string
    """
    card_keys = deck.get("card_keys", [])
    win_rate = deck.get("win_rate", 0.5)
    archetype = deck.get("archetype", "unknown")
    avg_elixir = deck.get("avg_elixir", 0.0)
    source = deck.get("source", "unknown")
    sample_size = deck.get("sample_size", 0)

    parts = []

    # 1. Archetype + win rate intro
    archetype_display = archetype.replace("_", " ").title()
    win_pct = round(win_rate * 100, 1)

    trophy_low = deck.get("trophy_range_low", 0)
    trophy_high = deck.get("trophy_range_high", 9000)

    if player_trophies > 0:
        parts.append(
            f"This {archetype_display} deck has a {win_pct}% win rate "
            f"in the {trophy_low}-{trophy_high} trophy range"
            f"{f', with an average elixir cost of {avg_elixir:.1f}' if avg_elixir > 0 else ''}."
        )
    else:
        parts.append(
            f"This {archetype_display} deck has a {win_pct}% win rate"
            f"{f', with an average elixir cost of {avg_elixir:.1f}' if avg_elixir > 0 else ''}."
        )

    # 2. Card level assessment
    strong_cards = []
    weak_cards = []
    missing_cards = []

    for card_key in card_keys:
        display_name = card_key.replace("-", " ").title()
        level = player_card_levels.get(card_key, 0)
        if level == 0:
            missing_cards.append(display_name)
        elif level >= 13:
            strong_cards.append(f"{display_name} (Lv{level})")
        elif level <= 10:
            weak_cards.append(f"{display_name} (Lv{level})")

    if strong_cards:
        cards_str = ", ".join(strong_cards[:3])
        parts.append(
            f"Your {cards_str} {'are' if len(strong_cards) > 1 else 'is'} "
            f"well-leveled, giving you a competitive advantage."
        )

    if missing_cards:
        cards_str = ", ".join(missing_cards[:2])
        parts.append(
            f"Note: You don't own {cards_str} yet — "
            f"this deck may not be fully available."
        )
    elif weak_cards:
        cards_str = ", ".join(weak_cards[:2])
        parts.append(
            f"Consider upgrading {cards_str} for better performance on ladder."
        )

    # 3. Archetype preference match
    if archetype_pref:
        if archetype == archetype_pref:
            parts.append(
                f"This deck matches your {archetype_pref.replace('_', ' ')} preference."
            )
        else:
            parts.append(
                f"While you prefer {archetype_pref.replace('_', ' ')}, this {archetype_display} "
                f"deck scored highly due to your card levels and its meta performance."
            )

    if required_cards:
        required_display = ", ".join(card.replace("-", " ").title() for card in required_cards)
        parts.append(
            f"It includes {required_display}, matching your optional card preference."
        )

    # 4. Key synergies (top 2 card pairs)
    pair_synergies = []
    for a, b in combinations(sorted(card_keys), 2):
        pair = (a, b)
        syn_score = synergy_map.get(pair, 0.0)
        if syn_score > 0:
            pair_synergies.append((a, b, syn_score))

    pair_synergies.sort(key=lambda x: x[2], reverse=True)

    if pair_synergies:
        top_pairs = pair_synergies[:2]
        synergy_parts = []
        for a, b, _ in top_pairs:
            a_name = a.replace("-", " ").title()
            b_name = b.replace("-", " ").title()
            synergy_parts.append(f"{a_name} + {b_name}")

        parts.append(
            f"Key synergies: {' and '.join(synergy_parts)} "
            f"frequently appear together in winning decks."
        )

    # 5. Meta stability / data source
    if sample_size > 100:
        parts.append(
            f"Based on {sample_size:,} recorded matches — a statistically reliable sample."
        )
    elif sample_size > 0:
        parts.append(
            f"Based on {sample_size} recorded matches."
        )

    return " ".join(parts)


def generate_short_summary(deck: dict, scores: dict) -> str:
    """Generate a one-line summary for compact display."""
    archetype = deck.get("archetype", "unknown").replace("_", " ").title()
    win_pct = round(deck.get("win_rate", 0.5) * 100, 1)
    overall = round(scores.get("overall", 0) * 100, 1)
    return f"{archetype} deck · {win_pct}% win rate · {overall}% match score"
