"""
nodes/intake_parser.py — Node 1: INTAKE_PARSER

Parses raw user message → structured ingredients, session data, flags.
Uses structured output (with_structured_output) to populate ParsedIngredients.
"""

from __future__ import annotations

import json
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from config import settings, INTAKE_PARSER_PROMPT
from state import RecipeState, ParsedIngredients


def intake_parser_node(state: RecipeState) -> dict:
    """
    Node 1: INTAKE_PARSER

    Input:  Last human message in state["messages"]
    Output: Populated current_session, user_profile updates, flags

    Routing:
      → CLARIFICATION if flags.needs_clarification
      → RECIPE_GENERATOR otherwise
    """
    # Get latest user message
    last_human = next(
        (m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
        None,
    )
    if not last_human:
        return {"flags": {**state["flags"], "needs_clarification": True},
                "pending_question": "What ingredients do you have available?",
                "current_node": "INTAKE_PARSER"}

    user_input = last_human.content

    # Build context from existing profile
    profile = state["user_profile"]
    context_parts = []
    if profile.get("dietary_restrictions"):
        context_parts.append(f"Dietary restrictions: {', '.join(profile['dietary_restrictions'])}")
    if profile.get("allergies"):
        context_parts.append(f"Allergies: {', '.join(profile['allergies'])}")
    if profile.get("skill_level"):
        context_parts.append(f"Skill level: {profile['skill_level']}")
    context = ". ".join(context_parts)

    # Build the LLM (structured output)
    llm = ChatOpenAI(
        model=settings.model,
        temperature=0.1,
        api_key=settings.openai_api_key,
    )
    structured_llm = llm.with_structured_output(ParsedIngredients)

    prompt = f"{context}\n\nUser message: {user_input}" if context else f"User message: {user_input}"

    try:
        parsed: ParsedIngredients = structured_llm.invoke([
            SystemMessage(content=INTAKE_PARSER_PROMPT),
            HumanMessage(content=prompt),
        ])
    except Exception as e:
        # Fallback: set clarification flag if parsing fails
        return {
            "flags": {**state["flags"], "needs_clarification": True},
            "pending_question": f"I couldn't parse that. Could you list your ingredients one by one? (Error: {e})",
            "current_node": "INTAKE_PARSER",
        }

    # Build updated session
    new_session = {
        "available_ingredients": [ing.dict() for ing in parsed.available_ingredients],
        "time_limit": parsed.time_limit or state["current_session"].get("time_limit"),
        "equipment_available": (
            parsed.equipment_available
            if parsed.equipment_available
            else state["current_session"].get("equipment_available", ["stovetop", "oven", "microwave"])
        ),
    }

    # Update profile with any restrictions/allergies mentioned
    updated_profile = dict(state["user_profile"])
    if parsed.dietary_restrictions:
        existing = set(updated_profile.get("dietary_restrictions", []))
        updated_profile["dietary_restrictions"] = list(existing | set(parsed.dietary_restrictions))
    if parsed.allergies:
        existing = set(updated_profile.get("allergies", []))
        updated_profile["allergies"] = list(existing | set(parsed.allergies))

    # Build interrupt payload for clarification if needed
    interrupt_payload = None
    if parsed.needs_clarification:
        interrupt_payload = {
            "question_type": "clarification",
            "content": parsed.clarification_question or "Could you clarify your ingredients?",
            "options": None,
            "state_snapshot": {
                "parsed_so_far": len(parsed.available_ingredients),
                "ingredients": [i.name for i in parsed.available_ingredients],
            },
        }

    return {
        "current_session": new_session,
        "user_profile": updated_profile,
        "flags": {
            **state["flags"],
            "needs_clarification": parsed.needs_clarification,
        },
        "interrupt_payload": interrupt_payload,
        "pending_question": parsed.clarification_question if parsed.needs_clarification else None,
        "current_node": "INTAKE_PARSER",
    }
