"""
nodes/modification.py — Node 7: MODIFICATION_HANDLER

Parses modification requests and routes accordingly.
Handles: flavor, equipment, scale, ingredient_swap, time
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.types import Command

from config import settings, MODIFICATION_HANDLER_PROMPT
from state import RecipeState, ModificationRequest, ModificationType


def modification_handler_node(state: RecipeState) -> Command:
    """
    Node 7: MODIFICATION_HANDLER

    Parses the modification request from pending_question.
    Routes:
      flavor         → RECIPE_GENERATOR (with flavor feedback)
      equipment      → SUBSTITUTION_NEGOTIATOR (method focus)
      scale          → PRESENT_RECIPE (mathematical adjustment, no LLM)
      ingredient_swap→ RECIPE_GENERATOR
      time           → RECIPE_GENERATOR (with time flag)
    """
    modification_text = state.get("pending_question", "") or ""
    if not modification_text:
        # No modification specified — go back to present
        return Command(
            update={"current_node": "MODIFICATION_HANDLER"},
            goto="present_recipe",
        )

    llm = ChatOpenAI(
        model=settings.model,
        temperature=0.1,
        api_key=settings.openai_api_key,
    )
    structured_llm = llm.with_structured_output(ModificationRequest)

    try:
        mod: ModificationRequest = structured_llm.invoke([
            SystemMessage(content=MODIFICATION_HANDLER_PROMPT),
            HumanMessage(content=f"Modification request: {modification_text}"),
        ])
    except Exception:
        # Default to flavor modification
        mod = ModificationRequest(
            modification_type=ModificationType.FLAVOR,
            specific_request=modification_text,
            intensity="moderate",
        )

    # ── Scale: pure math, no LLM needed ──
    if mod.modification_type == ModificationType.SCALE:
        factor = mod.scale_factor or 2.0
        rc = state["recipe_candidate"]
        scaled_ingredients = []
        for ing in rc.get("required_ingredients", []):
            # Attempt to scale quantity (simple numeric extraction)
            qty_str = ing.get("quantity", "1")
            try:
                # Extract first number from quantity string
                import re
                nums = re.findall(r"[\d.]+", qty_str)
                if nums:
                    scaled_num = float(nums[0]) * factor
                    new_qty = qty_str.replace(nums[0], f"{scaled_num:.1g}")
                else:
                    new_qty = qty_str
            except Exception:
                new_qty = qty_str
            scaled_ingredients.append({**ing, "quantity": new_qty})

        return Command(
            update={
                "recipe_candidate": {**rc, "required_ingredients": scaled_ingredients},
                "messages": [AIMessage(content=f"📐 Recipe scaled by {factor}x!")],
                "pending_question": None,
                "current_node": "MODIFICATION_HANDLER",
            },
            goto="present_recipe",
        )

    # ── Equipment: route to substitution negotiator ──
    if mod.modification_type == ModificationType.EQUIPMENT:
        equipment = mod.specific_request
        current_equip = state["current_session"].get("equipment_available", [])
        # Parse "no oven" → remove oven, "use stovetop" → add stovetop
        if "no " in equipment.lower():
            item = equipment.lower().replace("no ", "").strip()
            updated_equip = [e for e in current_equip if item not in e.lower()]
        else:
            updated_equip = current_equip + [equipment]

        return Command(
            update={
                "current_session": {**state["current_session"], "equipment_available": updated_equip},
                "messages": [AIMessage(content=f"🔧 Equipment updated: {', '.join(updated_equip)}")],
                "pending_question": None,
                "current_node": "MODIFICATION_HANDLER",
            },
            goto="substitution_negotiator",
        )

    # ── Flavor / Ingredient swap / Time → RECIPE_GENERATOR ──
    flavor_feedback = None
    if mod.modification_type == ModificationType.FLAVOR:
        flavor_feedback = f"Flavor adjustment ({mod.intensity}): {mod.specific_request}"
    elif mod.modification_type == ModificationType.INGREDIENT_SWAP:
        flavor_feedback = f"Ingredient swap: {mod.specific_request}"
    elif mod.modification_type == ModificationType.TIME:
        flavor_feedback = f"Time modification: {mod.specific_request}"
        # Try to parse new time limit
        import re
        nums = re.findall(r"\d+", mod.specific_request)
        if nums:
            new_time = int(nums[0])
            return Command(
                update={
                    "current_session": {**state["current_session"], "time_limit": new_time},
                    "user_feedback": f"MODIFY: {mod.specific_request}",
                    "messages": [AIMessage(content=f"⏱ Adjusting for {new_time} minute limit...")],
                    "pending_question": None,
                    "current_node": "MODIFICATION_HANDLER",
                },
                goto="recipe_generator",
            )

    return Command(
        update={
            "user_feedback": f"MODIFY: {flavor_feedback}",
            "messages": [AIMessage(content=f"✏️ Got it — {flavor_feedback}. Finding a better match...")],
            "pending_question": None,
            "current_node": "MODIFICATION_HANDLER",
        },
        goto="recipe_generator",
    )
