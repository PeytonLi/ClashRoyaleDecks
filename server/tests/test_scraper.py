"""
Integration tests for the DeckScraper module.

Tests validate that:
- Scraper fetches cards from Supercell API and saves to DB
- Scraper fetches winning decks from top ladder and saves to DB
- Scraper computes card synergy pairs correctly
"""

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.scraper import DeckScraper
from app.models import Card, MetaDeck, CardSynergy
from app.services.cr_api import CRApiClient


@pytest.mark.asyncio
@pytest.mark.api
async def test_scraper_syncs_cards_from_supercell_api(cleaned_db: AsyncSession, cr_api_client: CRApiClient):
    """
    TRACER BULLET: Verify that scraper fetches cards from Supercell API and saves to DB.
    
    This is the foundational test that validates the entire scraper → DB pipeline.
    """
    # Arrange
    scraper = DeckScraper(cleaned_db, cr_api_client)
    
    # Act: Sync cards from the real Supercell API
    count = await scraper.sync_cards_from_api()
    
    # Assert: Cards were saved to the database
    assert count > 0, "Scraper should have imported at least one card"
    
    # Verify cards exist in DB
    result = await cleaned_db.execute(select(func.count()).select_from(Card))
    db_card_count = result.scalar_one()
    assert db_card_count > 0, "Database should contain cards after sync"
    assert db_card_count == count, "Count of synced cards should match DB record count"
    
    # Verify card data integrity
    result = await cleaned_db.execute(select(Card).limit(1))
    sample_card = result.scalar()
    
    assert sample_card is not None, "Should retrieve at least one card from DB"
    assert sample_card.name, "Card should have a name"
    assert sample_card.sc_key, "Card should have a sc_key (internal Supercell key)"
    assert sample_card.elixir >= 0, "Card elixir cost should be non-negative"
    assert sample_card.rarity.lower() in ["common", "rare", "epic", "legendary", "champion"], \
        "Card rarity should be one of the standard types"
    assert sample_card.max_level > 0, "Card max level should be positive"


@pytest.mark.asyncio
@pytest.mark.api
async def test_scraper_fetches_and_saves_top_ladder_decks(cleaned_db: AsyncSession, cr_api_client: CRApiClient):
    """
    Verify that scraper fetches winning decks from top ladder and saves them.
    
    Prerequisites: Cards must exist in DB (they will be referenced by decks).
    """
    # Arrange
    scraper = DeckScraper(cleaned_db, cr_api_client)
    
    # Step 1: Sync cards first (decks reference cards)
    await scraper.sync_cards_from_api()
    
    # Act: Scrape top ladder decks
    deck_count = await scraper.scrape_top_ladder(max_players=10)  # Small max to avoid rate limits
    
    # Assert: Decks were scraped
    assert deck_count > 0, "Scraper should have found at least one winning deck"
    
    # Verify decks exist in DB
    result = await cleaned_db.execute(select(func.count()).select_from(MetaDeck))
    db_deck_count = result.scalar_one()
    assert db_deck_count > 0, "Database should contain meta decks after scraping"
    
    # Verify deck structure
    result = await cleaned_db.execute(select(MetaDeck).limit(1))
    sample_deck = result.scalar()
    
    assert sample_deck is not None, "Should retrieve at least one deck from DB"
    assert len(sample_deck.card_keys) == 8, "Each deck should have exactly 8 cards"
    assert sample_deck.archetype is not None, "Deck should have an archetype classification"
    assert sample_deck.source == "ladder", "Deck source should be 'ladder'"
    assert sample_deck.trophy_range_low >= 0, "Trophy range low should be non-negative"
    assert sample_deck.trophy_range_high >= sample_deck.trophy_range_low, \
        "Trophy range high should be >= low"
    assert sample_deck.avg_elixir > 0, "Average elixir should be positive"


@pytest.mark.asyncio
@pytest.mark.api
async def test_scraper_computes_card_synergies(cleaned_db: AsyncSession, cr_api_client: CRApiClient):
    """
    Verify that scraper computes card-pair synergy scores from meta decks.
    
    Prerequisites: Cards and decks must exist.
    """
    # Arrange
    scraper = DeckScraper(cleaned_db, cr_api_client)
    
    # Step 1: Sync cards
    await scraper.sync_cards_from_api()
    
    # Step 2: Scrape top ladder decks (minimum 5 to have meaningful synergies)
    await scraper.scrape_top_ladder(max_players=10)
    
    # Act: Compute card synergies
    synergy_count = await scraper.compute_synergies()
    
    # Assert: Synergies were computed
    assert synergy_count > 0, "Scraper should have computed synergy pairs"
    
    # Verify synergies exist in DB
    result = await cleaned_db.execute(select(func.count()).select_from(CardSynergy))
    db_synergy_count = result.scalar_one()
    assert db_synergy_count > 0, "Database should contain synergy pairs"
    assert db_synergy_count == synergy_count, "Synergy count should match DB records"
    
    # Verify synergy data integrity
    result = await cleaned_db.execute(select(CardSynergy).limit(1))
    sample_synergy = result.scalar()
    
    assert sample_synergy is not None, "Should retrieve at least one synergy from DB"
    assert sample_synergy.card_a_key, "Synergy should reference card A"
    assert sample_synergy.card_b_key, "Synergy should reference card B"
    assert sample_synergy.card_a_key != sample_synergy.card_b_key, "Cards should be different"
    assert 0 <= sample_synergy.synergy_score <= 1, "Synergy score should be normalized (0-1)"
    assert sample_synergy.co_occurrence_count > 0, "Co-occurrence count should be positive"
    assert 0 <= sample_synergy.avg_win_rate <= 1, "Win rate should be normalized (0-1)"
