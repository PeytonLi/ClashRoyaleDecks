import pytest

from app.data.scraper import deck_hash
from app.ml.model import DeckRecommender
from app.services.deck_forms import (
    FORM_CHAMPION,
    FORM_EVOLUTION,
    FORM_HERO,
    SLOT_EVOLUTION,
    SLOT_HERO,
    SLOT_WILD,
    normalize_deck_slots,
    parse_card_input,
)


DECK = [
    "firecracker",
    "bowler",
    "archer-queen",
    "hog-rider",
    "knight",
    "cannon",
    "ice-spirit",
    "the-log",
]


def test_parse_card_input_strips_special_form_prefixes():
    assert parse_card_input("Evo Firecracker") == {
        "query": "firecracker",
        "form": FORM_EVOLUTION,
    }
    assert parse_card_input("Hero Bowler") == {
        "query": "bowler",
        "form": FORM_HERO,
    }
    assert parse_card_input("Champion Archer Queen") == {
        "query": "archer queen",
        "form": FORM_CHAMPION,
    }


def test_normalize_deck_slots_assigns_current_special_slots():
    slots = normalize_deck_slots(DECK, [
        {"card_key": "firecracker", "form": "evolution"},
        {"card_key": "bowler", "form": "hero"},
        {"card_key": "archer-queen", "form": "champion"},
        {"card_key": "hog-rider", "form": "base"},
        {"card_key": "knight", "form": "base"},
        {"card_key": "cannon", "form": "base"},
        {"card_key": "ice-spirit", "form": "base"},
        {"card_key": "the-log", "form": "base"},
    ])

    assert slots[0]["slot_type"] == SLOT_EVOLUTION
    assert slots[1]["slot_type"] == SLOT_HERO
    assert slots[2]["slot_type"] == SLOT_WILD


def test_normalize_deck_slots_rejects_more_special_forms_than_slots():
    with pytest.raises(ValueError):
        normalize_deck_slots(DECK, [
            {"card_key": "firecracker", "form": "evolution"},
            {"card_key": "knight", "form": "evolution"},
            {"card_key": "bowler", "form": "hero"},
            {"card_key": "archer-queen", "form": "champion"},
            {"card_key": "hog-rider", "form": "base"},
            {"card_key": "cannon", "form": "base"},
            {"card_key": "ice-spirit", "form": "base"},
            {"card_key": "the-log", "form": "base"},
        ])


def test_deck_hash_preserves_base_hash_and_distinguishes_special_variants():
    base_slots = normalize_deck_slots(DECK)
    evo_firecracker = normalize_deck_slots(DECK, [
        {"card_key": "firecracker", "form": "evolution"},
        *[{"card_key": key, "form": "base"} for key in DECK[1:]],
    ])
    evo_knight = normalize_deck_slots(DECK, [
        {"card_key": "firecracker", "form": "base"},
        {"card_key": "bowler", "form": "base"},
        {"card_key": "archer-queen", "form": "base"},
        {"card_key": "hog-rider", "form": "base"},
        {"card_key": "knight", "form": "evolution"},
        {"card_key": "cannon", "form": "base"},
        {"card_key": "ice-spirit", "form": "base"},
        {"card_key": "the-log", "form": "base"},
    ])

    assert deck_hash(DECK) == deck_hash(DECK, base_slots)
    assert deck_hash(DECK, evo_firecracker) != deck_hash(DECK)
    assert deck_hash(DECK, evo_firecracker) != deck_hash(DECK, evo_knight)


def test_recommender_filters_special_forms_without_unlocks():
    model = DeckRecommender()
    model.meta_decks = [
        {"card_keys": DECK, "deck_slots": normalize_deck_slots(DECK), "win_rate": 0.5},
        {
            "card_keys": DECK,
            "deck_slots": normalize_deck_slots(DECK, [
                {"card_key": "firecracker", "form": "evolution"},
                *[{"card_key": key, "form": "base"} for key in DECK[1:]],
            ]),
            "win_rate": 0.99,
        },
    ]
    model.all_card_keys = DECK
    model.card_to_idx = {key: idx for idx, key in enumerate(DECK)}
    model.card_max_levels = {key: 14 for key in DECK}

    results = model.recommend(
        player_card_levels={key: 14 for key in DECK},
        player_special_unlocks={"evolutions": [], "heroes": [], "champions": []},
        player_trophies=5000,
        top_k=5,
    )

    assert len(results) == 1
    assert all(slot["form"] == "base" for slot in results[0]["deck"]["deck_slots"])


def test_recommender_allows_unlocked_required_evolution():
    model = DeckRecommender()
    model.meta_decks = [
        {
            "card_keys": DECK,
            "deck_slots": normalize_deck_slots(DECK, [
                {"card_key": "firecracker", "form": "evolution"},
                *[{"card_key": key, "form": "base"} for key in DECK[1:]],
            ]),
            "win_rate": 0.99,
        },
    ]
    model.all_card_keys = DECK
    model.card_to_idx = {key: idx for idx, key in enumerate(DECK)}
    model.card_max_levels = {key: 14 for key in DECK}

    results = model.recommend(
        player_card_levels={key: 14 for key in DECK},
        required_cards=[{"card_key": "firecracker", "form": "evolution"}],
        player_special_unlocks={"evolutions": ["firecracker"], "heroes": [], "champions": []},
        player_trophies=5000,
        top_k=1,
    )

    assert len(results) == 1
    assert results[0]["deck"]["deck_slots"][0]["form"] == "evolution"

