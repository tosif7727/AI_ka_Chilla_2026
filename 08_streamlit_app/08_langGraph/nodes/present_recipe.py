"""
nodes/present_recipe.py — Node 6: PRESENT_RECIPE (Interrupt Point)

Formats and presents the recipe with visual structure.
Provides "You might also like" from persistent memory.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage
from langgraph.types import interrupt, Command

from config import settings, InterruptType
from state import RecipeState
from memory import PersistentMemory


def _format_recipe_display(rc: dict, similar: list[dict]) -> str:
    """Format recipe as a rich text string for CLI display."""
    name = rc.get("name", "Recipe")
    total_time = rc.get("total_time", "?")
    difficulty = rc.get("difficulty", "intermediate")
    confidence = rc.get("confidence_score", 0)
    tags = rc.get("flavor_profile_tags", [])
    chef_notes = rc.get("chef_notes", "")
    subs = rc.get("substitutions", {})

    lines = [
        f"\n{'═' * 60}",
        f"  🍽️  {name}",
        f"{'═' * 60}",
        f"  ⏱  {total_time} min  │  👨‍🍳 {difficulty}  │  ✓ {confidence:.0%} confidence",
        f"  🏷  {' · '.join(tags) if tags else 'comfort food'}",
        f"{'─' * 60}",
        "  INGREDIENTS",
    ]

    for ing in rc.get("required_ingredients", []):
        icon = "✓" if ing.get("available") else "⚠️ "
        lines.append(f"  {icon}  {ing.get('quantity', '')} {ing.get('name', '')}")

    for original, substitute in subs.items():
        lines.append(f"  ↻  {substitute} (substituting {original})")

    lines += [f"{'─' * 60}", "  INSTRUCTIONS"]

    for step in rc.get("instructions", []):
        step_num = step.get("step", "?")
        text = step.get("text", "")
        time_m = step.get("time_minutes")
        time_str = f" [{time_m} min]" if time_m else ""
        lines.append(f"  {step_num}. {text}{time_str}")
        if step.get("technique_tip"):
            lines.append(f"     💡 {step['technique_tip']}")

    if chef_notes:
        lines += [f"{'─' * 60}", f"  👨‍🍳 Chef's note: {chef_notes}"]

    if similar:
        lines += [f"{'─' * 60}", "  YOU MIGHT ALSO LIKE"]
        for s in similar[:3]:
            lines.append(f"  • {s.get('name', 'Previous recipe')} (rated {s.get('rating', '?')}/5)")

    lines.append(f"{'═' * 60}")
    return "\n".join(lines)


def present_recipe_node(state: RecipeState) -> Command:
    """
    Node 6: PRESENT_RECIPE

    interrupt() payload:
    {
        "question_type": "recipe_review",
        "content": str (formatted recipe),
        "options": ["start_cooking", "save_for_later", "adjust_recipe", "reject"],
        "state_snapshot": {recipe_candidate}
    }

    Resume with Command(resume={
        "action": "start_cooking" | "save_for_later" | "adjust_recipe" | "reject",
        "modification_request": str  (if adjust_recipe)
    })
    """
    rc = state["recipe_candidate"]
    memory = PersistentMemory(settings.memory_file)

    # Get similar recipes from taste profile
    similar = memory.get_similar_recipes(rc.get("flavor_profile_tags", []), n=3)
    # Filter out current recipe if it's already in history
    similar = [s for s in similar if s.get("name") != rc.get("name")]

    # Format display
    recipe_display = _format_recipe_display(rc, similar)

    # interrupt() — await user decision
    user_response = interrupt({
        "question_type": InterruptType.RECIPE_REVIEW,
        "content": recipe_display,
        "options": ["start_cooking", "save_for_later", "adjust_recipe", "reject"],
        "state_snapshot": {
            "recipe": rc,
            "similar_recipes": similar,
        },
    })

    action = "reject"
    modification_request = ""
    if isinstance(user_response, dict):
        action = user_response.get("action", "reject")
        modification_request = user_response.get("modification_request", "")
    elif isinstance(user_response, str):
        action = user_response

    if action == "start_cooking":
        return Command(
            update={
                "cooking_step_index": 0,
                "messages": [AIMessage(content=f"🍳 Let's cook **{rc.get('name')}**! I'll guide you step by step.")],
                "current_node": "PRESENT_RECIPE",
            },
            goto="cooking_mode",
        )

    elif action == "save_for_later":
        # Save to memory without rating
        recipe_id = memory.add_recipe(
            name=rc.get("name", "Recipe"),
            flavor_tags=rc.get("flavor_profile_tags", []),
            substitutions_used=rc.get("substitutions", {}),
        )
        return Command(
            update={
                "messages": [AIMessage(content=f"💾 Saved **{rc.get('name')}** to your recipe book! (ID: {recipe_id})")],
                "current_node": "PRESENT_RECIPE",
            },
            goto="__end__",
        )

    elif action == "adjust_recipe":
        return Command(
            update={
                "messages": [
                    AIMessage(content=f"✏️ Modifying recipe: {modification_request}"),
                    # Add modification request as a human message for the handler to parse
                ],
                "current_node": "PRESENT_RECIPE",
                "pending_question": modification_request,
            },
            goto="modification_handler",
        )

    else:  # reject
        return Command(
            update={
                "user_feedback": "REJECT",
                "messages": [AIMessage(content="🔄 No problem! Let me try a completely different approach...")],
                "current_node": "PRESENT_RECIPE",
            },
            goto="recipe_generator",
        )
