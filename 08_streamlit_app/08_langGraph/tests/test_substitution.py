"""
tests/test_substitution.py — Substitution negotiation tests.
tests/test_constraint_rescue.py — Constraint rescue path tests.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import HumanMessage

from state import make_initial_state, GeneratedSubstitutions, SubstitutionPair, SubstitutionOption


# ─────────────────────────────────────────────
# Substitution tests
# ─────────────────────────────────────────────

@pytest.fixture
def state_with_missing():
    state = make_initial_state()
    state["current_session"] = {
        "available_ingredients": [
            {"name": "flour", "quantity": "2 cups", "category": "dry_goods"},
            {"name": "sugar", "quantity": "1 cup", "category": "dry_goods"},
            {"name": "oil", "quantity": "1/2 cup", "category": "fats"},
            {"name": "applesauce", "quantity": "1/2 cup", "category": "produce"},
        ],
        "time_limit": 45,
        "equipment_available": ["oven"],
    }
    state["recipe_candidate"] = {
        "name": "Simple Cake",
        "required_ingredients": [
            {"name": "flour", "quantity": "2 cups", "available": True},
            {"name": "sugar", "quantity": "1 cup", "available": True},
            {"name": "eggs", "quantity": "2", "available": False, "importance": "critical"},
            {"name": "butter", "quantity": "1/2 cup", "available": False, "importance": "critical"},
        ],
        "missing_ingredients": [
            {"name": "eggs", "quantity": "2", "importance": "critical"},
            {"name": "butter", "quantity": "1/2 cup", "importance": "critical"},
        ],
        "substitutions": {},
        "instructions": [],
        "confidence_score": 0.6,
        "flavor_profile_tags": ["sweet", "baked"],
        "total_time": 45,
        "difficulty": "beginner",
        "chef_notes": "",
    }
    state["flags"] = {
        "impossible_constraints": False,
        "needs_substitution": True,
        "needs_clarification": False,
        "api_unavailable": False,
    }
    return state


class TestSubstitutionNegotiator:
    def test_generates_substitution_options(self, state_with_missing):
        """Should generate options for each missing ingredient."""
        from nodes.substitution import substitution_negotiator_node

        mock_subs = GeneratedSubstitutions(
            substitutions={
                "eggs": SubstitutionPair(
                    purpose="binding and moisture",
                    option_a=SubstitutionOption(
                        ingredient="flax egg",
                        ratio="1 tbsp ground flax + 3 tbsp water per egg",
                        trade_offs="Slightly denser texture, nutty flavor",
                        available=False,
                    ),
                    option_b=SubstitutionOption(
                        ingredient="applesauce",
                        ratio="1/4 cup per egg",
                        trade_offs="Adds sweetness, very moist result",
                        available=True,
                    ),
                ),
                "butter": SubstitutionPair(
                    purpose="fat and flavor",
                    option_a=SubstitutionOption(
                        ingredient="oil",
                        ratio="3/4 cup per cup of butter",
                        trade_offs="Less rich flavor, good texture",
                        available=True,
                    ),
                    option_b=SubstitutionOption(
                        ingredient="applesauce",
                        ratio="1:1",
                        trade_offs="Much lower fat, very moist, less rich",
                        available=True,
                    ),
                ),
            }
        )

        with patch("nodes.substitution.ChatOpenAI") as mock_llm_cls, \
             patch("nodes.substitution.interrupt") as mock_interrupt:
            mock_instance = MagicMock()
            mock_instance.with_structured_output.return_value.invoke.return_value = mock_subs
            mock_llm_cls.return_value = mock_instance

            # Simulate user accepting all substitutions
            mock_interrupt.return_value = {"choice": "accept_all"}

            result = substitution_negotiator_node(state_with_missing)

        # Command should route to present_recipe
        assert result.goto == "present_recipe"
        updated = result.update
        assert "eggs" in updated["recipe_candidate"]["substitutions"]
        assert "butter" in updated["recipe_candidate"]["substitutions"]
        assert updated["recipe_candidate"]["substitutions"]["eggs"] == "flax egg"
        assert updated["flags"]["needs_substitution"] is False

    def test_reject_routes_to_generator(self, state_with_missing):
        """Rejecting subs should route back to recipe generator."""
        from nodes.substitution import substitution_negotiator_node

        mock_subs = GeneratedSubstitutions(substitutions={
            "eggs": SubstitutionPair(
                purpose="binding",
                option_a=SubstitutionOption(ingredient="flax egg", ratio="1:1", trade_offs="", available=False),
                option_b=SubstitutionOption(ingredient="applesauce", ratio="1:1", trade_offs="", available=True),
            )
        })

        with patch("nodes.substitution.ChatOpenAI") as mock_llm_cls, \
             patch("nodes.substitution.interrupt") as mock_interrupt:
            mock_instance = MagicMock()
            mock_instance.with_structured_output.return_value.invoke.return_value = mock_subs
            mock_llm_cls.return_value = mock_instance
            mock_interrupt.return_value = {"choice": "reject_all"}

            result = substitution_negotiator_node(state_with_missing)

        assert result.goto == "recipe_generator"
        assert result.update["user_feedback"] == "REJECT"

    def test_custom_substitution_choice(self, state_with_missing):
        """Custom choice should use user-specified substitutes."""
        from nodes.substitution import substitution_negotiator_node

        mock_subs = GeneratedSubstitutions(substitutions={
            "eggs": SubstitutionPair(
                purpose="binding",
                option_a=SubstitutionOption(ingredient="flax egg", ratio="1:1", trade_offs="", available=False),
                option_b=SubstitutionOption(ingredient="applesauce", ratio="1/4 cup", trade_offs="", available=True),
            )
        })

        with patch("nodes.substitution.ChatOpenAI") as mock_llm_cls, \
             patch("nodes.substitution.interrupt") as mock_interrupt:
            mock_instance = MagicMock()
            mock_instance.with_structured_output.return_value.invoke.return_value = mock_subs
            mock_llm_cls.return_value = mock_instance
            # Choose custom with option_b for eggs
            mock_interrupt.return_value = {
                "choice": "custom",
                "accepted_substitutions": {"eggs": "applesauce"},
            }

            result = substitution_negotiator_node(state_with_missing)

        assert result.goto == "present_recipe"
        assert result.update["recipe_candidate"]["substitutions"]["eggs"] == "applesauce"


# ─────────────────────────────────────────────
# Constraint rescue tests
# ─────────────────────────────────────────────

@pytest.fixture
def impossible_state():
    state = make_initial_state()
    state["current_session"] = {
        "available_ingredients": [
            {"name": "rice", "quantity": "1 cup", "category": "dry_goods"},
        ],
        "time_limit": 5,  # Only 5 minutes — very tight
        "equipment_available": ["microwave"],
    }
    state["recipe_candidate"] = {
        "name": "", "required_ingredients": [], "missing_ingredients": [],
        "substitutions": {}, "instructions": [], "confidence_score": 0.1,
        "flavor_profile_tags": [], "total_time": 0, "difficulty": "beginner",
        "chef_notes": "",
    }
    state["flags"] = {
        "impossible_constraints": True,
        "needs_substitution": False,
        "needs_clarification": False,
        "api_unavailable": False,
    }
    state["iteration_count"] = 2
    return state


class TestConstraintRescue:
    def test_presents_rescue_options(self, impossible_state):
        """Should generate 3 rescue paths and interrupt."""
        from nodes.constraint_rescue import constraint_rescue_node
        from state import RescueDiagnosis, RescuePathOption, RescuePath

        mock_diagnosis = RescueDiagnosis(
            diagnosis="With only rice and 5 minutes, we can't make a full meal.",
            bottleneck="Insufficient ingredients and time",
            rescue_paths=[
                RescuePathOption(
                    id=RescuePath.ADD_INGREDIENTS,
                    title="Quick store run",
                    description="Grab eggs and soy sauce to make fried rice",
                    additions=["eggs", "soy sauce", "frozen peas"],
                ),
                RescuePathOption(
                    id=RescuePath.SIMPLE_MEAL,
                    title="Plain rice",
                    description="Cook the rice with some salt — simple but filling",
                    recipe_hint="Microwave rice with water",
                ),
                RescuePathOption(
                    id=RescuePath.REPLAN,
                    title="Start fresh",
                    description="Tell me what else you have and we'll start over",
                ),
            ],
        )

        with patch("nodes.constraint_rescue.ChatOpenAI") as mock_llm_cls, \
             patch("nodes.constraint_rescue.interrupt") as mock_interrupt:
            mock_instance = MagicMock()
            mock_instance.with_structured_output.return_value.invoke.return_value = mock_diagnosis
            mock_llm_cls.return_value = mock_instance
            mock_interrupt.return_value = {"path": "simple_meal"}

            result = constraint_rescue_node(impossible_state)

        assert result.goto == "recipe_generator"
        assert result.update["current_session"]["time_limit"] == 15  # reset for simple meal

    def test_replan_clears_session(self, impossible_state):
        """Choosing replan should clear current_session and route to intake_parser."""
        from nodes.constraint_rescue import constraint_rescue_node
        from state import RescueDiagnosis, RescuePathOption, RescuePath

        mock_diagnosis = RescueDiagnosis(
            diagnosis="Not enough ingredients.",
            bottleneck="Only 1 ingredient",
            rescue_paths=[
                RescuePathOption(id=RescuePath.ADD_INGREDIENTS, title="Shop", description="Buy more"),
                RescuePathOption(id=RescuePath.SIMPLE_MEAL, title="Simple", description="Keep it simple"),
                RescuePathOption(id=RescuePath.REPLAN, title="Restart", description="Start over"),
            ],
        )

        with patch("nodes.constraint_rescue.ChatOpenAI") as mock_llm_cls, \
             patch("nodes.constraint_rescue.interrupt") as mock_interrupt:
            mock_instance = MagicMock()
            mock_instance.with_structured_output.return_value.invoke.return_value = mock_diagnosis
            mock_llm_cls.return_value = mock_instance
            mock_interrupt.return_value = {"path": "replan"}

            result = constraint_rescue_node(impossible_state)

        assert result.goto == "intake_parser"
        assert result.update["current_session"]["available_ingredients"] == []
        assert result.update["iteration_count"] == 0

    def test_add_ingredients_resets_iteration(self, impossible_state):
        """Choosing add_ingredients should reset iteration_count for fresh attempt."""
        from nodes.constraint_rescue import constraint_rescue_node
        from state import RescueDiagnosis, RescuePathOption, RescuePath

        mock_diagnosis = RescueDiagnosis(
            diagnosis="Need more ingredients.",
            bottleneck="Only rice",
            rescue_paths=[
                RescuePathOption(
                    id=RescuePath.ADD_INGREDIENTS,
                    title="Add items",
                    description="Grab eggs",
                    additions=["eggs", "butter"],
                ),
                RescuePathOption(id=RescuePath.SIMPLE_MEAL, title="Simple", description="Simple"),
                RescuePathOption(id=RescuePath.REPLAN, title="Restart", description="Restart"),
            ],
        )

        with patch("nodes.constraint_rescue.ChatOpenAI") as mock_llm_cls, \
             patch("nodes.constraint_rescue.interrupt") as mock_interrupt:
            mock_instance = MagicMock()
            mock_instance.with_structured_output.return_value.invoke.return_value = mock_diagnosis
            mock_llm_cls.return_value = mock_instance
            mock_interrupt.return_value = {"path": "add_ingredients"}

            result = constraint_rescue_node(impossible_state)

        assert result.goto == "recipe_generator"
        assert result.update["iteration_count"] == 0
        assert result.update["flags"]["impossible_constraints"] is False
        # Hypothetical ingredients should be added
        new_ingredients = result.update["current_session"]["available_ingredients"]
        assert len(new_ingredients) > 1
