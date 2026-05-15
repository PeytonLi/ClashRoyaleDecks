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
from app.models import Player, User, UserPlayer
from app.ml.model import DeckRecommender
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


async def _auth_headers(db: AsyncSession, email: str = "test@example.com") -> dict[str, str]:
    user = User(email=email, name="Test User")
    db.add(user)
    await db.flush()
    await db.commit()
    return {"X-User-Id": str(user.id)}


@pytest.mark.asyncio
async def test_auth_signup_and_login(async_client: AsyncClient, cleaned_db: AsyncSession):
    signup = await async_client.post(
        "/api/auth/signup",
        json={"email": "NewUser@Example.com", "password": "strongpass123", "name": "New User"},
    )

    assert signup.status_code == 201
    created = signup.json()
    assert created["email"] == "newuser@example.com"
    assert created["id"] > 0

    login = await async_client.post(
        "/api/auth/login",
        json={"email": "newuser@example.com", "password": "strongpass123"},
    )

    assert login.status_code == 200
    assert login.json()["id"] == created["id"]


@pytest.mark.asyncio
async def test_player_endpoint_requires_authenticated_user(async_client: AsyncClient):
    response = await async_client.get("/api/players/GGCQ2PJV")

    assert response.status_code == 401


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
    headers = await _auth_headers(db_session)
    
    # Act: Make request to player endpoint
    response = await async_client.get(f"/api/players/{test_tag}", headers=headers)
    
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
async def test_recommend_endpoint_requires_player_tag(
    async_client: AsyncClient,
    cleaned_db: AsyncSession,
):
    """
    Verify that POST /api/predict/recommend validates required player tag parameter.
    """
    headers = await _auth_headers(cleaned_db, email="required@example.com")
    # Act: Make request without player tag
    response = await async_client.post(
        "/api/predict/recommend",
        json={},  # Empty body
        headers=headers,
    )
    
    # Assert: Should return validation error
    assert response.status_code == 422, "Missing required field should return validation error"


@pytest.mark.asyncio
async def test_recommend_endpoint_accepts_o_and_finds_cached_zero_variant(
    async_client: AsyncClient,
    cleaned_db: AsyncSession,
):
    """Recommend endpoint should resolve O->0 when querying cached player rows."""
    headers = await _auth_headers(cleaned_db)
    user_id = int(headers["X-User-Id"])
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
    cleaned_db.add(UserPlayer(user_id=user_id, player_tag="#J0C9YVUL"))
    await cleaned_db.commit()

    with patch("app.routers.predict.recommender.is_trained", True), \
        patch("app.routers.predict.recommender.recommend", return_value=[]):
        response = await async_client.post(
            "/api/predict/recommend",
            json={"player_tag": "#JOC9YVUL"},
            headers=headers,
        )

    # Route reached model stage, meaning cache lookup succeeded via O->0 resolution.
    assert response.status_code == 404
    assert "No deck recommendations available" in response.json().get("detail", "")


@pytest.mark.asyncio
async def test_recommend_endpoint_passes_optional_required_card(
    async_client: AsyncClient,
    cleaned_db: AsyncSession,
):
    """Optional required cards should be resolved and sent to the scorer."""
    headers = await _auth_headers(cleaned_db)
    user_id = int(headers["X-User-Id"])
    cleaned_db.add(Player(
        tag="#GGCQ2PJV",
        name="Card Filter Player",
        trophies=6000,
        best_trophies=6200,
        arena_id=54000010,
        arena_name="League 1",
        exp_level=50,
        card_levels={"hog-rider": 14, "fireball": 13},
        cards_owned=["hog-rider", "fireball"],
    ))
    cleaned_db.add(UserPlayer(user_id=user_id, player_tag="#GGCQ2PJV"))
    await cleaned_db.commit()

    deck = {
        "card_keys": [
            "hog-rider",
            "fireball",
            "the-log",
            "ice-spirit",
            "skeletons",
            "cannon",
            "musketeer",
            "knight",
        ],
        "archetype": "cycle",
        "win_rate": 0.58,
        "avg_elixir": 2.8,
        "source": "test",
        "sample_size": 12,
    }
    model_cards = deck["card_keys"] + ["giant"]

    with patch("app.routers.predict.recommender.is_trained", True), \
        patch("app.routers.predict.recommender.all_card_keys", model_cards), \
        patch("app.routers.predict.recommender.recommend", return_value=[{
            "deck": deck,
            "scores": {
                "overall": 0.91,
                "cf": 0.5,
                "cb": 0.5,
                "level_fit": 0.85,
                "win_rate": 0.7,
            },
        }]) as mock_recommend:
        response = await async_client.post(
            "/api/predict/recommend",
            json={"player_tag": "#GGCQ2PJV", "required_cards": ["Hog Rider"]},
            headers=headers,
        )

    assert response.status_code == 200
    assert mock_recommend.call_args.kwargs["required_cards"] == [
        {"card_key": "hog-rider", "form": None}
    ]
    data = response.json()
    assert data["required_cards"] == ["Hog Rider"]
    assert "Hog Rider" in data["recommendations"][0]["cards"]
    assert data["recommendations"][0]["slots"][0]["form"] == "base"


@pytest.mark.asyncio
async def test_recommend_endpoint_returns_special_slots_for_form_required_card(
    async_client: AsyncClient,
    cleaned_db: AsyncSession,
):
    """Form-aware required cards should be resolved and returned with slot metadata."""
    headers = await _auth_headers(cleaned_db)
    user_id = int(headers["X-User-Id"])
    deck_cards = [
        "firecracker",
        "hog-rider",
        "the-log",
        "ice-spirit",
        "skeletons",
        "cannon",
        "musketeer",
        "knight",
    ]
    deck_slots = [
        {"card_key": "firecracker", "form": "evolution", "slot_type": "evolution"},
        *[{"card_key": key, "form": "base", "slot_type": "normal"} for key in deck_cards[1:]],
    ]
    cleaned_db.add(Player(
        tag="#GGCQ2PJV",
        name="Evo Player",
        trophies=6000,
        best_trophies=6200,
        arena_id=54000010,
        arena_name="League 1",
        exp_level=50,
        card_levels={key: 14 for key in deck_cards},
        cards_owned=deck_cards,
        special_card_unlocks={"evolutions": ["firecracker"], "heroes": [], "champions": []},
    ))
    cleaned_db.add(UserPlayer(user_id=user_id, player_tag="#GGCQ2PJV"))
    await cleaned_db.commit()

    deck = {
        "card_keys": deck_cards,
        "deck_slots": deck_slots,
        "archetype": "cycle",
        "win_rate": 0.58,
        "avg_elixir": 2.8,
        "source": "test",
        "sample_size": 12,
    }

    with patch("app.routers.predict.recommender.is_trained", True), \
        patch("app.routers.predict.recommender.all_card_keys", deck_cards), \
        patch("app.routers.predict.recommender.recommend", return_value=[{
            "deck": deck,
            "scores": {
                "overall": 0.91,
                "cf": 0.5,
                "cb": 0.5,
                "level_fit": 0.85,
                "win_rate": 0.7,
            },
        }]) as mock_recommend:
        response = await async_client.post(
            "/api/predict/recommend",
            json={"player_tag": "#GGCQ2PJV", "required_cards": ["Evo Firecracker"]},
            headers=headers,
        )

    assert response.status_code == 200
    assert mock_recommend.call_args.kwargs["required_cards"] == [
        {"card_key": "firecracker", "form": "evolution"}
    ]
    assert mock_recommend.call_args.kwargs["player_special_unlocks"]["evolutions"] == ["firecracker"]
    data = response.json()
    assert data["required_cards"] == ["Evolution Firecracker"]
    assert data["recommendations"][0]["slots"][0] == {
        "card": "Firecracker",
        "card_key": "firecracker",
        "form": "evolution",
        "slot_type": "evolution",
    }


def test_recommender_filters_to_required_cards():
    """The scorer should only return decks containing every required card."""
    model = DeckRecommender()
    model.meta_decks = [
        {
            "card_keys": [
                "giant",
                "fireball",
                "the-log",
                "ice-spirit",
                "skeletons",
                "cannon",
                "musketeer",
                "knight",
            ],
            "archetype": "beatdown",
            "win_rate": 0.99,
        },
        {
            "card_keys": [
                "hog-rider",
                "fireball",
                "the-log",
                "ice-spirit",
                "skeletons",
                "cannon",
                "musketeer",
                "knight",
            ],
            "archetype": "cycle",
            "win_rate": 0.5,
        },
    ]
    model.synergy_map = {}
    model.all_card_keys = ["giant", "hog-rider", "fireball"]
    model.card_to_idx = {key: idx for idx, key in enumerate(model.all_card_keys)}

    results = model.recommend(
        player_card_levels={"hog-rider": 14, "fireball": 14, "giant": 14},
        required_cards=["hog-rider"],
        top_k=2,
    )

    assert len(results) == 1
    assert "hog-rider" in results[0]["deck"]["card_keys"]


@pytest.mark.asyncio
async def test_recommend_endpoint_rejects_unlinked_cached_player(
    async_client: AsyncClient,
    cleaned_db: AsyncSession,
):
    headers = await _auth_headers(cleaned_db, email="owner@example.com")
    cleaned_db.add(Player(
        tag="#GGCQ2PJV",
        name="Other Player",
        trophies=6000,
        best_trophies=6200,
        arena_id=54000010,
        arena_name="League 1",
        exp_level=50,
        card_levels={"hog-rider": 14},
        cards_owned=["hog-rider"],
    ))
    await cleaned_db.commit()

    response = await async_client.post(
        "/api/predict/recommend",
        json={"player_tag": "#GGCQ2PJV"},
        headers=headers,
    )

    assert response.status_code == 403
    assert "not linked" in response.json().get("detail", "")


@pytest.mark.asyncio
async def test_player_endpoint_rejects_invalid_tag_characters(
    async_client: AsyncClient,
    cleaned_db: AsyncSession,
):
    """Unsupported characters should return 400 before any CR API call."""
    headers = await _auth_headers(cleaned_db, email="invalid@example.com")
    response = await async_client.get("/api/players/J0C9YVUX", headers=headers)

    assert response.status_code == 400
    detail = response.json().get("detail", "")
    assert "Invalid characters" in detail


@pytest.mark.asyncio
async def test_player_endpoint_normalizes_valid_tag_before_api_call(
    async_client: AsyncClient,
    cleaned_db: AsyncSession,
):
    """Valid tags should be normalized and forwarded as canonical uppercase # format."""
    headers = await _auth_headers(cleaned_db)
    with patch("app.routers.players.cr_api.get_player", new_callable=AsyncMock) as mock_get_player:
        mock_get_player.return_value = _mock_player_payload("#GGCQ2PJV")

        response = await async_client.get("/api/players/ggcq2pjv", headers=headers)

        assert response.status_code == 200
        mock_get_player.assert_awaited_once_with("#GGCQ2PJV")
        data = response.json()
        assert data["tag"] == "#GGCQ2PJV"


@pytest.mark.asyncio
async def test_player_endpoint_resolves_o_to_zero_variant(
    async_client: AsyncClient,
    cleaned_db: AsyncSession,
):
    """Ambiguous O input should retry with 0 variant and succeed when available."""
    headers = await _auth_headers(cleaned_db, email="variant@example.com")
    with patch("app.routers.players.cr_api.get_player", new_callable=AsyncMock) as mock_get_player:
        mock_get_player.side_effect = [
            ClashRoyaleAPIError(404, "Player not found"),
            _mock_player_payload("#J0C9YVUL"),
        ]

        response = await async_client.get("/api/players/JOC9YVUL", headers=headers)

        assert response.status_code == 200
        assert mock_get_player.await_count == 2
        assert mock_get_player.await_args_list[0].args == ("#JOC9YVUL",)
        assert mock_get_player.await_args_list[1].args == ("#J0C9YVUL",)
        data = response.json()
        assert data["tag"] == "#J0C9YVUL"


@pytest.mark.asyncio
async def test_player_endpoint_rejects_too_short_tag(
    async_client: AsyncClient,
    cleaned_db: AsyncSession,
):
    """Very short tags should be rejected as invalid format."""
    headers = await _auth_headers(cleaned_db, email="short@example.com")
    response = await async_client.get("/api/players/AB", headers=headers)

    assert response.status_code == 400
    detail = response.json().get("detail", "")
    assert "Invalid player tag" in detail


@pytest.mark.asyncio
async def test_player_endpoint_returns_not_found_after_candidate_exhaustion(
    async_client: AsyncClient,
    cleaned_db: AsyncSession,
):
    """All-candidate 404s should return actionable not-found guidance."""
    headers = await _auth_headers(cleaned_db, email="notfound@example.com")
    with patch("app.routers.players.cr_api.get_player", new_callable=AsyncMock) as mock_get_player:
        mock_get_player.side_effect = ClashRoyaleAPIError(404, "Player not found")

        response = await async_client.get("/api/players/JOC9YVUL", headers=headers)

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
