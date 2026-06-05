"""
Prediction router — deck recommendations and meta trends.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_existing_user_id, verify_bff_origin
from app.ml.explainer import generate_explanation, generate_short_summary
from app.ml.model import recommender
from app.models import Card, Player, UserPlayer
from app.services.deck_forms import (
    card_search_aliases,
    display_card_name,
    display_required_card,
    normalize_deck_slots,
    parse_card_input,
)
from app.services.tag_utils import (
    build_tag_candidates,
    normalize_tag_input,
    to_hash_tag,
)

router = APIRouter()


# --- Request / Response schemas ---


class RecommendRequest(BaseModel):
    player_tag: str
    archetype_preference: Optional[str] = (
        None  # cycle, beatdown, bridge_spam, control, bait
    )
    required_cards: list[str] = Field(default_factory=list, max_length=8)


class DeckSlotResponse(BaseModel):
    card: str
    card_key: str
    form: str
    slot_type: str


class DeckRecommendation(BaseModel):
    cards: list[str]
    slots: list[DeckSlotResponse] = Field(default_factory=list)
    archetype: str
    win_rate: float
    level_fit_score: float
    overall_score: float
    explanation: str
    short_summary: str


class PlayerSummary(BaseModel):
    name: str
    trophies: int
    arena_name: str
    max_card_level: int
    avg_card_level: float


class RecommendResponse(BaseModel):
    recommendations: list[DeckRecommendation]
    player_summary: PlayerSummary
    required_cards: list[str] = Field(default_factory=list)


def _format_deck_slots(deck: dict) -> list[DeckSlotResponse]:
    slots = normalize_deck_slots(deck.get("card_keys", []), deck.get("deck_slots"))
    return [
        DeckSlotResponse(
            card=display_card_name(slot["card_key"]),
            card_key=slot["card_key"],
            form=slot["form"],
            slot_type=slot["slot_type"],
        )
        for slot in slots
    ]


async def resolve_required_cards(
    db: AsyncSession,
    requested_cards: list[str],
) -> list[dict[str, Optional[str]]]:
    """Resolve user-entered card names into canonical card keys."""
    alias_to_key: dict[str, str] = {}

    for key in recommender.all_card_keys:
        for alias in card_search_aliases(key):
            alias_to_key[alias] = key

    result = await db.execute(select(Card.sc_key, Card.name))
    for sc_key, name in result.all():
        for alias in card_search_aliases(sc_key, name):
            alias_to_key[alias] = sc_key

    resolved: list[dict[str, Optional[str]]] = []
    seen: set[tuple[str, Optional[str]]] = set()
    unknown: list[str] = []

    for raw_card in requested_cards:
        raw_card = raw_card.strip()
        if not raw_card:
            continue

        parsed = parse_card_input(raw_card)
        key = None
        for alias in card_search_aliases(parsed["query"]):
            if alias in alias_to_key:
                key = alias_to_key[alias]
                break

        if key is None:
            unknown.append(raw_card)
        else:
            resolved_key = (key, parsed["form"])
            if resolved_key not in seen:
                resolved.append({"card_key": key, "form": parsed["form"]})
                seen.add(resolved_key)

    if unknown:
        card_list = ", ".join(unknown)
        raise HTTPException(
            status_code=400,
            detail=f"Unknown required card: {card_list}. Use a Clash Royale card name, such as Hog Rider.",
        )

    return resolved


# --- Endpoints ---


async def _lookup_cached_player(db: AsyncSession, raw_tag: str) -> Player:
    """Resolve a player tag to a cached Player row, raising on failure."""
    try:
        normalized = normalize_tag_input(raw_tag)
        candidates = [
            to_hash_tag(candidate) for candidate in build_tag_candidates(normalized)
        ]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    for candidate in candidates:
        result = await db.execute(select(Player).where(Player.tag == candidate))
        player = result.scalar_one_or_none()
        if player is not None:
            return player

    raise HTTPException(
        status_code=404,
        detail="Player not found in cache. Call GET /api/players/{tag} first to fetch their data. Use 0, not O.",
    )


async def _require_player_linked(
    db: AsyncSession, user_id: int, player_tag: str
) -> None:
    """Raise 403 if the authenticated user hasn't linked this player tag."""
    result = await db.execute(
        select(UserPlayer).where(
            UserPlayer.user_id == user_id,
            UserPlayer.player_tag == player_tag,
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=403,
            detail="This player profile is not linked to your account. Fetch the player profile first.",
        )


def _ensure_model_ready() -> None:
    """Raise 503 if the ML model isn't trained and can't be loaded from disk."""
    if recommender.is_trained:
        return
    if recommender.load():
        return
    raise HTTPException(
        status_code=503,
        detail="ML model is not trained yet. Run the training pipeline first.",
    )


def _build_player_summary(player: Player) -> PlayerSummary:
    all_levels = list(player.card_levels.values()) if player.card_levels else [0]
    return PlayerSummary(
        name=player.name,
        trophies=player.trophies,
        arena_name=player.arena_name,
        max_card_level=max(all_levels) if all_levels else 0,
        avg_card_level=round(sum(all_levels) / len(all_levels), 1)
        if all_levels
        else 0.0,
    )


def _build_recommendation(
    result: dict,
    player: Player,
    archetype_pref: Optional[str],
    required_cards: list[dict],
) -> DeckRecommendation:
    deck = result["deck"]
    scores = result["scores"]
    card_levels = player.card_levels or {}

    explanation = generate_explanation(
        deck=deck,
        scores=scores,
        player_card_levels=card_levels,
        player_trophies=player.trophies,
        archetype_pref=archetype_pref,
        required_cards=required_cards,
        synergy_map=recommender.synergy_map,
    )

    return DeckRecommendation(
        cards=[display_card_name(k) for k in deck.get("card_keys", [])],
        slots=_format_deck_slots(deck),
        archetype=deck.get("archetype", "unknown"),
        win_rate=round(deck.get("win_rate", 0.0), 4),
        level_fit_score=round(scores.get("level_fit", 0.0), 4),
        overall_score=round(scores.get("overall", 0.0), 4),
        explanation=explanation,
        short_summary=generate_short_summary(deck, scores),
    )


@router.post("/recommend", dependencies=[Depends(verify_bff_origin)])
async def recommend_deck(
    request: RecommendRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(require_existing_user_id),
) -> RecommendResponse:
    """Generate 3 deck recommendations for a player.

    Fetches player data from cache (must call /api/players/{tag} first),
    runs through the hybrid ML model, and returns recommendations
    with detailed explanations.
    """
    player = await _lookup_cached_player(db, request.player_tag)
    await _require_player_linked(db, user_id, player.tag)
    _ensure_model_ready()

    required_cards = await resolve_required_cards(db, request.required_cards)
    results = recommender.recommend(
        player_card_levels=player.card_levels or {},
        archetype_pref=request.archetype_preference,
        required_cards=required_cards,
        player_special_unlocks=player.special_card_unlocks or {},
        player_trophies=player.trophies,
        top_k=3,
    )

    if not results:
        if required_cards:
            required_display = ", ".join(
                display_required_card(card) for card in required_cards
            )
            raise HTTPException(
                status_code=404,
                detail=f"No deck recommendations available with {required_display}. Try another card or remove the optional card filter.",
            )
        raise HTTPException(
            status_code=404,
            detail="No deck recommendations available. The model may need more training data.",
        )

    recommendations = [
        _build_recommendation(r, player, request.archetype_preference, required_cards)
        for r in results
    ]

    return RecommendResponse(
        recommendations=recommendations,
        player_summary=_build_player_summary(player),
        required_cards=[display_required_card(card) for card in required_cards],
    )


class MetaTrendsResponse(BaseModel):
    top_decks: list[dict]
    archetype_distribution: dict[str, int]


@router.get("/meta-trends")
async def get_meta_trends(db: AsyncSession = Depends(get_db)) -> MetaTrendsResponse:
    """Get current meta trends — top decks by win rate and archetype distribution."""
    from app.models import MetaDeck

    result = await db.execute(
        select(MetaDeck).order_by(MetaDeck.win_rate.desc()).limit(10)
    )
    top_decks_rows = result.scalars().all()

    top_decks = []
    archetype_counts: dict[str, int] = {}

    for d in top_decks_rows:
        card_names = [k.replace("-", " ").title() for k in d.card_keys]
        deck_slots = _format_deck_slots(
            {"card_keys": d.card_keys, "deck_slots": d.deck_slots}
        )
        top_decks.append(
            {
                "cards": card_names,
                "slots": [slot.model_dump() for slot in deck_slots],
                "archetype": d.archetype or "unknown",
                "win_rate": round(d.win_rate, 4),
                "usage_rate": round(d.usage_rate, 4),
                "avg_elixir": round(d.avg_elixir, 1),
            }
        )
        arch = d.archetype or "unknown"
        archetype_counts[arch] = archetype_counts.get(arch, 0) + 1

    return MetaTrendsResponse(
        top_decks=top_decks,
        archetype_distribution=archetype_counts,
    )
