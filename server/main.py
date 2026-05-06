from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import close_db, init_db
from app.data.scheduler import start_scheduler, stop_scheduler
from app.routers import auth, decks, players, predict, usage


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle events."""
    # Startup
    await init_db()
    start_scheduler()

    # Try to load pre-trained model
    from app.ml.model import recommender
    recommender.load()

    yield

    # Shutdown
    stop_scheduler()
    await close_db()


app = FastAPI(
    title="Clash Royale Decks API",
    description="API for Clash Royale deck recommendations using ML",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Clash Royale Decks API", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Include routers
app.include_router(decks.router, prefix="/api/decks", tags=["decks"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(predict.router, prefix="/api/predict", tags=["predictions"])
app.include_router(players.router, prefix="/api/players", tags=["players"])
app.include_router(usage.router, prefix="/api/usage", tags=["usage"])
