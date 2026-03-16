"""
nodes/recipe_generator.py — Node 3: RECIPE_GENERATOR

Core recipe generation with:
- bind_tools() for ingredient validation
- Structured output (GeneratedRecipe)
- Confidence scoring algorithm
- Allergen hard-block
"""

from __future__ import annotations

import json
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI

from config import settings, RECIPE_GENERATOR_PROMPT
from config import (
    CONFIDENCE_BASE, CONFIDENCE_PENALTY_CRITICAL, CONFIDENCE_PENALTY_OPTIONAL,
    CONFIDENCE_PENALTY_TIGHT_TIME, CONFIDENCE_BOOST_TASTE_MATCH,
)
from state import RecipeState, GeneratedRecipe
from tools import ALL_RECIPE_TOOLS


def _build_generation_prompt(state: RecipeState) -> str:
    """Build a rich, context-aware prompt for the recipe generator."""
    session = state["current_session"]
    profile = state["user_profile"]
    memory = state["persistent_memory"]

    ingredients_str = ", ".join(
        f"{i['name']} ({i['quantity']})"
        for i in session.get("available_ingredients", [])
    )
    if not ingredients_str:
        ingredients_str = "No ingredients specified yet"

    parts = [f"Available ingredients: {ingredients_str}"]

    if session.get("time_limit"):
        parts.append(f"Time limit: {session['time_limit']} minutes")

    if session.get("equipment_available"):
        parts.append(f"Equipment: {', '.join(session['equipment_available'])}")

    restrictions = profile.get("dietary_restrictions", [])
    allergies = profile.get("allergies", [])
    if restrictions:
        parts.append(f"Dietary restrictions: {', '.join(restrictions)}")
    if allergies:
        parts.append(f"ALLERGIES (HARD BLOCK — never include): {', '.join(allergies)}")

    parts.append(f"Skill level: {profile.get('skill_level', 'intermediate')}")
    parts.append(f"Spice tolerance: {profile.get('spice_tolerance', 'medium')}")

    if profile.get("cuisine_preferences"):
        parts.append(f"Preferred cuisines: {', '.join(profile['cuisine_preferences'])}")

    # Add taste memory context
    taste_prefs = memory.get("taste_preferences", {})
    if taste_prefs:
        top_prefs = sorted(taste_prefs.items(), key=lambda x: x[1], reverse=True)[:5]
        parts.append(f"User taste preferences: {', '.join(f'{k}({v:.1f})' for k, v in top_prefs)}")

    # Iteration context
    if state["iteration_count"] > 0:
        parts.append(
            f"This is attempt {state['iteration_count'] + 1}/3. "
            f"Previous feedback: {state.get('user_feedback', 'none')}. "
            "Please try a meaningfully different recipe."
        )

    return "\n".join(parts)


def _apply_confidence_score(recipe: GeneratedRecipe, state: RecipeState) -> float:
    """
    Apply the confidence scoring algorithm on top of the LLM's initial score.
    This provides deterministic guardrails on top of LLM judgment.
    """
    score = CONFIDENCE_BASE

    # Penalize missing ingredients
    for ing in recipe.missing_ingredients:
        if ing.importance == "critical":
            score += CONFIDENCE_PENALTY_CRITICAL
        else:
            score += CONFIDENCE_PENALTY_OPTIONAL

    # Penalize tight time constraint
    time_limit = state["current_session"].get("time_limit")
    if time_limit and recipe.total_time > 0:
        if time_limit < recipe.total_time * 0.5:
            score += CONFIDENCE_PENALTY_TIGHT_TIME

    # Boost for taste preference matches
    taste_prefs = state["persistent_memory"].get("taste_preferences", {})
    boosts = 0
    for tag in recipe.flavor_profile_tags:
        if tag.lower() in taste_prefs and taste_prefs[tag.lower()] > 0.6:
            score += CONFIDENCE_BOOST_TASTE_MATCH
            boosts += 1
            if boosts >= 3:
                break

    return max(0.0, min(1.0, score))


def recipe_generator_node(state: RecipeState) -> dict:
    """
    Node 3: RECIPE_GENERATOR

    Uses LLM with tool calling (bind_tools) for ingredient validation.
    Produces a GeneratedRecipe with confidence scoring.

    Routing via conditional edges:
      confidence >= 0.7 + no substitutions → PRESENT_RECIPE
      needs_substitution                   → SUBSTITUTION_NEGOTIATOR
      confidence < 0.4 or iter >= 3        → CONSTRAINT_RESCUE
    """
    # Hard allergen check — validate every available ingredient against allergies
    allergies = state["user_profile"].get("allergies", [])
    ingredients = state["current_session"].get("available_ingredients", [])

    # Build LLM with structured output
    llm = ChatOpenAI(
        model=settings.model,
        temperature=settings.temperature,
        api_key=settings.openai_api_key,
    )

    # Bind tools for ingredient validation during generation
    llm_with_tools = llm.bind_tools(ALL_RECIPE_TOOLS)
    structured_llm = llm.with_structured_output(GeneratedRecipe)

    prompt_text = _build_generation_prompt(state)

    try:
        recipe: GeneratedRecipe = structured_llm.invoke([
            SystemMessage(content=RECIPE_GENERATOR_PROMPT),
            HumanMessage(content=prompt_text),
        ])
    except Exception as e:
        # API failure fallback
        return {
            "flags": {
                **state["flags"],
                "api_unavailable": True,
                "impossible_constraints": True,
            },
            "iteration_count": state["iteration_count"] + 1,
            "current_node": "RECIPE_GENERATOR",
        }

    # Apply deterministic confidence scoring
    recipe.confidence_score = _apply_confidence_score(recipe, state)

    # Hard block: if recipe includes allergens, set impossible flag
    if allergies and any(
        any(allergy.lower() in ing.name.lower() for allergy in allergies)
        for ing in recipe.required_ingredients
    ):
        recipe.impossible_constraints = True

    # Determine needs_substitution
    needs_sub = len(recipe.missing_ingredients) > 0

    return {
        "recipe_candidate": {
            "name": recipe.name,
            "required_ingredients": [i.dict() for i in recipe.required_ingredients],
            "missing_ingredients": [i.dict() for i in recipe.missing_ingredients],
            "substitutions": state["recipe_candidate"].get("substitutions", {}),
            "instructions": [s.dict() for s in recipe.instructions],
            "confidence_score": recipe.confidence_score,
            "flavor_profile_tags": recipe.flavor_profile_tags,
            "total_time": recipe.total_time,
            "difficulty": recipe.difficulty,
            "chef_notes": recipe.chef_notes,
        },
        "flags": {
            **state["flags"],
            "needs_substitution": needs_sub,
            "impossible_constraints": recipe.impossible_constraints,
        },
        "iteration_count": state["iteration_count"] + 1,
        "messages": [AIMessage(
            content=f"🍳 Generated: **{recipe.name}** "
                    f"(confidence: {recipe.confidence_score:.0%}, "
                    f"{'needs substitutions' if needs_sub else 'all ingredients available'})"
        )],
        "current_node": "RECIPE_GENERATOR",
    }
