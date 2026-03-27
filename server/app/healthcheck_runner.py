"""Deployment health checks for API, database, model, and scraper pipeline."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Awaitable, Callable
from urllib.request import urlopen
from typing_extensions import TypeAlias

from sqlalchemy import text

from app.database import async_session
from app.data.scraper import DeckScraper
from app.ml.model import recommender
from app.services.cr_api import CRApiClient, ClashRoyaleAPIError

HealthCheckCallable: TypeAlias = Callable[[], Awaitable[tuple[bool, str]]]


async def check_api_health(base_url: str = "http://127.0.0.1:8000") -> tuple[bool, str]:
    """Verify local API process responds healthy."""
    url = f"{base_url.rstrip('/')}/health"
    try:
        with urlopen(url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
            if response.status == 200 and payload.get("status") == "healthy":
                return True, "API /health is healthy"
            return False, f"Unexpected API /health payload: {payload}"
    except Exception as exc:
        return False, f"API health check failed: {exc}"


async def check_database() -> tuple[bool, str]:
    """Verify database connectivity via SQLAlchemy async session."""
    try:
        async with async_session() as db:
            result = await db.execute(text("SELECT 1"))
            value = result.scalar()
            if value == 1:
                return True, "Database connection OK"
            return False, f"Unexpected DB query result: {value}"
    except Exception as exc:
        return False, f"Database connection failed: {exc}"


async def check_supercell_api() -> tuple[bool, str]:
    """Verify Supercell API key works and can fetch top players."""
    api_key = os.getenv("CR_API_KEY", "").strip()
    if not api_key:
        return False, "CR_API_KEY is missing"

    client = CRApiClient(api_key=api_key)
    try:
        players = await client.get_top_players()
        if not players:
            return False, "Supercell API reachable but returned no top players"
        return True, f"Supercell API auth OK ({len(players)} top players fetched)"
    except ClashRoyaleAPIError as exc:
        return False, f"Supercell API error {exc.status_code}: {exc.message}"
    except Exception as exc:
        return False, f"Supercell API check failed: {exc}"
    finally:
        await client.close()


async def check_model_artifact() -> tuple[bool, str]:
    """Verify recommendation model artifact can be loaded from disk."""
    loaded = recommender.load()
    if loaded:
        return True, "Model artifact loaded successfully"
    return False, "Model artifact not loadable (deck_recommender.pkl missing or invalid)"


async def check_scraper_sync_cards() -> tuple[bool, str]:
    """Run scraper card sync and confirm rows were imported/upserted."""
    client = CRApiClient()
    try:
        async with async_session() as db:
            scraper = DeckScraper(db=db, cr_client=client)
            count = await scraper.sync_cards_from_api()
            if count > 0:
                return True, f"Scraper sync_cards_from_api OK ({count} cards)"
            return False, "Scraper sync_cards_from_api returned zero cards"
    except Exception as exc:
        return False, f"Scraper sync failed: {exc}"
    finally:
        await client.close()


def run_smoke_pytests() -> tuple[bool, str]:
    """Run a focused smoke subset of tests after deployment."""
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_scheduler.py::test_scheduler_registers_weekly_job_with_correct_cron",
        "tests/test_api_endpoints.py::test_recommend_endpoint_requires_player_tag",
        "-q",
    ]
    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if completed.returncode == 0:
            return True, "Smoke pytest checks passed"
        message = completed.stdout.strip() or completed.stderr.strip() or "unknown pytest failure"
        return False, f"Smoke pytest checks failed: {message}"
    except Exception as exc:
        return False, f"Smoke pytest execution failed: {exc}"


async def run_health_checks(
    include_api: bool = True,
    include_db: bool = True,
    include_supercell: bool = True,
    include_model: bool = True,
    include_scraper: bool = True,
    include_pytest: bool = False,
    api_base_url: str = "http://127.0.0.1:8000",
    printer: Callable[[str], None] = print,
) -> int:
    """Run selected checks and return process exit code."""
    checks: list[tuple[str, HealthCheckCallable]] = []

    if include_api:
        async def _api_check() -> tuple[bool, str]:
            return await check_api_health(api_base_url)

        checks.append(("api", _api_check))
    if include_db:
        checks.append(("database", check_database))
    if include_supercell:
        checks.append(("supercell", check_supercell_api))
    if include_model:
        checks.append(("model", check_model_artifact))
    if include_scraper:
        checks.append(("scraper", check_scraper_sync_cards))

    failures = 0
    for name, check in checks:
        ok, message = await check()
        status = "PASS" if ok else "FAIL"
        printer(f"[{status}] {name}: {message}")
        if not ok:
            failures += 1

    if include_pytest:
        ok, message = run_smoke_pytests()
        status = "PASS" if ok else "FAIL"
        printer(f"[{status}] smoke-tests: {message}")
        if not ok:
            failures += 1

    if failures == 0:
        printer("Deployment health checks passed.")
        return 0

    printer(f"Deployment health checks failed with {failures} failing check(s).")
    return 1
