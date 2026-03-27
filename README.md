# Clash Royale ML Deck Recommender

Hybrid ML + FastAPI + Next.js application that recommends decks based on a player's owned cards, levels, and ladder context.

## What It Does
- Fetches player and card data from the Clash Royale API.
- Scrapes top-ladder deck data and computes card synergies.
- Uses a hybrid recommender to return deck suggestions with explanations.
- Serves recommendations through FastAPI with a Next.js frontend.

## Tech Stack
- Frontend: Next.js 16, React 19, Tailwind CSS v4
- Backend: FastAPI, SQLAlchemy async, PostgreSQL 16
- ML/Data: scikit-learn, pandas, numpy

## Quick Start

### 1. Start PostgreSQL + API (Docker)
```bash
docker compose up -d --build
```

### 2. Run frontend
```bash
cd client
pnpm install
pnpm dev
```

### 3. Backend local dev (optional, without Docker API)
```bash
cd server
# Configure server/.env with CR_API_KEY and DATABASE_URL
python -m pip install -r requirements.txt
python -m app.ml.trainer
uvicorn main:app --reload
```

## Testing

Run backend tests:
```bash
cd server
python -m pytest tests -v
```

## Deployment Health Checks

Deep deployment checks (DB, API, model, Supercell auth, scraper, optional smoke tests):
```bash
cd server
python scripts/deploy_healthcheck.py
python scripts/deploy_healthcheck.py --run-smoke-tests
```

Lightweight checks only (API + DB):
```bash
cd server
python scripts/deploy_healthcheck.py --skip-supercell --skip-scraper --skip-model
```

## Notes
- API container health is exposed through `/health` and Docker health checks.
- `server/tests` uses a dedicated test database (`clashroyale_test`) and auto-creates it if missing.

Not affiliated with Supercell. Clash Royale is a trademark of Supercell Oy.
