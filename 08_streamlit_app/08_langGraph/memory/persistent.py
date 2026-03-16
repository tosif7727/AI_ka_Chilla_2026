"""
memory/persistent.py — Long-term memory: taste profiles, recipe history, substitution learning.

Short-term memory: LangGraph's built-in MemorySaver / SqliteSaver (handles graph checkpoints).
Long-term memory: This module (JSON file or can swap to SQL/vector store).
"""

from __future__ import annotations

import json
import math
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from state import RecipeHistoryEntry


class PersistentMemory:
    """
    Manages long-term user memory across LangGraph sessions.

    Storage layout (JSON):
    {
      "kitchen_staples": {"eggs": 12, "garlic": 8, ...},     # frequency counter
      "taste_preferences": {"umami": 0.8, "spicy": 0.3, ...}, # weighted 0-1
      "substitution_success_rate": {"flax_for_egg": 0.75, ...}, # bayesian
      "recipe_history": [RecipeHistoryEntry, ...]
    }
    """

    def __init__(self, filepath: str = "recipe_memory.json"):
        self.filepath = Path(filepath)
        self._data = self._load()

    # ─────────────────────────────────────────────
    # Load / Save
    # ─────────────────────────────────────────────

    def _load(self) -> dict:
        if self.filepath.exists():
            with open(self.filepath) as f:
                return json.load(f)
        return {
            "kitchen_staples": {},
            "taste_preferences": {},
            "substitution_success_rate": {},
            "recipe_history": [],
        }

    def save(self) -> None:
        with open(self.filepath, "w") as f:
            json.dump(self._data, f, indent=2, default=str)

    def as_dict(self) -> dict:
        """Return a copy suitable for embedding in LangGraph state."""
        return dict(self._data)

    # ─────────────────────────────────────────────
    # Kitchen staples — frequency tracking
    # ─────────────────────────────────────────────

    def update_kitchen_staples(self, ingredients: list[dict]) -> None:
        """Increment frequency for each ingredient used in a session."""
        staples = self._data["kitchen_staples"]
        for ing in ingredients:
            name = ing["name"].lower().strip()
            staples[name] = staples.get(name, 0) + 1
        self.save()

    def get_top_staples(self, n: int = 10) -> list[tuple[str, int]]:
        staples = self._data["kitchen_staples"]
        return sorted(staples.items(), key=lambda x: x[1], reverse=True)[:n]

    # ─────────────────────────────────────────────
    # Taste preferences — weighted tag system
    # ─────────────────────────────────────────────

    def update_taste_preferences(
        self,
        boost_tags: list[str],
        penalize_tags: list[str],
        rating: int,
        learning_rate: float = 0.15,
    ) -> None:
        """
        Weighted update of taste preference tags.
        Rating 5 → full learning_rate boost
        Rating 1 → full learning_rate penalty
        """
        prefs = self._data["taste_preferences"]
        normalized_rating = (rating - 3) / 2  # -1 to +1

        for tag in boost_tags:
            tag = tag.lower().strip()
            current = prefs.get(tag, 0.5)
            delta = learning_rate * normalized_rating
            prefs[tag] = max(0.0, min(1.0, current + delta))

        for tag in penalize_tags:
            tag = tag.lower().strip()
            current = prefs.get(tag, 0.5)
            prefs[tag] = max(0.0, min(1.0, current - learning_rate * 0.5))

        self.save()

    def get_preference_score(self, tags: list[str]) -> float:
        """
        Cosine-like similarity: average preference score for a set of tags.
        Returns 0.0–1.0. Used for recipe recommendation scoring.
        """
        prefs = self._data["taste_preferences"]
        if not tags:
            return 0.5
        scores = [prefs.get(tag.lower(), 0.5) for tag in tags]
        return sum(scores) / len(scores)

    def get_similar_recipes(self, tags: list[str], n: int = 3) -> list[dict]:
        """Return top-n past recipes ranked by tag similarity."""
        history = self._data["recipe_history"]
        scored = []
        for entry in history:
            score = self.get_preference_score(entry.get("flavor_tags", []))
            scored.append((score, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:n]]

    # ─────────────────────────────────────────────
    # Substitution success rate — Bayesian update
    # ─────────────────────────────────────────────

    def update_substitution_rate(
        self, substitution_key: str, success_rating: float
    ) -> None:
        """
        Bayesian update for substitution success rate.
        substitution_key format: "original_for_substitute" e.g. "flax_for_egg"
        success_rating: 0.0–1.0
        """
        rates = self._data["substitution_success_rate"]
        # Prior: 0.5 with weight 2 (weak prior)
        prior_successes = rates.get(f"{substitution_key}_successes", 1.0)
        prior_trials = rates.get(f"{substitution_key}_trials", 2.0)

        new_successes = prior_successes + success_rating
        new_trials = prior_trials + 1.0

        rates[f"{substitution_key}_successes"] = new_successes
        rates[f"{substitution_key}_trials"] = new_trials
        rates[substitution_key] = new_successes / new_trials  # posterior mean
        self.save()

    def get_substitution_rate(self, substitution_key: str) -> float:
        """Return estimated success rate for a substitution (default 0.5)."""
        return self._data["substitution_success_rate"].get(substitution_key, 0.5)

    # ─────────────────────────────────────────────
    # Recipe history
    # ─────────────────────────────────────────────

    def add_recipe(
        self,
        name: str,
        flavor_tags: list[str],
        substitutions_used: dict[str, str] | None = None,
        rating: int | None = None,
        would_make_again: bool | None = None,
        notes: str | None = None,
    ) -> str:
        """Add a recipe to history. Returns the recipe_id."""
        recipe_id = str(uuid.uuid4())[:8]
        entry = {
            "recipe_id": recipe_id,
            "name": name,
            "rating": rating,
            "would_make_again": would_make_again,
            "timestamp": datetime.now().isoformat(),
            "notes": notes,
            "flavor_tags": flavor_tags,
            "substitutions_used": substitutions_used or {},
        }
        self._data["recipe_history"].append(entry)
        self.save()
        return recipe_id

    def update_recipe_feedback(
        self,
        recipe_id: str,
        rating: int,
        would_make_again: bool,
        notes: str,
    ) -> None:
        for entry in self._data["recipe_history"]:
            if entry["recipe_id"] == recipe_id:
                entry["rating"] = rating
                entry["would_make_again"] = would_make_again
                entry["notes"] = notes
                break
        self.save()

    def get_history_summary(self) -> str:
        history = self._data["recipe_history"]
        if not history:
            return "No recipe history yet."
        rated = [e for e in history if e.get("rating")]
        avg = sum(e["rating"] for e in rated) / len(rated) if rated else 0
        return (
            f"{len(history)} recipes cooked | "
            f"{len(rated)} rated | "
            f"avg rating: {avg:.1f}/5"
        )

    # ─────────────────────────────────────────────
    # Bulk update from state (called at FEEDBACK_COLLECTOR node)
    # ─────────────────────────────────────────────

    def apply_feedback_update(
        self,
        recipe_name: str,
        flavor_tags: list[str],
        rating: int,
        would_make_again: bool,
        notes: str,
        boost_tags: list[str],
        penalize_tags: list[str],
        substitution_ratings: dict[str, float],
        ingredients_used: list[dict],
        substitutions_used: dict[str, str],
    ) -> str:
        """Single atomic update call from FEEDBACK_COLLECTOR node."""
        # 1. Save recipe
        recipe_id = self.add_recipe(
            name=recipe_name,
            flavor_tags=flavor_tags,
            substitutions_used=substitutions_used,
            rating=rating,
            would_make_again=would_make_again,
            notes=notes,
        )
        # 2. Update taste preferences
        self.update_taste_preferences(boost_tags, penalize_tags, rating)

        # 3. Update kitchen staples
        self.update_kitchen_staples(ingredients_used)

        # 4. Update substitution rates
        for sub_key, rate in substitution_ratings.items():
            self.update_substitution_rate(sub_key, rate)

        return recipe_id
