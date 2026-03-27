"""Tests for deployment healthcheck runner behavior."""

import pytest

from app import healthcheck_runner


@pytest.mark.asyncio
async def test_run_health_checks_all_pass(monkeypatch):
    """Runner returns 0 when all checks pass."""

    async def ok(*args, **kwargs):
        return True, "ok"

    monkeypatch.setattr(healthcheck_runner, "check_api_health", ok)
    monkeypatch.setattr(healthcheck_runner, "check_database", ok)
    monkeypatch.setattr(healthcheck_runner, "check_supercell_api", ok)
    monkeypatch.setattr(healthcheck_runner, "check_model_artifact", ok)
    monkeypatch.setattr(healthcheck_runner, "check_scraper_sync_cards", ok)
    monkeypatch.setattr(healthcheck_runner, "run_smoke_pytests", lambda: (True, "ok"))

    lines = []
    code = await healthcheck_runner.run_health_checks(include_pytest=True, printer=lines.append)

    assert code == 0
    assert any("[PASS] api" in line for line in lines)
    assert any("[PASS] smoke-tests" in line for line in lines)


@pytest.mark.asyncio
async def test_run_health_checks_reports_failures(monkeypatch):
    """Runner returns 1 when a selected check fails."""

    async def fail(*args, **kwargs):
        return False, "broken"

    async def ok(*args, **kwargs):
        return True, "ok"

    monkeypatch.setattr(healthcheck_runner, "check_api_health", ok)
    monkeypatch.setattr(healthcheck_runner, "check_database", fail)
    monkeypatch.setattr(healthcheck_runner, "check_supercell_api", ok)
    monkeypatch.setattr(healthcheck_runner, "check_model_artifact", ok)
    monkeypatch.setattr(healthcheck_runner, "check_scraper_sync_cards", ok)

    lines = []
    code = await healthcheck_runner.run_health_checks(include_pytest=False, printer=lines.append)

    assert code == 1
    assert any("[FAIL] database" in line for line in lines)


@pytest.mark.asyncio
async def test_run_health_checks_respects_skip_flags(monkeypatch):
    """Runner can execute with optional checks disabled."""

    async def ok(*args, **kwargs):
        return True, "ok"

    monkeypatch.setattr(healthcheck_runner, "check_database", ok)

    lines = []
    code = await healthcheck_runner.run_health_checks(
        include_api=False,
        include_db=True,
        include_supercell=False,
        include_model=False,
        include_scraper=False,
        include_pytest=False,
        printer=lines.append,
    )

    assert code == 0
    assert any("[PASS] database" in line for line in lines)
    assert not any("api" in line for line in lines)
