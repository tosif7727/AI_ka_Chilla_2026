"""
state.py — LangGraph State Schema + Pydantic Models

The RecipeState TypedDict is the single source of truth passed between
every node in the graph. Pydantic models are used for structured LLM output.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Optional
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────

class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class SpiceTolerance(str, Enum):
    MILD = "mild"
    MEDIUM = "medium"
    HOT = "hot"
    VERY_HOT = "very_hot"


class UserFeedback(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    MODIFY = "MODIFY"
    SAVE = "SAVE"


class IngredientImportance(str, Enum):
    CRITICAL = "critical"
    OPTIONAL = "optional"


class ModificationType(str, Enum):
    FLAVOR = "flavor"
    EQUIPMENT = "equipment"
    SCALE = "scale"
    INGREDIENT_SWAP = "ingredient_swap"
    TIME = "time"


class ModificationIntensity(str, Enum):
    SUBTLE = "subtle"
    MODERATE = "moderate"
    COMPLETE_OVERHAUL = "complete_overhaul"


class RescuePath(str, Enum):
    ADD_INGREDIENTS = "add_ingredients"
    SIMPLE_MEAL = "simple_meal"
    REPLAN = "replan"


# ─────────────────────────────────────────────
# Sub-models (used inside state dicts)
# ─────────────────────────────────────────────

class Ingredient(BaseModel):
    name: str
    quantity: str
    category: str = "general"
    unit: Optional[str] = None
    confidence: float = 1.0


class RecipeIngredient(BaseModel):
    name: str
    quantity: str
    available: bool = False
    importance: IngredientImportance = IngredientImportance.CRITICAL


class InstructionStep(BaseModel):
    step: int
    text: str
    time_minutes: Optional[int] = None
    technique_tip: Optional[str] = None


class SubstitutionOption(BaseModel):
    ingredient: str
    ratio: str
    trade_offs: str
    available: bool = False


class SubstitutionPair(BaseModel):
    purpose: str
    option_a: SubstitutionOption
    option_b: SubstitutionOption


class RescuePathOption(BaseModel):
    id: RescuePath
    title: str
    description: str
    additions: list[str] = Field(default_factory=list)
    recipe_hint: Optional[str] = None


class RecipeHistoryEntry(BaseModel):
    recipe_id: str
    name: str
    rating: Optional[int] = None
    would_make_again: Optional[bool] = None
    timestamp: str
    notes: Optional[str] = None
    flavor_tags: list[str] = Field(default_factory=list)
    substitutions_used: dict[str, str] = Field(default_factory=dict)


# ─────────────────────────────────────────────
# Main State TypedDict
# ─────────────────────────────────────────────

class RecipeState(TypedDict):
    # Conversation turns — uses add_messages reducer (append, not replace)
    messages: Annotated[list[BaseMessage], add_messages]

    # User profile — persists across sessions
    user_profile: dict  # {
    #   dietary_restrictions: list[str],
    #   allergies: list[str],
    #   skill_level: SkillLevel,
    #   time_preference: int (minutes),
    #   cuisine_preferences: list[str],
    #   spice_tolerance: SpiceTolerance
    # }

    # Current session data
    current_session: dict  # {
    #   available_ingredients: list[Ingredient],
    #   time_limit: Optional[int],
    #   equipment_available: list[str]
    # }

    # Active recipe being built
    recipe_candidate: dict  # {
    #   name: str,
    #   required_ingredients: list[RecipeIngredient],
    #   missing_ingredients: list[RecipeIngredient],
    #   substitutions: dict[str, SubstitutionPair],
    #   instructions: list[InstructionStep],
    #   confidence_score: float,
    #   flavor_profile_tags: list[str],
    #   total_time: int,
    #   difficulty: str,
    #   chef_notes: str
    # }

    # Loop guard — max 3 iterations before forced CONSTRAINT_RESCUE
    iteration_count: int

    # Last feedback from user at PRESENT_RECIPE interrupt
    user_feedback: Optional[str]

    # Boolean control flags
    flags: dict  # {
    #   impossible_constraints: bool,
    #   needs_substitution: bool,
    #   needs_clarification: bool,
    #   api_unavailable: bool
    # }

    # Long-term memory — persisted to disk/DB across sessions
    persistent_memory: dict  # {
    #   kitchen_staples: dict[str, int]  (frequency counter),
    #   taste_preferences: dict[str, float]  (weighted tags),
    #   substitution_success_rate: dict[str, float],
    #   recipe_history: list[RecipeHistoryEntry]
    # }

    # Which node are we currently in
    current_node: str

    # Payload surfaced to user at interrupt() points
    interrupt_payload: Optional[dict]

    # Current cooking step index (for COOKING_MODE)
    cooking_step_index: int

    # Pending clarification question
    pending_question: Optional[str]


# ─────────────────────────────────────────────
# Pydantic models for structured LLM output
# ─────────────────────────────────────────────

class ParsedIngredients(BaseModel):
    """Structured output from INTAKE_PARSER node."""
    available_ingredients: list[Ingredient]
    time_limit: Optional[int] = None
    equipment_available: list[str] = Field(default_factory=list)
    dietary_restrictions: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    needs_clarification: bool = False
    clarification_question: Optional[str] = None


class GeneratedRecipe(BaseModel):
    """Structured output from RECIPE_GENERATOR node."""
    name: str
    required_ingredients: list[RecipeIngredient]
    missing_ingredients: list[RecipeIngredient]
    instructions: list[InstructionStep]
    confidence_score: float = Field(ge=0.0, le=1.0)
    flavor_profile_tags: list[str]
    total_time: int
    difficulty: str
    needs_substitution: bool = False
    impossible_constraints: bool = False
    chef_notes: str = ""


class GeneratedSubstitutions(BaseModel):
    """Structured output from SUBSTITUTION_NEGOTIATOR node."""
    substitutions: dict[str, SubstitutionPair]


class RescueDiagnosis(BaseModel):
    """Structured output from CONSTRAINT_RESCUE node."""
    diagnosis: str
    bottleneck: str
    rescue_paths: list[RescuePathOption]


class ModificationRequest(BaseModel):
    """Structured output from MODIFICATION_HANDLER node."""
    modification_type: ModificationType
    specific_request: str
    intensity: ModificationIntensity
    scale_factor: Optional[float] = None  # for scale modifications


class FeedbackAnalysis(BaseModel):
    """Structured output from FEEDBACK_COLLECTOR node."""
    taste_tags_boost: list[str]
    taste_tags_penalize: list[str]
    substitution_ratings: dict[str, float] = Field(default_factory=dict)
    summary: str


# ─────────────────────────────────────────────
# State factory
# ─────────────────────────────────────────────

def make_initial_state(
    dietary_restrictions: list[str] | None = None,
    allergies: list[str] | None = None,
    skill_level: str = "intermediate",
    time_preference: int = 30,
    cuisine_preferences: list[str] | None = None,
    spice_tolerance: str = "medium",
    persistent_memory: dict | None = None,
) -> dict:
    """Factory to create a clean initial state, optionally with loaded profile."""
    return {
        "messages": [],
        "user_profile": {
            "dietary_restrictions": dietary_restrictions or [],
            "allergies": allergies or [],
            "skill_level": skill_level,
            "time_preference": time_preference,
            "cuisine_preferences": cuisine_preferences or [],
            "spice_tolerance": spice_tolerance,
        },
        "current_session": {
            "available_ingredients": [],
            "time_limit": None,
            "equipment_available": ["stovetop", "oven", "microwave"],
        },
        "recipe_candidate": {
            "name": "",
            "required_ingredients": [],
            "missing_ingredients": [],
            "substitutions": {},
            "instructions": [],
            "confidence_score": 0.0,
            "flavor_profile_tags": [],
            "total_time": 0,
            "difficulty": "intermediate",
            "chef_notes": "",
        },
        "iteration_count": 0,
        "user_feedback": None,
        "flags": {
            "impossible_constraints": False,
            "needs_substitution": False,
            "needs_clarification": False,
            "api_unavailable": False,
        },
        "persistent_memory": persistent_memory or {
            "kitchen_staples": {},
            "taste_preferences": {},
            "substitution_success_rate": {},
            "recipe_history": [],
        },
        "current_node": "IDLE",
        "interrupt_payload": None,
        "cooking_step_index": 0,
        "pending_question": None,
    }
