"""
Players router — fetch and cache player profiles from the Clash Royale API.
"""

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_existing_user_id, verify_bff_origin
from app.models import Player, UserPlayer
from app.services.cr_api import ClashRoyaleAPIError, cr_api
from app.services.tag_utils import build_tag_candidates, normalize_tag_input, to_hash_tag

router = APIRouter(dependencies=[Depends(verify_bff_origin)])

CACHE_TTL_HOURS = 1  # Re-fetch from API if data is older than this


class PlayerResponse(BaseModel):
    tag: str
    name: str
    trophies: int
    best_trophies: int
    arena_id: int
    arena_name: str
    exp_level: int
    card_levels: dict[str, int]
    cards_owned: list[str]
    cached: bool = False


def _response_from_cached_player(cached_player: Player, cached: bool) -> PlayerResponse:
    return PlayerResponse(
        tag=cached_player.tag,
        name=cached_player.name,
        trophies=cached_player.trophies,
        best_trophies=cached_player.best_trophies,
        arena_id=cached_player.arena_id,
        arena_name=cached_player.arena_name,
        exp_level=cached_player.exp_level,
        card_levels=cached_player.card_levels,
        cards_owned=cached_player.cards_owned,
        cached=cached,
    )


def _response_from_api_data(resolved_tag: str, player_data: dict) -> PlayerResponse:
    return PlayerResponse(
        tag=resolved_tag,
        name=player_data["name"],
        trophies=player_data["trophies"],
        best_trophies=player_data["best_trophies"],
        arena_id=player_data["arena_id"],
        arena_name=player_data["arena_name"],
        exp_level=player_data["exp_level"],
        card_levels=player_data["card_levels"],
        cards_owned=player_data["cards_owned"],
        cached=False,
    )


async def _link_player_to_user(db: AsyncSession, user_id: int, player_tag: str) -> None:
    result = await db.execute(
        select(UserPlayer).where(
            UserPlayer.user_id == user_id,
            UserPlayer.player_tag == player_tag,
        )
    )
    if result.scalar_one_or_none() is None:
        db.add(UserPlayer(user_id=user_id, player_tag=player_tag))


@router.get("/{tag}")
async def get_player(
    tag: str,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(require_existing_user_id),
) -> PlayerResponse:
    """
    Fetch a player's profile by tag.

    First checks the database cache. If the cached data is fresh (< 1 hour),
    returns it. Otherwise, fetches from the Clash Royale API and updates cache.
    """
    try:
        normalized = normalize_tag_input(tag)
        candidates = build_tag_candidates(normalized)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    for candidate in candidates:
        clean_tag = to_hash_tag(candidate)

        # Check cache candidate first
        result = await db.execute(select(Player).where(Player.tag == clean_tag))
        cached_player = result.scalar_one_or_none()

        if cached_player:
            age = datetime.now(timezone.utc) - cached_player.last_fetched
            if age < timedelta(hours=CACHE_TTL_HOURS):
                await _link_player_to_user(db, user_id, clean_tag)
                await db.commit()
                return _response_from_cached_player(cached_player, cached=True)

        # Fetch candidate from CR API
        try:
            player_data = await cr_api.get_player(clean_tag)
        except ClashRoyaleAPIError as e:
            if e.status_code == 404:
                continue
            if e.status_code == 429:
                raise HTTPException(status_code=429, detail="Rate limited. Please try again shortly.")
            if e.status_code == 403:
                raise HTTPException(status_code=500, detail="API configuration error. Contact support.")
            raise HTTPException(status_code=502, detail=f"Clash Royale API error: {e.message}")

        now = datetime.now(timezone.utc)

        # Upsert resolved candidate into cache
        if cached_player:
            cached_player.name = player_data["name"]
            cached_player.trophies = player_data["trophies"]
            cached_player.best_trophies = player_data["best_trophies"]
            cached_player.arena_id = player_data["arena_id"]
            cached_player.arena_name = player_data["arena_name"]
            cached_player.exp_level = player_data["exp_level"]
            cached_player.card_levels = player_data["card_levels"]
            cached_player.cards_owned = player_data["cards_owned"]
            cached_player.last_fetched = now
        else:
            db.add(Player(
                tag=clean_tag,
                name=player_data["name"],
                trophies=player_data["trophies"],
                best_trophies=player_data["best_trophies"],
                arena_id=player_data["arena_id"],
                arena_name=player_data["arena_name"],
                exp_level=player_data["exp_level"],
                card_levels=player_data["card_levels"],
                cards_owned=player_data["cards_owned"],
                last_fetched=now,
            ))

        await _link_player_to_user(db, user_id, clean_tag)
        await db.commit()
        return _response_from_api_data(clean_tag, player_data)

    raise HTTPException(
        status_code=404,
        detail="Player not found after trying tag variants. Check the tag and use 0, not O.",
    )
