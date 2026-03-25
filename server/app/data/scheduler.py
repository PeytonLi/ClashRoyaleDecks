"""
Weekly scheduler for data scraping and model retraining.

Uses APScheduler to run periodic jobs:
- Scrape top ladder decks
- Recompute card synergies
- Retrain ML model
"""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import async_session

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def weekly_scrape_and_retrain():
    """
    Weekly job that:
    1. Scrapes top ladder decks
    2. Recomputes synergy matrix
    3. Retrains the ML model
    """
    logger.info(f"Starting weekly scrape at {datetime.now(timezone.utc)}")

    async with async_session() as db:
        try:
            from app.data.scraper import DeckScraper
            from app.services.cr_api import CRApiClient

            client = CRApiClient()
            scraper = DeckScraper(db, client)

            # Step 1: Scrape top ladder
            deck_count = await scraper.scrape_top_ladder(max_players=50)
            logger.info(f"Scraped {deck_count} decks")

            # Step 2: Recompute synergies
            synergy_count = await scraper.compute_synergies()
            logger.info(f"Computed {synergy_count} synergy pairs")

            # Step 3: Retrain model
            from app.ml.trainer import retrain_model
            await retrain_model(db)
            logger.info("Model retrained successfully")

            await client.close()

        except Exception as e:
            logger.error(f"Weekly job failed: {e}", exc_info=True)

    logger.info("Weekly scrape complete")


def start_scheduler():
    """Start the weekly scheduler. Call this on app startup."""
    # Run every Sunday at 3:00 AM UTC
    scheduler.add_job(
        weekly_scrape_and_retrain,
        trigger=CronTrigger(day_of_week="sun", hour=3, minute=0),
        id="weekly_scrape",
        name="Weekly deck scrape and model retrain",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started — weekly scrape set for Sundays 3:00 AM UTC")


def stop_scheduler():
    """Stop the scheduler. Call this on app shutdown."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
