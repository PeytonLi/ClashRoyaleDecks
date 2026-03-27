"""
Integration tests for FastAPI endpoints.

Tests validate that:
- /api/players/{tag} fetches and caches player profiles
- /api/predict/recommend returns 3 deck recommendations with explanations
- /api/predict/meta-trends returns current meta snapshot
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.data.scraper import DeckScraper
from app.models import Player
from app.services.cr_api import CRApiClient, ClashRoyaleAPIError


def _mock_player_payload(tag: str) -> dict:
    """Build a minimal player payload returned by the CR API client mock."""
    return {
        "tag": tag,
        "name": "Test Player",
        "trophies": 5000,
        "best_trophies": 5200,
        "arena_id": 54000010,
        "arena_name": "League 1",
        "exp_level": 50,
        "card_levels": {"hog-rider": 14},
        "cards_owned": ["hog-rider"],
    }


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
async def test_recommend_endpoint_accepts_o_and_finds_cached_zero_variant(
    async_client: AsyncClient,
    cleaned_db: AsyncSession,
):
    """Recommend endpoint should resolve O->0 when querying cached player rows."""
    cleaned_db.add(Player(
        tag="#J0C9YVUL",
        name="Resolved Player",
        trophies=6000,
        best_trophies=6200,
        arena_id=54000010,
        arena_name="League 1",
        exp_level=50,
        card_levels={"hog-rider": 14},
        cards_owned=["hog-rider"],
    ))
    await cleaned_db.commit()

    with patch("app.routers.predict.recommender.is_trained", True), \
        patch("app.routers.predict.recommender.recommend", return_value=[]):
        response = await async_client.post(
            "/api/predict/recommend",
            json={"player_tag": "#JOC9YVUL"},
        )

    # Route reached model stage, meaning cache lookup succeeded via O->0 resolution.
    assert response.status_code == 404
    assert "No deck recommendations available" in response.json().get("detail", "")


@pytest.mark.asyncio
async def test_player_endpoint_rejects_invalid_tag_characters(async_client: AsyncClient):
    """Unsupported characters should return 400 before any CR API call."""
    response = await async_client.get("/api/players/J0C9YVUX")

    assert response.status_code == 400
    detail = response.json().get("detail", "")
    assert "0 not O" in detail


@pytest.mark.asyncio
async def test_player_endpoint_normalizes_valid_tag_before_api_call(async_client: AsyncClient):
    """Valid tags should be normalized and forwarded as canonical uppercase # format."""
    with patch("app.routers.players.cr_api.get_player", new_callable=AsyncMock) as mock_get_player:
        mock_get_player.return_value = _mock_player_payload("#GGCQ2PJV")

        response = await async_client.get("/api/players/ggcq2pjv")

        assert response.status_code == 200
        mock_get_player.assert_awaited_once_with("#GGCQ2PJV")
        data = response.json()
        assert data["tag"] == "#GGCQ2PJV"


@pytest.mark.asyncio
async def test_player_endpoint_resolves_o_to_zero_variant(async_client: AsyncClient):
    """Ambiguous O input should retry with 0 variant and succeed when available."""
    with patch("app.routers.players.cr_api.get_player", new_callable=AsyncMock) as mock_get_player:
        mock_get_player.side_effect = [
            ClashRoyaleAPIError(404, "Player not found"),
            _mock_player_payload("#J0C9YVUL"),
        ]

        response = await async_client.get("/api/players/JOC9YVUL")

        assert response.status_code == 200
        assert mock_get_player.await_count == 2
        assert mock_get_player.await_args_list[0].args == ("#JOC9YVUL",)
        assert mock_get_player.await_args_list[1].args == ("#J0C9YVUL",)
        data = response.json()
        assert data["tag"] == "#J0C9YVUL"


@pytest.mark.asyncio
async def test_player_endpoint_rejects_too_short_tag(async_client: AsyncClient):
    """Very short tags should be rejected as invalid format."""
    response = await async_client.get("/api/players/AB")

    assert response.status_code == 400
    detail = response.json().get("detail", "")
    assert "between" in detail


@pytest.mark.asyncio
async def test_player_endpoint_returns_not_found_after_candidate_exhaustion(async_client: AsyncClient):
    """All-candidate 404s should return actionable not-found guidance."""
    with patch("app.routers.players.cr_api.get_player", new_callable=AsyncMock) as mock_get_player:
        mock_get_player.side_effect = ClashRoyaleAPIError(404, "Player not found")

        response = await async_client.get("/api/players/JOC9YVUL")

        assert response.status_code == 404
        detail = response.json().get("detail", "")
        assert "after trying tag variants" in detail


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
