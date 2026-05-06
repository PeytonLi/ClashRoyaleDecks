"""
SQLAlchemy ORM models for the Clash Royale Deck Recommender.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Card(Base):
    """All Clash Royale cards with static properties."""

    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sc_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, comment="Supercell internal key e.g. 'hog-rider'")
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    elixir: Mapped[int] = mapped_column(Integer, nullable=False)
    rarity: Mapped[str] = mapped_column(String(20), nullable=False, comment="common, rare, epic, legendary, champion")
    card_type: Mapped[str] = mapped_column(String(30), nullable=False, comment="troop, spell, building")
    arena_unlock: Mapped[int] = mapped_column(Integer, default=0, comment="Arena number where card unlocks")
    icon_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    max_level: Mapped[int] = mapped_column(Integer, default=14)
    supports_evolution: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_hero: Mapped[bool] = mapped_column(Boolean, default=False)
    base_sc_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return f"<Card(name='{self.name}', elixir={self.elixir}, rarity='{self.rarity}')>"


class MetaDeck(Base):
    """Scraped meta decks from RoyaleAPI, ladder, Kaggle, etc."""

    __tablename__ = "meta_decks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    deck_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="SHA256 of sorted card keys for dedup")
    card_keys: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, comment="Array of 8 card sc_keys")
    deck_slots: Mapped[list[dict]] = mapped_column(JSONB, default=list, comment="8 slots with card_key, form, and slot_type")
    archetype: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, comment="cycle, beatdown, bridge_spam, control, bait")
    win_rate: Mapped[float] = mapped_column(Float, default=0.0)
    usage_rate: Mapped[float] = mapped_column(Float, default=0.0)
    avg_elixir: Mapped[float] = mapped_column(Float, default=0.0)
    trophy_range_low: Mapped[int] = mapped_column(Integer, default=0)
    trophy_range_high: Mapped[int] = mapped_column(Integer, default=9000)
    season: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="e.g. '2026-03'")
    source: Mapped[str] = mapped_column(String(30), default="unknown", comment="royaleapi, ladder, kaggle, manual")
    sample_size: Mapped[int] = mapped_column(Integer, default=0, comment="Number of games this deck was observed in")
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<MetaDeck(hash='{self.deck_hash[:8]}...', archetype='{self.archetype}', win_rate={self.win_rate})>"


class Player(Base):
    """Cached player profiles from the Clash Royale API."""

    __tablename__ = "players"

    tag: Mapped[str] = mapped_column(String(20), primary_key=True, comment="Player tag e.g. '#ABC123'")
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    trophies: Mapped[int] = mapped_column(Integer, default=0)
    best_trophies: Mapped[int] = mapped_column(Integer, default=0)
    arena_id: Mapped[int] = mapped_column(Integer, default=0)
    arena_name: Mapped[str] = mapped_column(String(100), default="")
    exp_level: Mapped[int] = mapped_column(Integer, default=1)
    card_levels: Mapped[dict] = mapped_column(JSONB, default=dict, comment="{ 'hog-rider': 14, 'fireball': 13, ... }")
    cards_owned: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, comment="List of card sc_keys the player owns")
    special_card_unlocks: Mapped[dict] = mapped_column(JSONB, default=dict, comment="{ evolutions: [], heroes: [], champions: [] }")
    last_fetched: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<Player(tag='{self.tag}', name='{self.name}', trophies={self.trophies})>"


class User(Base):
    """Application account used for login, ownership, and per-user quota."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    google_sub: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"


class UserPlayer(Base):
    """User-owned link to a cached Clash Royale player profile."""

    __tablename__ = "user_players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    player_tag: Mapped[str] = mapped_column(ForeignKey("players.tag", ondelete="CASCADE"), nullable=False)
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "player_tag", name="uq_user_player"),
    )

    def __repr__(self) -> str:
        return f"<UserPlayer(user_id={self.user_id}, player_tag='{self.player_tag}')>"


class UsageTracking(Base):
    """Track free tier usage by IP address."""

    __tablename__ = "usage_tracking"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ip_address: Mapped[str] = mapped_column(String(45), unique=True, nullable=False, comment="IPv4 or IPv6")
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False, comment="True if user has paid for unlimited access")
    first_used: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_used: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<UsageTracking(ip='{self.ip_address}', count={self.usage_count}, paid={self.is_paid})>"


class CardSynergy(Base):
    """Learned card-pair synergy scores computed from meta deck data."""

    __tablename__ = "card_synergies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    card_a_key: Mapped[str] = mapped_column(String(100), nullable=False)
    card_b_key: Mapped[str] = mapped_column(String(100), nullable=False)
    synergy_score: Mapped[float] = mapped_column(Float, default=0.0, comment="Normalized co-occurrence score weighted by win rate")
    co_occurrence_count: Mapped[int] = mapped_column(Integer, default=0, comment="Number of decks containing both cards")
    avg_win_rate: Mapped[float] = mapped_column(Float, default=0.0, comment="Avg win rate of decks containing both cards")
    season: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("card_a_key", "card_b_key", "season", name="uq_card_pair_season"),
    )

    def __repr__(self) -> str:
        return f"<CardSynergy(a='{self.card_a_key}', b='{self.card_b_key}', score={self.synergy_score})>"
