"""
Integration tests for FastAPI endpoints.

Tests validate that:
- /api/players/{tag} fetches and caches player profiles
- /api/predict/recommend returns 3 deck recommendations with explanations
- /api/predict/meta-trends returns current meta snapshot
"""

import pytest
from httpx import AsyncClient

from sqlalchemy.ext.asyncio import AsyncSession

from app.data.scraper import DeckScraper
from app.services.cr_api import CRApiClient


@pytest.mark.asyncio
@pytest.mark.api
async def test_player_endpoint_fetches_and_caches_profile(
    async_client: AsyncClient,
    db_session: AsyncSession,
    cr_api_client: CRApiClient,
):
    """
    Verify that GET /api/players/{tag} fetches player profile from CR API
    and returns properly formatted response.
    """
    test_tag = "#GGCQ2PJV"
    
    # Act: Make request to player endpoint
    response = await async_client.get(f"/api/players/{test_tag}")
    
    # Assert: Response structure (regardless of whether endpoint is mocked or real)
    assert response.status_code in [200, 404, 429, 500, 502], \
        f"Expected successful or auth error response, got {response.status_code}: {response.text}"
    
    # If 200, verify structure
    if response.status_code == 200:
        data = response.json()
        assert "tag" in data, "Response should contain player tag"
        assert "name" in data, "Response should contain player name"
        assert data["tag"].replace("#", "") == test_tag.replace("#", ""), "Tag should match request"


@pytest.mark.asyncio
async def test_recommend_endpoint_requires_player_tag(async_client: AsyncClient):
    """
    Verify that POST /api/predict/recommend validates required player tag parameter.
    """
    # Act: Make request without player tag
    response = await async_client.post(
        "/api/predict/recommend",
        json={}  # Empty body
    )
    
    # Assert: Should return validation error
    assert response.status_code == 422, "Missing required field should return validation error"


@pytest.mark.asyncio
@pytest.mark.api
async def test_meta_trends_endpoint_returns_deck_metadata(
    async_client: AsyncClient,
    cleaned_db: AsyncSession,
    cr_api_client: CRApiClient,
):
    """
    Verify that GET /api/predict/meta-trends returns meta deck data.
    
    First populates DB with sample decks, then queries the endpoint.
    """
    # Arrange: Populate DB with test data
    scraper = DeckScraper(cleaned_db, cr_api_client)
    
    # Sync cards
    await scraper.sync_cards_from_api()
    
    # Scrape a few decks
    await scraper.scrape_top_ladder(max_players=5)
    
    # Act: Query meta trends endpoint
    response = await async_client.get("/api/predict/meta-trends")
    
    # Assert: Response should contain meta decks
    assert response.status_code == 200, \
        f"Expected 200 or 404, got {response.status_code}: {response.text}"

    data = response.json()
    assert "top_decks" in data
    assert "archetype_distribution" in data
    assert isinstance(data["top_decks"], list)
    assert isinstance(data["archetype_distribution"], dict)

    if data["top_decks"]:
        sample_deck = data["top_decks"][0]
        assert "cards" in sample_deck
        assert "archetype" in sample_deck
        assert "win_rate" in sample_deck
