"""
Prediction router — deck recommendations and meta trends.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.ml.explainer import generate_explanation, generate_short_summary
from app.ml.model import recommender
from app.models import Player
from app.services.tag_utils import build_tag_candidates, normalize_tag_input, to_hash_tag

router = APIRouter()


# --- Request / Response schemas ---


class RecommendRequest(BaseModel):
    player_tag: str
    archetype_preference: Optional[str] = None  # cycle, beatdown, bridge_spam, control, bait


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


# --- Endpoints ---


@router.post("/recommend")
async def recommend_deck(
    request: RecommendRequest,
    db: AsyncSession = Depends(get_db),
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
    results = recommender.recommend(
        player_card_levels=card_levels,
        archetype_pref=request.archetype_preference,
        top_k=3,
    )

    if not results:
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
            synergy_map=recommender.synergy_map,
        )

        short = generate_short_summary(deck, scores)

        card_names = [k.replace("-", " ").title() for k in deck.get("card_keys", [])]

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
