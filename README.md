# ⚔️ Clash Royale ML Deck Recommender

An AI-powered deck recommendation engine that uses Hybrid Machine Learning to suggest the perfect Clash Royale decks based on your unique card collection, trophy range, and playstyle.

![CR Decks Landing Page](C:/Users/lipey/.gemini/antigravity/brain/13a4af2b-0828-469c-91bb-9f877c36d733/landing_page_build_error_1774401281484.png)
*(Note: Visual representation of the landing page in development)*

## 🚀 The Vision
Most deck builders just show you what's "meta." Our recommender goes deeper—it analyzes your specific card levels and collection to ensure you aren't just playing a "good deck," but a deck that **you can actually win with** at your current progression.

## ✨ Current Features
- **AI-Driven Recommendations**: Hybrid model combining SVD Collaborative Filtering and Content-Based Synergy scoring.
- **Level Fit Analysis**: Algorithms that prioritize your high-level cards to avoid ladder mismatches.
- **Archetype Filtering**: Quick-select between Cycle, Beatdown, Bridge Spam, Control, and Bait.
- **Explainable AI**: Every recommendation comes with a detailed breakdown of *why* it works and how to play it.
- **Usage Tracking**: IP-based free tier (3 uses) with a built-in Stripe-ready paywall.
- **Automated Meta Updates**: Weekly data scraping from top 1000 ladder players and auto-retraining.

## 🛠️ Architecture
- **Frontend**: Next.js 16 (React 19) + Tailwind CSS v4 (Aesthetic Red-to-Blue Gradients).
- **Backend**: FastAPI (Python 3.12) + PostgreSQL 16.
- **ML Engine**: Scikit-Learn (SVD) + Custom Synergy Matrix compute.
- **BFF Pattern**: Next.js API routes acting as a secure proxy to the private FastAPI backend.

## 🧭 Roadmap (Future Features)
- [ ] **Mobile App**: Porting the UI to React Native for on-the-go deck building.
- [ ] **Challenge Filters**: Dedicated recommendation modes for Grand Challenges and Classic Challenges.
- [ ] **F2P Progression Engine**: A "Free-to-Play" filter that factors in gold/wildcard costs and future upgrade paths.
- [ ] **Granular Archetypes**: Breaking down high-level categories into more specific sub-types (e.g., Lavahound Beatdown vs. Golem Beatdown).
- [ ] **Advanced Analytics**: Deeper historical win-rate charts for recommended decks over multiple seasons.

## 🔧 Quick Start

### 1. Backend Setup
```bash
cd server
cp .env.example .env
# Set your CR_API_KEY and DATABASE_URL
docker-compose up -d db
pip install -r requirements.txt
python -m app.ml.trainer  # Initial data scrape and model train
uvicorn main:app --reload
```

### 2. Frontend Setup
```bash
cd client
cp .env.example .env.local
npm install
npm run dev
```

---

*Not affiliated with Supercell. Clash Royale is a trademark of Supercell Oy.*
