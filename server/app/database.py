"""
Database connection and session management using SQLAlchemy 2.0 + asyncpg.
"""

import os
from dotenv import load_dotenv

from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/clashroyale",
)

engine = create_async_engine(DATABASE_URL, echo=False, pool_size=5, max_overflow=10)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides a database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create all tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await ensure_schema_compatibility(conn)


async def ensure_schema_compatibility(conn):
    """Add columns introduced after initial create_all-based deployments."""
    await conn.execute(text(
        """
        ALTER TABLE cards
            ADD COLUMN IF NOT EXISTS supports_evolution BOOLEAN NOT NULL DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS supports_hero BOOLEAN NOT NULL DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS base_sc_key VARCHAR(100)
        """
    ))
    await conn.execute(text(
        """
        ALTER TABLE meta_decks
            ADD COLUMN IF NOT EXISTS deck_slots JSONB NOT NULL DEFAULT '[]'::jsonb
        """
    ))
    await conn.execute(text(
        """
        ALTER TABLE players
            ADD COLUMN IF NOT EXISTS special_card_unlocks JSONB NOT NULL DEFAULT
            '{"evolutions": [], "heroes": [], "champions": []}'::jsonb
        """
    ))
    await conn.execute(text(
        """
        UPDATE cards
        SET base_sc_key = sc_key
        WHERE base_sc_key IS NULL
        """
    ))
    await conn.execute(text(
        """
        UPDATE meta_decks
        SET deck_slots = (
            SELECT COALESCE(
                jsonb_agg(
                    jsonb_build_object(
                        'card_key', card_key,
                        'form', 'base',
                        'slot_type', 'normal'
                    )
                ),
                '[]'::jsonb
            )
            FROM unnest(card_keys) AS cards(card_key)
        )
        WHERE deck_slots = '[]'::jsonb OR deck_slots IS NULL
        """
    ))


async def close_db():
    """Dispose engine on shutdown."""
    await engine.dispose()
