"""
Hybrid deck recommendation engine for Clash Royale.

Combines three signals:
1. Collaborative Filtering (SVD) — "players like you win with these decks"
2. Content-Based Filtering — card synergy scores + archetype matching
3. Card Level Fit — can the player actually play this deck at their trophy range?

Final score = w1×CF + w2×CB + w3×LevelFit + w4×WinRate
"""

import logging
import os
import pickle
from itertools import combinations
from typing import Optional

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

logger = logging.getLogger(__name__)

# Default hybrid weights
DEFAULT_WEIGHTS = {
    "cf": 0.25,       # Collaborative filtering
    "cb": 0.25,       # Content-based (synergy)
    "level_fit": 0.30, # Card level readiness
    "win_rate": 0.20,  # Historical win rate
}

MODEL_DIR = os.path.join(os.path.dirname(__file__), "artifacts")


class DeckRecommender:
    """
    Hybrid ML model for Clash Royale deck recommendations.

    Usage:
        model = DeckRecommender()
        model.load_or_train(meta_decks, synergies)
        results = model.recommend(player_card_levels, archetype_pref, top_k=3)
    """

    def __init__(self, weights: Optional[dict[str, float]] = None):
        self.weights = weights or DEFAULT_WEIGHTS

        # SVD model for collaborative filtering
        self.svd = TruncatedSVD(n_components=50, random_state=42)
        self.is_trained = False

        # Data loaded from DB
        self.meta_decks: list[dict] = []        # All meta decks
        self.synergy_map: dict[tuple, float] = {} # (card_a, card_b) -> score
        self.all_card_keys: list[str] = []       # Ordered list of all card keys
        self.card_to_idx: dict[str, int] = {}    # Card key -> matrix index

        # SVD matrices (populated after training)
        self.deck_vectors: Optional[np.ndarray] = None  # meta_decks projected into latent space

    def load_data(
        self,
        meta_decks: list[dict],
        synergies: list[dict],
        all_card_keys: list[str],
    ):
        """
        Load data from the database into the model.

        Args:
            meta_decks: List of dicts with keys: card_keys, win_rate, archetype, etc.
            synergies: List of dicts with keys: card_a_key, card_b_key, synergy_score
            all_card_keys: Ordered list of all card keys in the game
        """
        self.meta_decks = meta_decks
        self.all_card_keys = all_card_keys
        self.card_to_idx = {key: i for i, key in enumerate(all_card_keys)}

        # Build synergy lookup
        self.synergy_map = {}
        for s in synergies:
            pair = tuple(sorted([s["card_a_key"], s["card_b_key"]]))
            self.synergy_map[pair] = s["synergy_score"]

    def train(self):
        """
        Train the collaborative filtering component.

        Builds a deck-card binary matrix and applies SVD to find latent deck embeddings.
        """
        if not self.meta_decks or not self.all_card_keys:
            logger.warning("No data loaded — cannot train model")
            return

        num_decks = len(self.meta_decks)
        num_cards = len(self.all_card_keys)

        # Build deck-card matrix (rows=decks, cols=cards)
        # Value = 1 if card is in deck, weighted by deck win rate
        deck_card_matrix = np.zeros((num_decks, num_cards))

        for i, deck in enumerate(self.meta_decks):
            wr_weight = 0.5 + deck.get("win_rate", 0.5)  # Weight by win rate (range ~1.0-1.5)
            for card_key in deck.get("card_keys", []):
                idx = self.card_to_idx.get(card_key)
                if idx is not None:
                    deck_card_matrix[i, idx] = wr_weight

        # Apply SVD
        n_components = min(50, num_decks - 1, num_cards - 1)
        if n_components < 2:
            logger.warning(f"Too few decks/cards for SVD (decks={num_decks}, cards={num_cards})")
            self.deck_vectors = deck_card_matrix  # Fallback to raw matrix
        else:
            self.svd = TruncatedSVD(n_components=n_components, random_state=42)
            self.deck_vectors = self.svd.fit_transform(deck_card_matrix)

        self.is_trained = True
        logger.info(f"Model trained on {num_decks} decks × {num_cards} cards (latent dims={n_components})")

    def _score_cf(self, player_card_levels: dict[str, int]) -> np.ndarray:
        """
        Collaborative Filtering score for each meta deck.

        Projects the player's card levels into the SVD latent space
        and computes cosine similarity with each deck embedding.
        """
        if self.deck_vectors is None or not self.is_trained:
            return np.zeros(len(self.meta_decks))

        # Build player vector (card present = level/14, absent = 0)
        player_vec = np.zeros((1, len(self.all_card_keys)))
        for card_key, level in player_card_levels.items():
            idx = self.card_to_idx.get(card_key)
            if idx is not None:
                player_vec[0, idx] = level / 14.0  # Normalize by max level

        # Project into latent space
        if hasattr(self.svd, 'components_'):
            player_latent = player_vec @ self.svd.components_.T
        else:
            player_latent = player_vec[:, :self.deck_vectors.shape[1]]

        # Cosine similarity with each deck
        similarities = cosine_similarity(player_latent, self.deck_vectors).flatten()
        return similarities

    def _score_cb(self, archetype_pref: Optional[str] = None) -> np.ndarray:
        """
        Content-Based score for each meta deck.

        Computes the average pairwise synergy within each deck,
        with a bonus for archetype match.
        """
        scores = np.zeros(len(self.meta_decks))

        for i, deck in enumerate(self.meta_decks):
            card_keys = deck.get("card_keys", [])

            # Average pairwise synergy
            pair_scores = []
            for a, b in combinations(sorted(card_keys), 2):
                pair = (a, b)
                syn = self.synergy_map.get(pair, 0.0)
                pair_scores.append(syn)

            avg_synergy = np.mean(pair_scores) if pair_scores else 0.0

            # Archetype bonus
            archetype_bonus = 0.0
            if archetype_pref and deck.get("archetype") == archetype_pref:
                archetype_bonus = 0.15

            scores[i] = avg_synergy + archetype_bonus

        return scores

    def _score_level_fit(self, player_card_levels: dict[str, int]) -> np.ndarray:
        """
        Card Level Fit score for each meta deck.

        Computes avg(player_level / max_level) for the 8 cards,
        with a heavy penalty if any card is underleveled by ≥3.
        """
        scores = np.zeros(len(self.meta_decks))

        for i, deck in enumerate(self.meta_decks):
            card_keys = deck.get("card_keys", [])
            level_ratios = []
            penalty = 0.0

            for card_key in card_keys:
                player_level = player_card_levels.get(card_key, 0)
                if player_level == 0:
                    # Player doesn't own this card
                    level_ratios.append(0.0)
                    penalty += 0.15  # Significant penalty
                else:
                    ratio = player_level / 14.0
                    level_ratios.append(ratio)
                    if player_level <= 11:  # Underleveled by ≥3
                        penalty += 0.05

            avg_ratio = np.mean(level_ratios) if level_ratios else 0.0
            scores[i] = max(0.0, avg_ratio - penalty)

        return scores

    def _score_win_rate(self) -> np.ndarray:
        """Win rate score — directly from the meta deck data."""
        return np.array([d.get("win_rate", 0.5) for d in self.meta_decks])

    def recommend(
        self,
        player_card_levels: dict[str, int],
        archetype_pref: Optional[str] = None,
        required_cards: Optional[list[str]] = None,
        top_k: int = 3,
    ) -> list[dict]:
        """
        Generate top-K deck recommendations.

        Args:
            player_card_levels: Dict mapping card key → player's level for that card
            archetype_pref: Optional archetype preference (cycle, beatdown, etc.)
            required_cards: Optional card keys that every returned deck must include
            top_k: Number of recommendations to return

        Returns:
            List of dicts with deck info + scores + explanation data
        """
        if not self.meta_decks:
            return []

        # Compute all four score components
        cf_scores = self._score_cf(player_card_levels)
        cb_scores = self._score_cb(archetype_pref)
        level_scores = self._score_level_fit(player_card_levels)
        wr_scores = self._score_win_rate()

        # Normalize each to [0, 1]
        def safe_normalize(arr: np.ndarray) -> np.ndarray:
            max_val = arr.max()
            min_val = arr.min()
            if max_val == min_val:
                return np.ones_like(arr) * 0.5
            return (arr - min_val) / (max_val - min_val)

        cf_norm = safe_normalize(cf_scores)
        cb_norm = safe_normalize(cb_scores)
        level_norm = safe_normalize(level_scores)
        wr_norm = safe_normalize(wr_scores)

        # Weighted hybrid score
        w = self.weights
        final_scores = (
            w["cf"] * cf_norm +
            w["cb"] * cb_norm +
            w["level_fit"] * level_norm +
            w["win_rate"] * wr_norm
        )

        required_set = {card for card in (required_cards or []) if card}
        candidate_indices = np.arange(len(self.meta_decks))
        if required_set:
            candidate_indices = np.array([
                idx for idx, deck in enumerate(self.meta_decks)
                if required_set.issubset(set(deck.get("card_keys", [])))
            ])

        if candidate_indices.size == 0:
            return []

        # Get top K indices
        ranked_candidates = candidate_indices[np.argsort(final_scores[candidate_indices])[::-1]]
        top_indices = ranked_candidates[:top_k]

        results = []
        for idx in top_indices:
            deck = self.meta_decks[idx]
            results.append({
                "deck": deck,
                "scores": {
                    "overall": round(float(final_scores[idx]), 4),
                    "cf": round(float(cf_norm[idx]), 4),
                    "cb": round(float(cb_norm[idx]), 4),
                    "level_fit": round(float(level_norm[idx]), 4),
                    "win_rate": round(float(wr_norm[idx]), 4),
                },
                "raw_scores": {
                    "cf": round(float(cf_scores[idx]), 4),
                    "cb": round(float(cb_scores[idx]), 4),
                    "level_fit": round(float(level_scores[idx]), 4),
                    "win_rate": round(float(wr_scores[idx]), 4),
                },
            })

        return results

    def save(self, path: Optional[str] = None):
        """Serialize model to disk."""
        os.makedirs(MODEL_DIR, exist_ok=True)
        save_path = path or os.path.join(MODEL_DIR, "deck_recommender.pkl")

        model_data = {
            "weights": self.weights,
            "meta_decks": self.meta_decks,
            "synergy_map": self.synergy_map,
            "all_card_keys": self.all_card_keys,
            "card_to_idx": self.card_to_idx,
            "deck_vectors": self.deck_vectors,
            "svd": self.svd if self.is_trained else None,
            "is_trained": self.is_trained,
        }

        with open(save_path, "wb") as f:
            pickle.dump(model_data, f)
        logger.info(f"Model saved to {save_path}")

    def load(self, path: Optional[str] = None) -> bool:
        """Load model from disk. Returns True if successful."""
        load_path = path or os.path.join(MODEL_DIR, "deck_recommender.pkl")

        if not os.path.exists(load_path):
            logger.warning(f"No model file at {load_path}")
            return False

        try:
            with open(load_path, "rb") as f:
                model_data = pickle.load(f)

            self.weights = model_data["weights"]
            self.meta_decks = model_data["meta_decks"]
            self.synergy_map = model_data["synergy_map"]
            self.all_card_keys = model_data["all_card_keys"]
            self.card_to_idx = model_data["card_to_idx"]
            self.deck_vectors = model_data["deck_vectors"]
            if model_data.get("svd"):
                self.svd = model_data["svd"]
            self.is_trained = model_data["is_trained"]

            logger.info(f"Model loaded from {load_path} ({len(self.meta_decks)} decks)")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False


# Singleton instance
recommender = DeckRecommender()
