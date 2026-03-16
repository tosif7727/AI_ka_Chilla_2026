"""
tests/test_memory.py — Persistent memory: taste learning, Bayesian substitution rates.
"""

from __future__ import annotations

import json
import os
import tempfile
import pytest

from memory.persistent import PersistentMemory


@pytest.fixture
def tmp_memory():
    """PersistentMemory backed by a temp file."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tmp_path = f.name
    yield PersistentMemory(tmp_path)
    os.unlink(tmp_path)


class TestKitchenStaples:
    def test_increments_frequency(self, tmp_memory):
        ingredients = [
            {"name": "garlic", "quantity": "3 cloves"},
            {"name": "olive oil", "quantity": "2 tbsp"},
            {"name": "garlic", "quantity": "4 cloves"},
        ]
        tmp_memory.update_kitchen_staples(ingredients)
        assert tmp_memory._data["kitchen_staples"]["garlic"] == 2
        assert tmp_memory._data["kitchen_staples"]["olive oil"] == 1

    def test_top_staples_sorted(self, tmp_memory):
        for _ in range(5):
            tmp_memory.update_kitchen_staples([{"name": "salt"}])
        for _ in range(3):
            tmp_memory.update_kitchen_staples([{"name": "pepper"}])
        tmp_memory.update_kitchen_staples([{"name": "cumin"}])

        top = tmp_memory.get_top_staples(3)
        assert top[0][0] == "salt"
        assert top[0][1] == 5
        assert top[1][0] == "pepper"


class TestTastePreferences:
    def test_high_rating_boosts_tags(self, tmp_memory):
        tmp_memory.update_taste_preferences(
            boost_tags=["italian", "savory"],
            penalize_tags=[],
            rating=5,
            learning_rate=0.15,
        )
        prefs = tmp_memory._data["taste_preferences"]
        # High rating (5) → positive delta → above 0.5 baseline
        assert prefs.get("italian", 0.5) > 0.5
        assert prefs.get("savory", 0.5) > 0.5

    def test_low_rating_penalizes_tags(self, tmp_memory):
        tmp_memory.update_taste_preferences(
            boost_tags=["sweet"],
            penalize_tags=[],
            rating=1,
            learning_rate=0.15,
        )
        prefs = tmp_memory._data["taste_preferences"]
        # Low rating (1) → negative delta → below 0.5 baseline
        assert prefs.get("sweet", 0.5) < 0.5

    def test_preference_score_for_matching_tags(self, tmp_memory):
        # Seed preferences
        tmp_memory._data["taste_preferences"] = {
            "italian": 0.9,
            "savory": 0.8,
            "sweet": 0.2,
        }
        score_good = tmp_memory.get_preference_score(["italian", "savory"])
        score_bad = tmp_memory.get_preference_score(["sweet"])
        assert score_good > score_bad
        assert score_good > 0.8

    def test_multiple_sessions_converge(self, tmp_memory):
        """5 sessions with consistent high ratings should strongly boost tags."""
        for _ in range(5):
            tmp_memory.update_taste_preferences(
                boost_tags=["umami"], penalize_tags=[], rating=5
            )
        assert tmp_memory._data["taste_preferences"]["umami"] > 0.7


class TestSubstitutionRates:
    def test_bayesian_update_successful(self, tmp_memory):
        """Successful substitutions should push rate toward 1.0."""
        for _ in range(5):
            tmp_memory.update_substitution_rate("applesauce_for_egg", 0.9)

        rate = tmp_memory.get_substitution_rate("applesauce_for_egg")
        assert rate > 0.7

    def test_bayesian_update_failed(self, tmp_memory):
        """Failed substitutions should push rate toward 0."""
        for _ in range(5):
            tmp_memory.update_substitution_rate("water_for_butter", 0.1)

        rate = tmp_memory.get_substitution_rate("water_for_butter")
        assert rate < 0.4

    def test_unknown_key_returns_prior(self, tmp_memory):
        """Unknown substitution should return neutral prior (0.5)."""
        assert tmp_memory.get_substitution_rate("unknown_sub") == 0.5


class TestRecipeHistory:
    def test_add_and_retrieve(self, tmp_memory):
        rid = tmp_memory.add_recipe(
            name="Pasta Carbonara",
            flavor_tags=["italian", "creamy", "savory"],
            rating=5,
            would_make_again=True,
            notes="Perfect",
        )
        assert rid is not None
        assert len(tmp_memory._data["recipe_history"]) == 1

    def test_similar_recipes_ranked_by_preference(self, tmp_memory):
        """Similar recipes should be ranked by preference score."""
        tmp_memory._data["taste_preferences"] = {"italian": 0.9, "sweet": 0.2}

        tmp_memory.add_recipe("Pasta Bolognese", flavor_tags=["italian", "savory"])
        tmp_memory.add_recipe("Chocolate Cake", flavor_tags=["sweet", "baked"])
        tmp_memory.add_recipe("Risotto", flavor_tags=["italian", "creamy"])

        similar = tmp_memory.get_similar_recipes(["italian", "savory"], n=2)
        names = [s["name"] for s in similar]

        # Italian dishes should rank higher than sweet
        assert "Chocolate Cake" not in names or names.index("Chocolate Cake") == len(names) - 1

    def test_apply_feedback_update_atomic(self, tmp_memory):
        """apply_feedback_update should update all memory in one call."""
        rid = tmp_memory.apply_feedback_update(
            recipe_name="Stir Fry",
            flavor_tags=["asian", "savory", "spicy"],
            rating=4,
            would_make_again=True,
            notes="Great but a bit spicy",
            boost_tags=["asian", "savory"],
            penalize_tags=["spicy"],
            substitution_ratings={"soy_sauce_for_fish_sauce": 0.7},
            ingredients_used=[{"name": "tofu"}, {"name": "soy sauce"}],
            substitutions_used={"fish sauce": "soy sauce"},
        )

        # Recipe saved
        assert len(tmp_memory._data["recipe_history"]) == 1

        # Kitchen staples updated
        assert tmp_memory._data["kitchen_staples"].get("tofu", 0) > 0

        # Substitution rate updated
        assert "soy_sauce_for_fish_sauce" in tmp_memory._data["substitution_success_rate"]

        # Preferences updated
        assert "asian" in tmp_memory._data["taste_preferences"]

    def test_history_summary(self, tmp_memory):
        tmp_memory.add_recipe("Dish 1", [], rating=4)
        tmp_memory.add_recipe("Dish 2", [], rating=5)
        summary = tmp_memory.get_history_summary()
        assert "2 recipes" in summary
        assert "avg rating" in summary
