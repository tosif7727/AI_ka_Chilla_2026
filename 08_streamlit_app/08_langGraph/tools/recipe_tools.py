"""
tools/recipe_tools.py — LangChain @tool definitions bound to RECIPE_GENERATOR node.

These tools are used with bind_tools() to give the recipe generation LLM
the ability to validate ingredients, check allergens, and look up substitutions.
"""

from __future__ import annotations

import json
from typing import Optional

from langchain_core.tools import tool


# ─────────────────────────────────────────────
# Mock ingredient database (replace with real API)
# ─────────────────────────────────────────────

INGREDIENT_DB = {
    # proteins
    "chicken": {"categories": ["protein"], "allergens": [], "typical_cook_time": 20},
    "eggs": {"categories": ["protein", "binder"], "allergens": ["eggs"], "typical_cook_time": 5},
    "beef": {"categories": ["protein"], "allergens": [], "typical_cook_time": 30},
    "salmon": {"categories": ["protein", "fish"], "allergens": ["fish"], "typical_cook_time": 15},
    "tofu": {"categories": ["protein", "vegan"], "allergens": ["soy"], "typical_cook_time": 10},
    "lentils": {"categories": ["protein", "vegan"], "allergens": [], "typical_cook_time": 25},
    # dairy
    "butter": {"categories": ["dairy", "fat"], "allergens": ["dairy"], "typical_cook_time": 0},
    "milk": {"categories": ["dairy"], "allergens": ["dairy"], "typical_cook_time": 0},
    "cheese": {"categories": ["dairy"], "allergens": ["dairy"], "typical_cook_time": 5},
    "yogurt": {"categories": ["dairy"], "allergens": ["dairy"], "typical_cook_time": 0},
    "cream": {"categories": ["dairy", "fat"], "allergens": ["dairy"], "typical_cook_time": 0},
    # produce
    "garlic": {"categories": ["produce", "aromatics"], "allergens": [], "typical_cook_time": 2},
    "onion": {"categories": ["produce", "aromatics"], "allergens": [], "typical_cook_time": 8},
    "tomato": {"categories": ["produce"], "allergens": [], "typical_cook_time": 10},
    "spinach": {"categories": ["produce", "leafy_greens"], "allergens": [], "typical_cook_time": 3},
    "mushrooms": {"categories": ["produce"], "allergens": [], "typical_cook_time": 8},
    "potato": {"categories": ["produce", "starch"], "allergens": [], "typical_cook_time": 25},
    "carrot": {"categories": ["produce"], "allergens": [], "typical_cook_time": 15},
    "broccoli": {"categories": ["produce"], "allergens": [], "typical_cook_time": 8},
    "bell pepper": {"categories": ["produce"], "allergens": [], "typical_cook_time": 8},
    "lemon": {"categories": ["produce", "acid"], "allergens": [], "typical_cook_time": 0},
    # dry goods
    "flour": {"categories": ["dry_goods", "binder"], "allergens": ["gluten"], "typical_cook_time": 0},
    "pasta": {"categories": ["dry_goods", "starch"], "allergens": ["gluten"], "typical_cook_time": 10},
    "rice": {"categories": ["dry_goods", "starch"], "allergens": [], "typical_cook_time": 20},
    "bread": {"categories": ["dry_goods"], "allergens": ["gluten"], "typical_cook_time": 0},
    "oats": {"categories": ["dry_goods"], "allergens": ["gluten"], "typical_cook_time": 5},
    "sugar": {"categories": ["dry_goods", "sweetener"], "allergens": [], "typical_cook_time": 0},
    "baking powder": {"categories": ["dry_goods", "leavening"], "allergens": [], "typical_cook_time": 0},
    "baking soda": {"categories": ["dry_goods", "leavening"], "allergens": [], "typical_cook_time": 0},
    # condiments / fats
    "olive oil": {"categories": ["fat", "condiment"], "allergens": [], "typical_cook_time": 0},
    "soy sauce": {"categories": ["condiment", "umami"], "allergens": ["soy", "gluten"], "typical_cook_time": 0},
    "vinegar": {"categories": ["condiment", "acid"], "allergens": [], "typical_cook_time": 0},
    "honey": {"categories": ["condiment", "sweetener"], "allergens": [], "typical_cook_time": 0},
    "tomato paste": {"categories": ["condiment"], "allergens": [], "typical_cook_time": 0},
    # spices
    "salt": {"categories": ["spice"], "allergens": [], "typical_cook_time": 0},
    "pepper": {"categories": ["spice"], "allergens": [], "typical_cook_time": 0},
    "cumin": {"categories": ["spice"], "allergens": [], "typical_cook_time": 0},
    "paprika": {"categories": ["spice"], "allergens": [], "typical_cook_time": 0},
    "turmeric": {"categories": ["spice"], "allergens": [], "typical_cook_time": 0},
    "basil": {"categories": ["spice", "herb"], "allergens": [], "typical_cook_time": 0},
    "oregano": {"categories": ["spice", "herb"], "allergens": [], "typical_cook_time": 0},
    "thyme": {"categories": ["spice", "herb"], "allergens": [], "typical_cook_time": 0},
    "cinnamon": {"categories": ["spice"], "allergens": [], "typical_cook_time": 0},
}

SUBSTITUTION_MAP = {
    "eggs_binder": [
        {"sub": "flax egg", "ratio": "1 tbsp ground flax + 3 tbsp water per egg", "vegan": True},
        {"sub": "applesauce", "ratio": "1/4 cup per egg", "vegan": True},
        {"sub": "mashed banana", "ratio": "1/4 cup per egg", "vegan": True},
    ],
    "butter_fat": [
        {"sub": "olive oil", "ratio": "3/4 cup per cup of butter", "vegan": True},
        {"sub": "coconut oil", "ratio": "1:1", "vegan": True},
        {"sub": "applesauce", "ratio": "1:1 in baking", "vegan": True},
    ],
    "milk_dairy": [
        {"sub": "oat milk", "ratio": "1:1", "vegan": True},
        {"sub": "almond milk", "ratio": "1:1", "vegan": True},
        {"sub": "coconut milk", "ratio": "1:1", "vegan": True},
    ],
    "flour_gluten_free": [
        {"sub": "almond flour", "ratio": "1:1 (denser result)", "vegan": True},
        {"sub": "rice flour", "ratio": "1:1", "vegan": True},
        {"sub": "oat flour", "ratio": "1:1", "vegan": True},
    ],
}


@tool
def validate_ingredient(ingredient_name: str) -> str:
    """
    Validate whether an ingredient exists in the database and return its properties.
    Returns JSON with categories, allergens, and typical cook time.
    If not found, returns a best-guess based on similar items.
    """
    name = ingredient_name.lower().strip()
    if name in INGREDIENT_DB:
        data = INGREDIENT_DB[name]
        return json.dumps({"found": True, "name": name, **data})

    # Fuzzy match — find partial matches
    matches = [k for k in INGREDIENT_DB if name in k or k in name]
    if matches:
        best = matches[0]
        return json.dumps({
            "found": True,
            "name": best,
            "note": f"Matched '{ingredient_name}' → '{best}'",
            **INGREDIENT_DB[best]
        })

    return json.dumps({
        "found": False,
        "name": name,
        "categories": ["unknown"],
        "allergens": [],
        "typical_cook_time": 10,
        "note": "Not in database — treat as general ingredient"
    })


@tool
def check_allergens(ingredient_name: str, user_allergies: str) -> str:
    """
    Check if an ingredient conflicts with user allergies.
    user_allergies: comma-separated list of allergy strings.
    Returns JSON with conflict: bool and details.
    """
    name = ingredient_name.lower().strip()
    allergies = [a.strip().lower() for a in user_allergies.split(",") if a.strip()]

    ingredient_allergens = []
    if name in INGREDIENT_DB:
        ingredient_allergens = INGREDIENT_DB[name]["allergens"]

    # Check for conflicts including partial matches
    conflicts = []
    for allergy in allergies:
        for allergen in ingredient_allergens:
            if allergy in allergen or allergen in allergy:
                conflicts.append(allergen)

    return json.dumps({
        "ingredient": name,
        "allergens_present": ingredient_allergens,
        "user_allergies": allergies,
        "conflict": len(conflicts) > 0,
        "conflicts": conflicts,
        "safe": len(conflicts) == 0,
    })


@tool
def get_substitutions(ingredient_name: str, purpose: str, dietary_restrictions: str) -> str:
    """
    Get substitution options for a missing ingredient.
    purpose: why the ingredient is used (binding, leavening, fat, dairy, protein, etc.)
    dietary_restrictions: comma-separated list (vegan, gluten_free, etc.)
    Returns JSON list of substitution options sorted by suitability.
    """
    name = ingredient_name.lower().strip()
    restrictions = [r.strip().lower() for r in dietary_restrictions.split(",") if r.strip()]
    is_vegan = "vegan" in restrictions or "vegetarian" in restrictions

    # Look up substitutions by ingredient+purpose key
    key = f"{name}_{purpose}"
    subs = SUBSTITUTION_MAP.get(key, [])

    # Filter by dietary restrictions
    if is_vegan:
        subs = [s for s in subs if s.get("vegan", False)]

    if not subs:
        # Generic fallback
        subs = [
            {"sub": f"similar {purpose} ingredient", "ratio": "adjust to taste", "note": "consult recipe context"},
        ]

    return json.dumps({
        "ingredient": name,
        "purpose": purpose,
        "options": subs[:3],
        "total_options": len(subs),
    })


@tool
def estimate_cook_time(ingredients: str, technique: str) -> str:
    """
    Estimate total cook time for a recipe based on ingredients and technique.
    ingredients: comma-separated ingredient names
    technique: cooking method (stir_fry, roast, simmer, bake, etc.)
    Returns estimated minutes.
    """
    technique_multipliers = {
        "raw": 0,
        "microwave": 0.3,
        "stir_fry": 0.5,
        "sauté": 0.7,
        "simmer": 1.0,
        "boil": 0.8,
        "roast": 1.5,
        "bake": 1.4,
        "braise": 3.0,
        "slow_cook": 8.0,
    }

    names = [i.strip().lower() for i in ingredients.split(",")]
    base_times = []
    for name in names:
        if name in INGREDIENT_DB:
            base_times.append(INGREDIENT_DB[name]["typical_cook_time"])

    if not base_times:
        base_times = [15]  # default

    # The longest ingredient determines overall time (parallel cooking)
    max_time = max(base_times)
    multiplier = technique_multipliers.get(technique.lower(), 1.0)
    estimated = int(max_time * multiplier) + 5  # +5 for prep

    return json.dumps({
        "technique": technique,
        "estimated_minutes": estimated,
        "breakdown": dict(zip(names, base_times)),
    })


# ─────────────────────────────────────────────
# Tool registry — pass to bind_tools()
# ─────────────────────────────────────────────

ALL_RECIPE_TOOLS = [validate_ingredient, check_allergens, get_substitutions, estimate_cook_time]
