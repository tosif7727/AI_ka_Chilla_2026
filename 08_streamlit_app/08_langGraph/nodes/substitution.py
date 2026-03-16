"""
nodes/substitution.py — Node 4: SUBSTITUTION_NEGOTIATOR (Interrupt Point)

Generates 2-3 substitution options per missing ingredient.
Uses interrupt() to present options and await user choice.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.types import interrupt, Command

from config import settings, SUBSTITUTION_NEGOTIATOR_PROMPT, InterruptType
from state import RecipeState, GeneratedSubstitutions
from memory import PersistentMemory


def substitution_negotiator_node(state: RecipeState) -> Command:
    """
    Node 4: SUBSTITUTION_NEGOTIATOR

    interrupt() payload:
    {
        "question_type": "substitution_choice",
        "content": str,
        "substitutions": {missing_ingredient: SubstitutionPair},
        "options": ["accept_all", "reject_all", "custom"],
        "state_snapshot": {recipe_name, missing_list}
    }

    Resume with Command(resume={
        "choice": "accept_all" | "reject_all" | "custom",
        "accepted_substitutions": {original: substitute} (for custom)
    })
    """
    rc = state["recipe_candidate"]
    missing = rc.get("missing_ingredients", [])
    available = state["current_session"].get("available_ingredients", [])
    available_names = ", ".join(i["name"] for i in available)

    # Get substitution success history from memory
    memory = PersistentMemory(settings.memory_file)
    sub_rates = memory._data.get("substitution_success_rate", {})

    # Build prompt
    prompt = (
        f"Missing ingredients for '{rc.get('name', 'this recipe')}':\n"
        f"{[f\"{m['name']} ({m['quantity']}) - {m['importance']}\" for m in missing]}\n\n"
        f"Available ingredients to substitute from: {available_names}\n"
        f"Dietary restrictions: {', '.join(state['user_profile'].get('dietary_restrictions', [])) or 'none'}\n"
        f"Known substitution success rates: {sub_rates}"
    )

    llm = ChatOpenAI(
        model=settings.model,
        temperature=0.2,
        api_key=settings.openai_api_key,
    )
    structured_llm = llm.with_structured_output(GeneratedSubstitutions)

    try:
        result: GeneratedSubstitutions = structured_llm.invoke([
            SystemMessage(content=SUBSTITUTION_NEGOTIATOR_PROMPT),
            HumanMessage(content=prompt),
        ])
        subs_dict = {k: v.dict() for k, v in result.substitutions.items()}
    except Exception:
        # Fallback substitutions
        subs_dict = {
            m["name"]: {
                "purpose": "ingredient",
                "option_a": {"ingredient": "similar available ingredient", "ratio": "1:1", "trade_offs": "May alter flavor slightly", "available": True},
                "option_b": {"ingredient": "omit", "ratio": "n/a", "trade_offs": "Recipe may be less complete", "available": True},
            }
            for m in missing[:3]
        }

    # interrupt() — pause and await user choice
    user_response = interrupt({
        "question_type": InterruptType.SUBSTITUTION_CHOICE,
        "content": f"I need to substitute {len(missing)} ingredient(s) for **{rc.get('name', 'this recipe')}**:",
        "substitutions": subs_dict,
        "options": ["accept_all", "reject_all", "custom"],
        "state_snapshot": {
            "recipe_name": rc.get("name"),
            "missing": [m["name"] for m in missing],
        },
    })

    choice = user_response.get("choice", "reject_all") if isinstance(user_response, dict) else "reject_all"
    accepted = user_response.get("accepted_substitutions", {}) if isinstance(user_response, dict) else {}

    if choice == "reject_all":
        # Route back to RECIPE_GENERATOR for a different recipe
        return Command(
            update={
                "user_feedback": "REJECT",
                "messages": [AIMessage(content="Let me find a different recipe that better matches what you have...")],
                "current_node": "SUBSTITUTION_NEGOTIATOR",
            },
            goto="recipe_generator",
        )

    # Accept: build final substitutions dict
    if choice == "accept_all":
        # Auto-pick option_a for all
        final_subs = {
            ingredient: sub["option_a"]["ingredient"]
            for ingredient, sub in subs_dict.items()
        }
    else:
        # Custom: use whatever was accepted, fill rest with option_a
        final_subs = {}
        for ingredient, sub in subs_dict.items():
            if ingredient in accepted:
                final_subs[ingredient] = accepted[ingredient]
            else:
                final_subs[ingredient] = sub["option_a"]["ingredient"]

    # Update recipe candidate with substitutions applied
    updated_recipe = {
        **state["recipe_candidate"],
        "substitutions": final_subs,
        "missing_ingredients": [],  # Resolved
    }

    return Command(
        update={
            "recipe_candidate": updated_recipe,
            "flags": {**state["flags"], "needs_substitution": False},
            "messages": [AIMessage(
                content=f"✅ Substitutions confirmed: {', '.join(f'{k} → {v}' for k, v in final_subs.items())}"
            )],
            "current_node": "SUBSTITUTION_NEGOTIATOR",
        },
        goto="present_recipe",
    )
