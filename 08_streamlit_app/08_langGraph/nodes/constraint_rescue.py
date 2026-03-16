"""
nodes/constraint_rescue.py — Node 5: CONSTRAINT_RESCUE (Interrupt Point)

Triggered when no viable recipe exists. Diagnoses the bottleneck and
presents 3 rescue paths to the user.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.types import interrupt, Command

from config import settings, CONSTRAINT_RESCUE_PROMPT, InterruptType
from state import RecipeState, RescueDiagnosis


def constraint_rescue_node(state: RecipeState) -> Command:
    """
    Node 5: CONSTRAINT_RESCUE

    interrupt() payload:
    {
        "question_type": "rescue_option",
        "content": str (diagnosis),
        "bottleneck": str,
        "rescue_paths": [RescuePathOption, ...],
        "options": ["add_ingredients", "simple_meal", "replan"]
    }

    Resume with Command(resume={"path": "add_ingredients" | "simple_meal" | "replan"})
    """
    session = state["current_session"]
    ingredients = session.get("available_ingredients", [])
    time_limit = session.get("time_limit")

    prompt = (
        f"Available ingredients: {[i['name'] for i in ingredients]}\n"
        f"Time limit: {time_limit or 'flexible'} minutes\n"
        f"Equipment: {', '.join(session.get('equipment_available', []))}\n"
        f"Dietary restrictions: {', '.join(state['user_profile'].get('dietary_restrictions', [])) or 'none'}\n"
        f"Allergies: {', '.join(state['user_profile'].get('allergies', [])) or 'none'}\n"
        f"Iterations tried: {state['iteration_count']}\n"
        f"Last confidence score: {state['recipe_candidate'].get('confidence_score', 0):.2f}"
    )

    llm = ChatOpenAI(
        model=settings.model,
        temperature=0.4,
        api_key=settings.openai_api_key,
    )
    structured_llm = llm.with_structured_output(RescueDiagnosis)

    try:
        diagnosis: RescueDiagnosis = structured_llm.invoke([
            SystemMessage(content=CONSTRAINT_RESCUE_PROMPT),
            HumanMessage(content=prompt),
        ])
        paths = [p.dict() for p in diagnosis.rescue_paths]
        diag_text = diagnosis.diagnosis
        bottleneck = diagnosis.bottleneck
    except Exception:
        diag_text = "I'm having trouble finding a viable recipe with the current ingredients."
        bottleneck = "Insufficient ingredients"
        paths = [
            {"id": "add_ingredients", "title": "Quick grocery run", "description": "Pick up 1-2 key ingredients to unlock more recipes", "additions": ["protein of choice", "pasta or rice"]},
            {"id": "simple_meal", "title": "Simple snack meal", "description": "I'll make the best possible simple dish with what you have"},
            {"id": "replan", "title": "Start fresh", "description": "Let's rethink the meal type entirely"},
        ]

    # interrupt() — present rescue options
    user_response = interrupt({
        "question_type": InterruptType.RESCUE_OPTION,
        "content": diag_text,
        "bottleneck": bottleneck,
        "rescue_paths": paths,
        "options": [p["id"] for p in paths],
        "state_snapshot": {
            "ingredient_count": len(ingredients),
            "iterations": state["iteration_count"],
        },
    })

    path = user_response.get("path", "simple_meal") if isinstance(user_response, dict) else "simple_meal"

    if path == "replan":
        # Clear session, keep profile — route back to INTAKE_PARSER
        return Command(
            update={
                "current_session": {
                    "available_ingredients": [],
                    "time_limit": None,
                    "equipment_available": state["current_session"].get("equipment_available", ["stovetop"]),
                },
                "recipe_candidate": {
                    "name": "", "required_ingredients": [], "missing_ingredients": [],
                    "substitutions": {}, "instructions": [], "confidence_score": 0.0,
                    "flavor_profile_tags": [], "total_time": 0, "difficulty": "intermediate",
                    "chef_notes": "",
                },
                "iteration_count": 0,
                "flags": {**state["flags"], "impossible_constraints": False},
                "messages": [AIMessage(content="🔄 Let's start fresh! Tell me what ingredients you have and we'll find something great.")],
                "current_node": "CONSTRAINT_RESCUE",
            },
            goto="intake_parser",
        )

    elif path == "add_ingredients":
        # Add hypothetical ingredients and retry generation
        additions = next(
            (p.get("additions", []) for p in paths if p["id"] == "add_ingredients"),
            []
        )
        # Add hypothetical ingredients to session for planning purposes
        new_ingredients = list(state["current_session"]["available_ingredients"])
        for item in additions:
            new_ingredients.append({"name": item, "quantity": "as needed", "category": "general"})

        return Command(
            update={
                "current_session": {**state["current_session"], "available_ingredients": new_ingredients},
                "iteration_count": 0,  # reset counter for new attempt
                "flags": {**state["flags"], "impossible_constraints": False},
                "messages": [AIMessage(content=f"🛒 Planning with these additions: {', '.join(additions)}. Let me find a recipe...")],
                "current_node": "CONSTRAINT_RESCUE",
            },
            goto="recipe_generator",
        )

    else:  # simple_meal
        # Generate a minimal recipe — reset time constraints
        return Command(
            update={
                "current_session": {
                    **state["current_session"],
                    "time_limit": 15,  # Quick meal
                },
                "iteration_count": 0,
                "flags": {**state["flags"], "impossible_constraints": False},
                "messages": [AIMessage(content="🥄 Let me find the simplest possible meal with what you have...")],
                "current_node": "CONSTRAINT_RESCUE",
            },
            goto="recipe_generator",
        )
