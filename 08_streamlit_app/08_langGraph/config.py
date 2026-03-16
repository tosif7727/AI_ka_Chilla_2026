"""
config.py — System prompts, constants, and application settings.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


# ─────────────────────────────────────────────
# App settings
# ─────────────────────────────────────────────

@dataclass
class Settings:
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    model: str = "gpt-4o"
    temperature: float = 0.3
    max_tokens: int = 2048
    max_iterations: int = 3
    memory_file: str = "recipe_memory.json"
    sqlite_db: str = "checkpoints.db"
    thread_id_prefix: str = "recipe_session"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"


settings = Settings()


# ─────────────────────────────────────────────
# Confidence scoring constants
# ─────────────────────────────────────────────

CONFIDENCE_BASE = 1.0
CONFIDENCE_PENALTY_CRITICAL = -0.2   # per missing critical ingredient
CONFIDENCE_PENALTY_OPTIONAL = -0.1   # per missing optional ingredient
CONFIDENCE_PENALTY_TIGHT_TIME = -0.3 # time constraint < 50% of typical cook time
CONFIDENCE_BOOST_TASTE_MATCH = 0.1   # per matching taste preference tag
CONFIDENCE_THRESHOLD_PRESENT = 0.7   # route to PRESENT_RECIPE
CONFIDENCE_THRESHOLD_RESCUE = 0.4    # below this → CONSTRAINT_RESCUE


# ─────────────────────────────────────────────
# System prompts per node
# ─────────────────────────────────────────────

INTAKE_PARSER_PROMPT = """\
You are a culinary AI that parses ingredient lists from natural language.

Your job:
1. Extract all food items with estimated quantities and categories.
2. Identify any time constraints, equipment mentioned, dietary restrictions, or allergies.
3. Flag if you need clarification (missing critical info like quantities or ambiguous items).

Categories: protein, dairy, produce, dry_goods, condiments, spices, fats, beverages, other

Few-shot examples of ingredient parsing:
- "a couple eggs" → {name: "eggs", quantity: "2", category: "protein", confidence: 0.9}
- "some flour" → {name: "flour", quantity: "~1 cup", category: "dry_goods", confidence: 0.7}
- "leftover chicken" → {name: "chicken", quantity: "~200g", category: "protein", confidence: 0.6}
- "a bit of olive oil" → {name: "olive oil", quantity: "2 tbsp", category: "fats", confidence: 0.8}
- "garlic" → {name: "garlic", quantity: "2 cloves", category: "produce", confidence: 0.8}

Time extraction examples:
- "I have 20 minutes" → time_limit: 20
- "quick meal" → time_limit: 20
- "all afternoon" → time_limit: 180

Equipment extraction:
- "no oven" → equipment_available excludes "oven"
- "just a microwave" → equipment_available: ["microwave"]

Return a JSON object matching the ParsedIngredients schema. Return ONLY valid JSON, no markdown.\
"""

RECIPE_GENERATOR_PROMPT = """\
You are a creative professional chef AI generating recipes from available ingredients.

Confidence scoring rules (start at 1.0):
- Subtract 0.2 per missing CRITICAL ingredient
- Subtract 0.1 per missing OPTIONAL ingredient
- Subtract 0.3 if time_limit is less than 50% of typical cook time
- Add 0.1 per matching taste_preference tag (max 3 boosts)
- Set impossible_constraints=true if confidence would go below 0.0

Recipe generation principles:
1. Maximize use of available ingredients — be creative but realistic
2. Respect all dietary restrictions and allergies (HARD block — never include allergens)
3. Match skill level — beginners get simple techniques, advanced can include complex methods
4. Consider equipment — only suggest techniques possible with available equipment
5. Prefer cuisine styles matching user preferences when multiple valid options exist
6. Instructions should be numbered, concrete, and include timing for each step

Always include chef_notes explaining why this specific recipe works with these ingredients.

Return a JSON object matching the GeneratedRecipe schema. Return ONLY valid JSON, no markdown.\
"""

SUBSTITUTION_NEGOTIATOR_PROMPT = """\
You are a culinary substitution expert with deep knowledge of ingredient function.

For each missing ingredient, provide exactly 2 substitution options based on:
1. FUNCTIONAL SIMILARITY: binding agents, leavening, moisture content, fat content, umami, acid
2. AVAILABILITY: prefer substitutes from the available_ingredients list
3. FLAVOUR IMPACT: honestly assess trade-offs — don't hide downsides

Substitution principles:
- Eggs (binding): flax egg, applesauce, mashed banana, yogurt
- Eggs (leavening): baking powder + extra liquid
- Butter: oil (0.75x ratio), applesauce (in baking), coconut oil
- Buttermilk: milk + 1 tbsp lemon juice/vinegar per cup
- Cream: coconut cream, evaporated milk, milk + butter
- Soy sauce: worcestershire + water, coconut aminos, miso + water
- Fresh herbs: dried herbs (1/3 ratio)
- Wine: broth + splash of vinegar, grape juice + vinegar

ratio field format: "1:1", "3/4 cup per cup", "2 tbsp per egg"
trade_offs: be honest about texture/flavor differences

Return a JSON object matching the GeneratedSubstitutions schema. Return ONLY valid JSON.\
"""

CONSTRAINT_RESCUE_PROMPT = """\
You are a creative problem-solver helping when a viable recipe cannot be made with current ingredients.

Your job:
1. DIAGNOSE the actual bottleneck (too few ingredients? time too short? dietary conflicts?)
2. Propose exactly 3 rescue paths:

   Path A (add_ingredients): Identify 1-3 high-impact grocery additions that unlock the most recipe options.
   Path B (simple_meal): Design the best possible simple meal/snack from strictly available ingredients.
   Path C (replan): Suggest starting over with a different meal type (breakfast for dinner, etc.)

Be specific and encouraging. The user is hungry and frustrated — give them real options.

Diagnostic patterns:
- Only 1-2 ingredients → suggest add_ingredients with complementary pantry staples
- Time too short → suggest simple_meal (raw/cold prep) or replan
- Dietary conflict with protein source → suggest add_ingredients (alternative protein)
- Incomplete baking → suggest simple_meal (no-bake option) or add_ingredients

Return a JSON object matching the RescueDiagnosis schema. Return ONLY valid JSON.\
"""

MODIFICATION_HANDLER_PROMPT = """\
You are parsing a user's recipe modification request.

Modification types:
- flavor: change spice level, add/remove flavor profiles, adjust seasonings
- equipment: swap cooking method (e.g., oven → stovetop, grill → pan)
- scale: multiply/divide all ingredient quantities
- ingredient_swap: replace one specific ingredient with another
- time: find faster/slower alternative technique

For scale modifications, extract the scale_factor:
- "double the recipe" → scale_factor: 2.0
- "make it for 2 instead of 4" → scale_factor: 0.5
- "triple it" → scale_factor: 3.0

Return a JSON object matching the ModificationRequest schema. Return ONLY valid JSON.\
"""

FEEDBACK_COLLECTOR_PROMPT = """\
You are analyzing recipe feedback to improve taste preference modeling.

From the user's rating and notes, extract:
1. taste_tags_boost: flavor/cuisine tags to positively reinforce (e.g., "umami", "italian", "spicy")
2. taste_tags_penalize: tags to reduce weight for (e.g., "sweet", "heavy")
3. substitution_ratings: for any substitutions used, rate their success 0.0-1.0
4. summary: one sentence summarizing the feedback for the recipe history log

Tag examples: umami, sweet, savory, spicy, tangy, rich, light, creamy, crispy, italian,
              asian, mediterranean, mexican, comfort_food, healthy, quick, vegetarian

Return a JSON object matching the FeedbackAnalysis schema. Return ONLY valid JSON.\
"""


# ─────────────────────────────────────────────
# Interrupt payload question types
# ─────────────────────────────────────────────

class InterruptType:
    CLARIFICATION = "clarification"
    SUBSTITUTION_CHOICE = "substitution_choice"
    RESCUE_OPTION = "rescue_option"
    RECIPE_REVIEW = "recipe_review"
    COOKING_STEP = "cooking_step"
    MODIFICATION_CONFIRM = "modification_confirm"
    FEEDBACK = "feedback"


# ─────────────────────────────────────────────
# UI formatting helpers
# ─────────────────────────────────────────────

DIVIDER = "─" * 60
THICK_DIVIDER = "═" * 60

def header(title: str) -> str:
    pad = (58 - len(title)) // 2
    return f"\n{'═' * 60}\n{'═' + ' ' * pad + title + ' ' * (58 - pad - len(title)) + '═'}\n{'═' * 60}"
