"""Run deployment health checks for ClashRoyaleDecks server."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_ROOT = os.path.dirname(SCRIPT_DIR)
if SERVER_ROOT not in sys.path:
    sys.path.insert(0, SERVER_ROOT)

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.healthcheck_runner import run_health_checks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deployment health checks")
    parser.add_argument("--api-base-url", default="http://127.0.0.1:8000", help="API base URL for /health check")
    parser.add_argument("--skip-api", action="store_true", help="Skip API /health check")
    parser.add_argument("--skip-db", action="store_true", help="Skip database connectivity check")
    parser.add_argument("--skip-supercell", action="store_true", help="Skip Supercell API auth check")
    parser.add_argument("--skip-model", action="store_true", help="Skip model artifact check")
    parser.add_argument("--skip-scraper", action="store_true", help="Skip scraper sync cards check")
    parser.add_argument("--run-smoke-tests", action="store_true", help="Run smoke pytest subset")
    return parser.parse_args()


async def _main() -> int:
    args = parse_args()
    return await run_health_checks(
        include_api=not args.skip_api,
        include_db=not args.skip_db,
        include_supercell=not args.skip_supercell,
        include_model=not args.skip_model,
        include_scraper=not args.skip_scraper,
        include_pytest=args.run_smoke_tests,
        api_base_url=args.api_base_url,
    )


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
