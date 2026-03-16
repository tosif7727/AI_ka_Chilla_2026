"""
tests/test_happy_path.py — Happy path: confidence≥0.7, all ingredients available.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage

from state import make_initial_state, GeneratedRecipe, RecipeIngredient, InstructionStep


# ─────────────────────────────────────────────
# Shared fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def base_state():
    state = make_initial_state()
    state["current_session"] = {
        "available_ingredients": [
            {"name": "chicken breast", "quantity": "2", "category": "protein"},
            {"name": "garlic", "quantity": "4 cloves", "category": "produce"},
            {"name": "pasta", "quantity": "200g", "category": "dry_goods"},
            {"name": "olive oil", "quantity": "3 tbsp", "category": "fats"},
            {"name": "salt", "quantity": "to taste", "category": "spice"},
            {"name": "pepper", "quantity": "to taste", "category": "spice"},
        ],
        "time_limit": 30,
        "equipment_available": ["stovetop", "oven"],
    }
    return state


@pytest.fixture
def mock_high_confidence_recipe():
    return GeneratedRecipe(
        name="Garlic Chicken Pasta",
        required_ingredients=[
            RecipeIngredient(name="chicken breast", quantity="2", available=True),
            RecipeIngredient(name="garlic", quantity="4 cloves", available=True),
            RecipeIngredient(name="pasta", quantity="200g", available=True),
            RecipeIngredient(name="olive oil", quantity="3 tbsp", available=True),
        ],
        missing_ingredients=[],
        instructions=[
            InstructionStep(step=1, text="Boil pasta in salted water", time_minutes=10),
            InstructionStep(step=2, text="Sauté garlic in olive oil until golden", time_minutes=3),
            InstructionStep(step=3, text="Add chicken and cook through", time_minutes=12),
            InstructionStep(step=4, text="Toss pasta with chicken and garlic oil", time_minutes=2),
        ],
        confidence_score=0.85,
        flavor_profile_tags=["savory", "italian", "garlic"],
        total_time=27,
        difficulty="beginner",
        needs_substitution=False,
        impossible_constraints=False,
        chef_notes="The secret is not to burn the garlic — low heat is key.",
    )


# ─────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────

class TestIntakeParser:
    def test_parses_basic_ingredients(self, base_state):
        """Intake parser should extract named ingredients with quantities."""
        from nodes.intake_parser import intake_parser_node

        base_state["messages"] = [HumanMessage(
            content="I have 2 chicken breasts, garlic, pasta, and olive oil. 30 minutes."
        )]

        with patch("nodes.intake_parser.ChatOpenAI") as mock_llm_cls:
            from state import ParsedIngredients, Ingredient
            mock_result = ParsedIngredients(
                available_ingredients=[
                    Ingredient(name="chicken breast", quantity="2", category="protein"),
                    Ingredient(name="garlic", quantity="4 cloves", category="produce"),
                    Ingredient(name="pasta", quantity="200g", category="dry_goods"),
                    Ingredient(name="olive oil", quantity="3 tbsp", category="fats"),
                ],
                time_limit=30,
                equipment_available=["stovetop"],
                needs_clarification=False,
            )
            mock_instance = MagicMock()
            mock_instance.with_structured_output.return_value.invoke.return_value = mock_result
            mock_llm_cls.return_value = mock_instance

            result = intake_parser_node(base_state)

        assert "current_session" in result
        assert len(result["current_session"]["available_ingredients"]) == 4
        assert result["current_session"]["time_limit"] == 30
        assert result["flags"]["needs_clarification"] is False

    def test_flags_clarification_for_ambiguous_input(self, base_state):
        """Vague input should trigger clarification."""
        from nodes.intake_parser import intake_parser_node

        base_state["messages"] = [HumanMessage(content="I have some stuff")]

        with patch("nodes.intake_parser.ChatOpenAI") as mock_llm_cls:
            from state import ParsedIngredients
            mock_result = ParsedIngredients(
                available_ingredients=[],
                needs_clarification=True,
                clarification_question="What specific ingredients do you have?",
            )
            mock_instance = MagicMock()
            mock_instance.with_structured_output.return_value.invoke.return_value = mock_result
            mock_llm_cls.return_value = mock_instance

            result = intake_parser_node(base_state)

        assert result["flags"]["needs_clarification"] is True
        assert result["interrupt_payload"]["question_type"] == "clarification"

    def test_respects_existing_profile(self, base_state):
        """Existing dietary restrictions in profile should be preserved."""
        base_state["user_profile"]["dietary_restrictions"] = ["vegetarian"]
        base_state["messages"] = [HumanMessage(content="eggs, cheese, spinach")]

        with patch("nodes.intake_parser.ChatOpenAI") as mock_llm_cls:
            from state import ParsedIngredients, Ingredient
            mock_result = ParsedIngredients(
                available_ingredients=[
                    Ingredient(name="eggs", quantity="3", category="protein"),
                ],
                dietary_restrictions=[],  # LLM doesn't override existing
                needs_clarification=False,
            )
            mock_instance = MagicMock()
            mock_instance.with_structured_output.return_value.invoke.return_value = mock_result
            mock_llm_cls.return_value = mock_instance

            result = intake_parser_node(base_state)

        assert "vegetarian" in result["user_profile"]["dietary_restrictions"]


class TestRecipeGenerator:
    def test_generates_high_confidence_recipe(self, base_state, mock_high_confidence_recipe):
        """Should route to PRESENT_RECIPE when confidence ≥ 0.7 and no subs needed."""
        from nodes.recipe_generator import recipe_generator_node

        with patch("nodes.recipe_generator.ChatOpenAI") as mock_llm_cls:
            mock_instance = MagicMock()
            mock_instance.with_structured_output.return_value.invoke.return_value = mock_high_confidence_recipe
            mock_instance.bind_tools.return_value = mock_instance
            mock_llm_cls.return_value = mock_instance

            result = recipe_generator_node(base_state)

        assert result["recipe_candidate"]["name"] == "Garlic Chicken Pasta"
        assert result["recipe_candidate"]["confidence_score"] >= 0.7
        assert result["flags"]["needs_substitution"] is False
        assert result["iteration_count"] == 1

    def test_increments_iteration_count(self, base_state, mock_high_confidence_recipe):
        """Iteration count must increment on each call."""
        from nodes.recipe_generator import recipe_generator_node

        base_state["iteration_count"] = 1

        with patch("nodes.recipe_generator.ChatOpenAI") as mock_llm_cls:
            mock_instance = MagicMock()
            mock_instance.with_structured_output.return_value.invoke.return_value = mock_high_confidence_recipe
            mock_instance.bind_tools.return_value = mock_instance
            mock_llm_cls.return_value = mock_instance

            result = recipe_generator_node(base_state)

        assert result["iteration_count"] == 2

    def test_blocks_allergen_conflict(self, base_state, mock_high_confidence_recipe):
        """Should set impossible_constraints=True when allergen is in recipe."""
        from nodes.recipe_generator import recipe_generator_node

        base_state["user_profile"]["allergies"] = ["gluten"]
        # pasta contains gluten — should trigger block

        with patch("nodes.recipe_generator.ChatOpenAI") as mock_llm_cls:
            mock_instance = MagicMock()
            mock_instance.with_structured_output.return_value.invoke.return_value = mock_high_confidence_recipe
            mock_instance.bind_tools.return_value = mock_instance
            mock_llm_cls.return_value = mock_instance

            result = recipe_generator_node(base_state)

        assert result["flags"]["impossible_constraints"] is True


class TestRouting:
    def test_route_to_present_recipe(self, base_state):
        """High confidence + no subs → PRESENT_RECIPE."""
        from graph import route_after_generator

        base_state["recipe_candidate"]["confidence_score"] = 0.85
        base_state["flags"]["needs_substitution"] = False
        base_state["flags"]["impossible_constraints"] = False
        base_state["iteration_count"] = 1

        assert route_after_generator(base_state) == "present_recipe"

    def test_route_to_substitution_negotiator(self, base_state):
        """Needs substitution → SUBSTITUTION_NEGOTIATOR."""
        from graph import route_after_generator

        base_state["recipe_candidate"]["confidence_score"] = 0.75
        base_state["flags"]["needs_substitution"] = True
        base_state["flags"]["impossible_constraints"] = False
        base_state["iteration_count"] = 1

        assert route_after_generator(base_state) == "substitution_negotiator"

    def test_route_to_constraint_rescue_impossible(self, base_state):
        """Impossible constraints → CONSTRAINT_RESCUE."""
        from graph import route_after_generator

        base_state["flags"]["impossible_constraints"] = True

        assert route_after_generator(base_state) == "constraint_rescue"

    def test_route_to_constraint_rescue_max_iterations(self, base_state):
        """Max iterations reached → CONSTRAINT_RESCUE regardless of confidence."""
        from graph import route_after_generator

        base_state["recipe_candidate"]["confidence_score"] = 0.9
        base_state["flags"]["needs_substitution"] = False
        base_state["flags"]["impossible_constraints"] = False
        base_state["iteration_count"] = 3  # >= max_iterations (3)

        assert route_after_generator(base_state) == "constraint_rescue"

    def test_route_to_constraint_rescue_low_confidence(self, base_state):
        """Low confidence → CONSTRAINT_RESCUE."""
        from graph import route_after_generator

        base_state["recipe_candidate"]["confidence_score"] = 0.2
        base_state["flags"]["needs_substitution"] = False
        base_state["flags"]["impossible_constraints"] = False
        base_state["iteration_count"] = 1

        assert route_after_generator(base_state) == "constraint_rescue"
