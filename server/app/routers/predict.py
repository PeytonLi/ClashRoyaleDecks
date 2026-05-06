"""
Prediction router — deck recommendations and meta trends.
"""

import re
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
from app.services.tag_utils import build_tag_candidates, normalize_tag_input, to_hash_tag

router = APIRouter()


# --- Request / Response schemas ---


class RecommendRequest(BaseModel):
    player_tag: str
    archetype_preference: Optional[str] = None  # cycle, beatdown, bridge_spam, control, bait
    required_cards: list[str] = Field(default_factory=list, max_length=8)


class CardInfo(BaseModel):
    key: str
    name: str


class DeckRecommendation(BaseModel):
    cards: list[str]
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


def _compact_card_alias(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _slug_card_alias(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _card_aliases(sc_key: str, name: Optional[str] = None) -> set[str]:
    values = {sc_key}
    if name:
        values.add(name)

    aliases: set[str] = set()
    for value in values:
        clean = value.strip().lower()
        if not clean:
            continue
        slug = _slug_card_alias(clean)
        compact = _compact_card_alias(clean)
        aliases.update({
            clean,
            slug,
            slug.replace("-", " "),
            compact,
        })
    return aliases


def _display_card_name(card_key: str) -> str:
    return card_key.replace("-", " ").title()


async def resolve_required_cards(
    db: AsyncSession,
    requested_cards: list[str],
) -> list[str]:
    """Resolve user-entered card names into canonical card keys."""
    alias_to_key: dict[str, str] = {}

    for key in recommender.all_card_keys:
        for alias in _card_aliases(key):
            alias_to_key[alias] = key

    result = await db.execute(select(Card.sc_key, Card.name))
    for sc_key, name in result.all():
        for alias in _card_aliases(sc_key, name):
            alias_to_key[alias] = sc_key

    resolved: list[str] = []
    unknown: list[str] = []

    for raw_card in requested_cards:
        raw_card = raw_card.strip()
        if not raw_card:
            continue

        key = None
        for alias in _card_aliases(raw_card):
            if alias in alias_to_key:
                key = alias_to_key[alias]
                break

        if key is None:
            unknown.append(raw_card)
        elif key not in resolved:
            resolved.append(key)

    if unknown:
        card_list = ", ".join(unknown)
        raise HTTPException(
            status_code=400,
            detail=f"Unknown required card: {card_list}. Use a Clash Royale card name, such as Hog Rider.",
        )

    return resolved


# --- Endpoints ---


@router.post("/recommend", dependencies=[Depends(verify_bff_origin)])
async def recommend_deck(
    request: RecommendRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(require_existing_user_id),
) -> RecommendResponse:
    """
    Generate 3 deck recommendations for a player.

    Fetches player data from cache (must call /api/players/{tag} first),
    runs through the hybrid ML model, and returns recommendations
    with detailed explanations.
    """
    try:
        normalized = normalize_tag_input(request.player_tag)
        candidates = [to_hash_tag(candidate) for candidate in build_tag_candidates(normalized)]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    player = None
    for candidate in candidates:
        result = await db.execute(select(Player).where(Player.tag == candidate))
        player = result.scalar_one_or_none()
        if player is not None:
            break

    if not player:
        raise HTTPException(
            status_code=404,
            detail="Player not found in cache. Call GET /api/players/{tag} first to fetch their data. Use 0, not O.",
        )

    link_result = await db.execute(
        select(UserPlayer).where(
            UserPlayer.user_id == user_id,
            UserPlayer.player_tag == player.tag,
        )
    )
    if link_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=403,
            detail="This player profile is not linked to your account. Fetch the player profile first.",
        )

    # Check if model is trained
    if not recommender.is_trained:
        # Try to load from disk
        if not recommender.load():
            raise HTTPException(
                status_code=503,
                detail="ML model is not trained yet. Run the training pipeline first.",
            )

    # Run recommendation
    card_levels = player.card_levels or {}
    required_cards = await resolve_required_cards(db, request.required_cards)
    results = recommender.recommend(
        player_card_levels=card_levels,
        archetype_pref=request.archetype_preference,
        required_cards=required_cards,
        top_k=3,
    )

    if not results:
        if required_cards:
            required_display = ", ".join(_display_card_name(card) for card in required_cards)
            raise HTTPException(
                status_code=404,
                detail=f"No deck recommendations available with {required_display}. Try another card or remove the optional card filter.",
            )
        raise HTTPException(
            status_code=404,
            detail="No deck recommendations available. The model may need more training data.",
        )

    # Build response with explanations
    recommendations = []
    for r in results:
        deck = r["deck"]
        scores = r["scores"]

        explanation = generate_explanation(
            deck=deck,
            scores=scores,
            player_card_levels=card_levels,
            player_trophies=player.trophies,
            archetype_pref=request.archetype_preference,
            required_cards=required_cards,
            synergy_map=recommender.synergy_map,
        )

        short = generate_short_summary(deck, scores)

        card_names = [_display_card_name(k) for k in deck.get("card_keys", [])]

        recommendations.append(DeckRecommendation(
            cards=card_names,
            archetype=deck.get("archetype", "unknown"),
            win_rate=round(deck.get("win_rate", 0.0), 4),
            level_fit_score=round(scores.get("level_fit", 0.0), 4),
            overall_score=round(scores.get("overall", 0.0), 4),
            explanation=explanation,
            short_summary=short,
        ))

    # Player summary
    all_levels = list(card_levels.values()) if card_levels else [0]
    player_summary = PlayerSummary(
        name=player.name,
        trophies=player.trophies,
        arena_name=player.arena_name,
        max_card_level=max(all_levels) if all_levels else 0,
        avg_card_level=round(sum(all_levels) / len(all_levels), 1) if all_levels else 0.0,
    )

    return RecommendResponse(
        recommendations=recommendations,
        player_summary=player_summary,
        required_cards=[_display_card_name(card) for card in required_cards],
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
        top_decks.append({
            "cards": card_names,
            "archetype": d.archetype or "unknown",
            "win_rate": round(d.win_rate, 4),
            "usage_rate": round(d.usage_rate, 4),
            "avg_elixir": round(d.avg_elixir, 1),
        })
        arch = d.archetype or "unknown"
        archetype_counts[arch] = archetype_counts.get(arch, 0) + 1

    return MetaTrendsResponse(
        top_decks=top_decks,
        archetype_distribution=archetype_counts,
    )
