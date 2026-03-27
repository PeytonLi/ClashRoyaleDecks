"""
Model training script.

Loads data from PostgreSQL, trains the hybrid model, and saves artifacts.
Can be run standalone or called by the scheduler.
"""

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Card, CardSynergy, MetaDeck
from app.ml.model import recommender
from app.database import async_session, init_db, close_db
from app.data.scraper import DeckScraper

logger = logging.getLogger(__name__)


async def retrain_model(db: AsyncSession):
    """
    Load fresh data from the database and retrain the model.
    """
    # 1. Load all cards
    result = await db.execute(select(Card).order_by(Card.sc_key))
    cards = result.scalars().all()
    all_card_keys = [c.sc_key for c in cards]

    if not all_card_keys:
        logger.warning("No cards in database — cannot train model")
        return

    # 2. Load meta decks
    result = await db.execute(select(MetaDeck))
    meta_deck_rows = result.scalars().all()
    meta_decks = [
        {
            "card_keys": d.card_keys,
            "archetype": d.archetype,
            "win_rate": d.win_rate,
            "usage_rate": d.usage_rate,
            "avg_elixir": d.avg_elixir,
            "trophy_range_low": d.trophy_range_low,
            "trophy_range_high": d.trophy_range_high,
            "season": d.season,
            "source": d.source,
            "sample_size": d.sample_size,
        }
        for d in meta_deck_rows
    ]

    if not meta_decks:
        logger.warning("No meta decks in database — cannot train model")
        return

    # 3. Load synergies
    result = await db.execute(select(CardSynergy))
    synergy_rows = result.scalars().all()
    synergies = [
        {
            "card_a_key": s.card_a_key,
            "card_b_key": s.card_b_key,
            "synergy_score": s.synergy_score,
        }
        for s in synergy_rows
    ]

    # 4. Load data into model and train
    recommender.load_data(meta_decks, synergies, all_card_keys)
    recommender.train()

    # 5. Save
    recommender.save()

    logger.info(
        f"Model retrained: {len(meta_decks)} decks, "
        f"{len(synergies)} synergy pairs, {len(all_card_keys)} cards"
    )

async def main():
    logging.basicConfig(level=logging.INFO)
    logger.info("Initializing database...")
    try:
        await init_db()
        
        logger.info("Starting initial data population pipeline...")
        async with async_session() as db:
            scraper = DeckScraper(db)
            
            logger.info("Importing card definitions...")
            await scraper.sync_cards_from_api()
            
            logger.info("Scraping top ladder decks (this may take a minute)...")
            await scraper.scrape_top_ladder()
            
            logger.info("Computing card synergies...")
            await scraper.compute_synergies()
            
            logger.info("Training hybrid ML model...")
            await retrain_model(db)
            
            logger.info("Pipeline complete! You can now start the API.")
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(main())
