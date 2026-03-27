"""
Data scraper for meta decks from multiple sources.

Sources:
- Clash Royale Official API (top player battle logs)
- RoyaleAPI (meta deck pages)
- Kaggle datasets (historical data)
"""

import asyncio
import hashlib
import logging
import random
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.archetype_classifier import classify_archetype, compute_avg_elixir
from app.models import Card, CardSynergy, MetaDeck
from app.services.cr_api import CRApiClient

logger = logging.getLogger(__name__)


def deck_hash(card_keys: list[str]) -> str:
    """Generate a deterministic hash for a deck (sorted card keys)."""
    sorted_keys = sorted(card_keys)
    return hashlib.sha256(",".join(sorted_keys).encode()).hexdigest()


class DeckScraper:
    """Scrapes and stores meta decks from various sources."""

    def __init__(self, db: AsyncSession, cr_client: Optional[CRApiClient] = None):
        self.db = db
        self.cr_client = cr_client or CRApiClient()

    async def scrape_top_ladder(self, max_players: int = 50) -> int:
        """
        Scrape decks from top ladder players' battle logs.

        1. Get top players from global leaderboard
        2. Fetch each player's battle log
        3. Extract winning deck compositions
        4. Classify archetypes and store in DB

        Returns number of decks inserted/updated.
        """
        count = 0
        try:
            top_players = await self.cr_client.get_top_players()
            logger.info(f"Fetched {len(top_players)} top players from leaderboard")

            for player_info in top_players[:max_players]:
                tag = player_info.get("tag", "")
                if not tag:
                    continue

                try:
                    battles = await self.cr_client.get_battle_log(tag)
                    trophies = player_info.get("trophies", 0)

                    for battle in battles:
                        if not battle.get("won"):
                            continue

                        team_deck = battle.get("team_deck", [])
                        if len(team_deck) != 8:
                            continue

                        inserted = await self._upsert_deck(
                            card_keys=team_deck,
                            trophy_range_low=max(0, trophies - 200),
                            trophy_range_high=trophies + 200,
                            source="ladder",
                        )
                        if inserted:
                            count += 1

                except Exception as e:
                    logger.warning(f"Error fetching battle log for {tag}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error scraping top ladder: {e}")

        logger.info(f"Scraped {count} winning decks from top ladder")
        return count

    async def import_deck_list(
        self,
        decks: list[dict],
        source: str = "manual",
    ) -> int:
        """
        Import a list of decks from any source (Kaggle, CSV, manual).

        Each dict should have: card_keys (list[str]), and optionally:
        win_rate, usage_rate, trophy_range_low, trophy_range_high, season.

        Returns number of decks inserted/updated.
        """
        count = 0
        for deck_data in decks:
            card_keys = deck_data.get("card_keys", [])
            if len(card_keys) != 8:
                continue

            inserted = await self._upsert_deck(
                card_keys=card_keys,
                win_rate=deck_data.get("win_rate", 0.0),
                usage_rate=deck_data.get("usage_rate", 0.0),
                trophy_range_low=deck_data.get("trophy_range_low", 0),
                trophy_range_high=deck_data.get("trophy_range_high", 9000),
                season=deck_data.get("season"),
                source=source,
                sample_size=deck_data.get("sample_size", 1),
            )
            if inserted:
                count += 1

        await self.db.commit()
        logger.info(f"Imported {count} decks from {source}")
        return count

    async def _upsert_deck(
        self,
        card_keys: list[str],
        win_rate: float = 0.0,
        usage_rate: float = 0.0,
        trophy_range_low: int = 0,
        trophy_range_high: int = 9000,
        season: Optional[str] = None,
        source: str = "unknown",
        sample_size: int = 1,
    ) -> bool:
        """Insert or update a deck. Returns True if a new deck was inserted."""
        d_hash = deck_hash(card_keys)
        archetype = classify_archetype(card_keys)
        avg_elixir = compute_avg_elixir(card_keys)
        now = datetime.now(timezone.utc)

        if season is None:
            season = now.strftime("%Y-%m")

        stmt = pg_insert(MetaDeck).values(
            deck_hash=d_hash,
            card_keys=card_keys,
            archetype=archetype,
            win_rate=win_rate,
            usage_rate=usage_rate,
            avg_elixir=avg_elixir,
            trophy_range_low=trophy_range_low,
            trophy_range_high=trophy_range_high,
            season=season,
            source=source,
            sample_size=sample_size,
            scraped_at=now,
        ).on_conflict_do_update(
            index_elements=["deck_hash"],
            set_={
                "win_rate": MetaDeck.win_rate,  # Keep existing if conflict
                "usage_rate": MetaDeck.usage_rate,
                "sample_size": MetaDeck.sample_size + sample_size,
                "scraped_at": now,
            },
        )

        await self.db.execute(stmt)
        return True

    async def compute_synergies(self, season: Optional[str] = None) -> int:
        """
        Compute card-pair synergy scores from the meta_decks table.

        For each pair of cards that co-occur in decks, compute:
        - co_occurrence_count: how many winning decks contain both
        - avg_win_rate: average win rate of those decks
        - synergy_score: normalized score

        Returns number of synergy pairs computed.
        """
        current_season = season or datetime.now(timezone.utc).strftime("%Y-%m")

        # Fetch all meta decks for the season
        result = await self.db.execute(
            select(MetaDeck).where(MetaDeck.season == current_season)
        )
        decks = result.scalars().all()

        if not decks:
            logger.info("No decks found for synergy computation")
            return 0

        # Count co-occurrences
        pair_stats: dict[tuple[str, str], dict] = {}
        for d in decks:
            cards = sorted(d.card_keys)
            for i in range(len(cards)):
                for j in range(i + 1, len(cards)):
                    pair = (cards[i], cards[j])
                    if pair not in pair_stats:
                        pair_stats[pair] = {"count": 0, "total_wr": 0.0}
                    pair_stats[pair]["count"] += 1
                    pair_stats[pair]["total_wr"] += d.win_rate

        # Normalize and insert
        max_count = max(s["count"] for s in pair_stats.values()) if pair_stats else 1
        count = 0
        now = datetime.now(timezone.utc)

        for (card_a, card_b), stats in pair_stats.items():
            avg_wr = stats["total_wr"] / stats["count"] if stats["count"] > 0 else 0
            score = (stats["count"] / max_count) * avg_wr  # Normalized co-occurrence × win rate

            stmt = pg_insert(CardSynergy).values(
                card_a_key=card_a,
                card_b_key=card_b,
                synergy_score=round(score, 4),
                co_occurrence_count=stats["count"],
                avg_win_rate=round(avg_wr, 4),
                season=current_season,
                computed_at=now,
            ).on_conflict_do_update(
                constraint="uq_card_pair_season",
                set_={
                    "synergy_score": round(score, 4),
                    "co_occurrence_count": stats["count"],
                    "avg_win_rate": round(avg_wr, 4),
                    "computed_at": now,
                },
            )
            await self.db.execute(stmt)
            count += 1

        await self.db.commit()
        logger.info(f"Computed {count} card synergy pairs for season {current_season}")
        return count

    async def sync_cards_from_api(self) -> int:
        """
        Fetch all cards from the CR API and sync to the cards table.

        Returns number of cards synced.
        """
        cards_data = await self.cr_client.get_cards()
        count = 0

        for card in cards_data:
            stmt = pg_insert(Card).values(
                sc_key=card["sc_key"],
                name=card["name"],
                elixir=card["elixir"],
                rarity=card["rarity"],
                card_type="troop",  # API doesn't always distinguish, will refine
                icon_url=card.get("icon_url", ""),
                max_level=card.get("max_level", 14),
            ).on_conflict_do_update(
                index_elements=["sc_key"],
                set_={
                    "name": card["name"],
                    "elixir": card["elixir"],
                    "rarity": card["rarity"],
                    "icon_url": card.get("icon_url", ""),
                },
            )
            await self.db.execute(stmt)
            count += 1

        await self.db.commit()
        logger.info(f"Synced {count} cards from CR API")
        return count
