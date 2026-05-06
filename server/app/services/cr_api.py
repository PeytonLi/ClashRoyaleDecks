"""
Clash Royale Official API client.

Uses httpx for async HTTP requests with rate limiting and caching.
API docs: https://developer.clashroyale.com
"""

import os
from datetime import datetime, timezone
from typing import Any, Optional
import httpx
from dotenv import load_dotenv

from app.services.deck_forms import (
    base_card_key_from_api_card,
    card_key_from_name,
    extract_special_unlocks,
    make_base_slots,
    slots_from_api_cards,
    supports_evolution_from_api_card,
    supports_hero_from_api_card,
)

load_dotenv()

CR_API_BASE = "https://api.clashroyale.com/v1"
CR_API_KEY = os.getenv("CR_API_KEY", "")


class ClashRoyaleAPIError(Exception):
    """Raised when the Clash Royale API returns an error."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"CR API Error {status_code}: {message}")


class CRApiClient:
    """Async client for the Clash Royale Official API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or CR_API_KEY
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=CR_API_BASE,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "application/json",
                },
                timeout=15.0,
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _request(self, endpoint: str) -> dict[str, Any]:
        """Make an authenticated GET request to the CR API."""
        client = await self._get_client()
        # URL-encode the '#' in player tags
        response = await client.get(endpoint)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise ClashRoyaleAPIError(404, "Player not found. Check the tag and try again.")
        elif response.status_code == 429:
            raise ClashRoyaleAPIError(429, "Rate limited. Please try again in a few seconds.")
        elif response.status_code == 403:
            raise ClashRoyaleAPIError(403, "Invalid API key or IP not whitelisted.")
        else:
            raise ClashRoyaleAPIError(response.status_code, response.text)

    def _encode_tag(self, tag: str) -> str:
        """URL-encode a player tag (replace # with %23)."""
        tag = tag.strip()
        if not tag.startswith("#"):
            tag = f"#{tag}"
        return tag.replace("#", "%23")

    def _parse_deck_cards(self, cards: list[dict[str, Any]]) -> tuple[list[str], list[dict[str, str]]]:
        card_keys = [base_card_key_from_api_card(card) for card in cards]
        if len(card_keys) != 8:
            return card_keys, []
        try:
            slots = slots_from_api_cards(cards)
        except ValueError:
            slots = make_base_slots(card_keys)
        return [slot["card_key"] for slot in slots], slots

    async def get_player(self, tag: str) -> dict[str, Any]:
        """
        Fetch a player's profile by tag.

        Returns parsed data with card levels extracted.
        """
        encoded_tag = self._encode_tag(tag)
        data = await self._request(f"/players/{encoded_tag}")

        # Extract card levels into a clean dict
        card_levels: dict[str, int] = {}
        cards_owned: list[str] = []
        profile_cards = data.get("cards", [])
        for card in profile_cards:
            key = base_card_key_from_api_card(card)
            if key:
                card_levels[key] = card.get("level", 1)
                cards_owned.append(key)

        return {
            "tag": data.get("tag", tag),
            "name": data.get("name", "Unknown"),
            "trophies": data.get("trophies", 0),
            "best_trophies": data.get("bestTrophies", 0),
            "arena_id": data.get("arena", {}).get("id", 0),
            "arena_name": data.get("arena", {}).get("name", "Unknown"),
            "exp_level": data.get("expLevel", 1),
            "card_levels": card_levels,
            "cards_owned": cards_owned,
            "special_card_unlocks": extract_special_unlocks(profile_cards),
        }

    async def get_battle_log(self, tag: str) -> list[dict[str, Any]]:
        """
        Fetch a player's last 25 battles.

        Extracts deck compositions and outcomes.
        """
        encoded_tag = self._encode_tag(tag)
        battles = await self._request(f"/players/{encoded_tag}/battlelog")

        parsed_battles = []
        for battle in battles:
            team = battle.get("team", [{}])
            opponent = battle.get("opponent", [{}])

            if not team or not opponent:
                continue

            team_cards = team[0].get("cards", [])
            opponent_cards = opponent[0].get("cards", [])
            team_deck, team_deck_slots = self._parse_deck_cards(team_cards)
            opp_deck, opponent_deck_slots = self._parse_deck_cards(opponent_cards)

            team_crowns = team[0].get("crowns", 0)
            opp_crowns = opponent[0].get("crowns", 0)

            parsed_battles.append({
                "type": battle.get("type", "unknown"),
                "team_deck": team_deck,
                "team_deck_slots": team_deck_slots,
                "opponent_deck": opp_deck,
                "opponent_deck_slots": opponent_deck_slots,
                "team_crowns": team_crowns,
                "opponent_crowns": opp_crowns,
                "won": team_crowns > opp_crowns,
                "battle_time": battle.get("battleTime", ""),
            })

        return parsed_battles

    async def get_top_players(self, location_id: str = "global") -> list[dict[str, Any]]:
        """Fetch top players from the leaderboard."""
        endpoint = f"/locations/{location_id}/pathoflegend/players"
        if location_id == "global":
            endpoint = "/locations/global/pathoflegend/players"

        data = await self._request(endpoint)
        return data.get("items", [])

    async def get_cards(self) -> list[dict[str, Any]]:
        """Fetch the full list of Clash Royale cards."""
        data = await self._request("/cards")
        cards = []
        for card in data.get("items", []):
            cards.append({
                "sc_key": base_card_key_from_api_card(card) or card_key_from_name(card.get("name", "")),
                "name": card.get("name", ""),
                "elixir": card.get("elixirCost", 0),
                "rarity": card.get("rarity", "common").lower(),
                "icon_url": card.get("iconUrls", {}).get("medium", ""),
                "max_level": card.get("maxLevel", 14),
                "supports_evolution": supports_evolution_from_api_card(card),
                "supports_hero": supports_hero_from_api_card(card),
                "base_sc_key": base_card_key_from_api_card(card) or card_key_from_name(card.get("name", "")),
            })
        return cards


# Singleton client
cr_api = CRApiClient()
