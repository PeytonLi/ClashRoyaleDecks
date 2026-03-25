from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class Card(BaseModel):
    id: int
    name: str
    elixir: int
    rarity: str


class Deck(BaseModel):
    id: int
    name: str
    cards: List[Card]
    win_rate: Optional[float] = None


# Example data - replace with database later
SAMPLE_DECKS = [
    {
        "id": 1,
        "name": "Hog 2.6",
        "cards": [
            {"id": 1, "name": "Hog Rider", "elixir": 4, "rarity": "rare"},
            {"id": 2, "name": "Musketeer", "elixir": 4, "rarity": "rare"},
            {"id": 3, "name": "Ice Golem", "elixir": 2, "rarity": "rare"},
            {"id": 4, "name": "Skeletons", "elixir": 1, "rarity": "common"},
            {"id": 5, "name": "Ice Spirit", "elixir": 1, "rarity": "common"},
            {"id": 6, "name": "Cannon", "elixir": 3, "rarity": "common"},
            {"id": 7, "name": "Fireball", "elixir": 4, "rarity": "rare"},
            {"id": 8, "name": "The Log", "elixir": 2, "rarity": "legendary"},
        ],
        "win_rate": 0.52,
    },
]


@router.get("/")
async def get_decks() -> list[Deck]:
    """Get all decks."""
    return SAMPLE_DECKS


@router.get("/{deck_id}")
async def get_deck(deck_id: int) -> Deck:
    """Get a specific deck by ID."""
    for deck in SAMPLE_DECKS:
        if deck["id"] == deck_id:
            return deck
    raise HTTPException(status_code=404, detail="Deck not found")


class DeckCreate(BaseModel):
    name: str
    card_ids: List[int]


@router.post("/")
async def create_deck(deck: DeckCreate) -> dict:
    """Create a new deck."""
    # TODO: Implement deck creation with database
    return {"message": "Deck created", "name": deck.name}
