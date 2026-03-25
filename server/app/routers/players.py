"""
Players router — fetch and cache player profiles from the Clash Royale API.
"""

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Player
from app.services.cr_api import ClashRoyaleAPIError, cr_api

router = APIRouter()

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


@router.get("/{tag}")
async def get_player(tag: str, db: AsyncSession = Depends(get_db)) -> PlayerResponse:
    """
    Fetch a player's profile by tag.

    First checks the database cache. If the cached data is fresh (< 1 hour),
    returns it. Otherwise, fetches from the Clash Royale API and updates cache.
    """
    # Normalize tag
    clean_tag = tag.strip().upper()
    if not clean_tag.startswith("#"):
        clean_tag = f"#{clean_tag}"

    # Check cache
    result = await db.execute(select(Player).where(Player.tag == clean_tag))
    cached_player = result.scalar_one_or_none()

    if cached_player:
        age = datetime.now(timezone.utc) - cached_player.last_fetched
        if age < timedelta(hours=CACHE_TTL_HOURS):
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
                cached=True,
            )

    # Fetch from CR API
    try:
        player_data = await cr_api.get_player(clean_tag)
    except ClashRoyaleAPIError as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Player not found. Check the tag and try again.")
        elif e.status_code == 429:
            raise HTTPException(status_code=429, detail="Rate limited. Please try again shortly.")
        elif e.status_code == 403:
            raise HTTPException(status_code=500, detail="API configuration error. Contact support.")
        else:
            raise HTTPException(status_code=502, detail=f"Clash Royale API error: {e.message}")

    now = datetime.now(timezone.utc)

    # Upsert into cache
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
        new_player = Player(
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
        )
        db.add(new_player)

    await db.commit()

    return PlayerResponse(
        tag=clean_tag,
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
