"""
nodes/feedback.py — Node 9: FEEDBACK_COLLECTOR (Final Node)

Collects structured feedback and updates persistent_memory:
- Recipe history with rating
- Taste preferences (weighted update)
- Kitchen staples (frequency increment)
- Substitution success rates (Bayesian update)
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.types import interrupt, Command

from config import settings, FEEDBACK_COLLECTOR_PROMPT, InterruptType
from state import RecipeState, FeedbackAnalysis
from memory import PersistentMemory


def feedback_collector_node(state: RecipeState) -> Command:
    """
    Node 9: FEEDBACK_COLLECTOR

    interrupt() payload:
    {
        "question_type": "feedback",
        "content": str,
        "options": {rating: 1-5, would_make_again: bool, taste_notes: str}
    }

    Resume with Command(resume={
        "rating": int,
        "would_make_again": bool,
        "taste_notes": str,
        "substitution_evaluations": {sub_key: float}
    })
    """
    rc = state["recipe_candidate"]

    # Collect feedback via interrupt
    user_response = interrupt({
        "question_type": InterruptType.FEEDBACK,
        "content": (
            f"How did **{rc.get('name', 'the recipe')}** turn out?\n"
            "Please rate it 1-5, and let me know if you'd make it again."
        ),
        "options": {
            "rating": "1-5",
            "would_make_again": "true/false",
            "taste_notes": "optional notes",
            "substitution_evaluations": "optional: rate each sub 0.0-1.0",
        },
        "state_snapshot": {
            "recipe_name": rc.get("name"),
            "substitutions_used": rc.get("substitutions", {}),
        },
    })

    # Parse response
    rating = 3
    would_make_again = True
    taste_notes = ""
    sub_evals = {}

    if isinstance(user_response, dict):
        rating = int(user_response.get("rating", 3))
        would_make_again = bool(user_response.get("would_make_again", True))
        taste_notes = user_response.get("taste_notes", "")
        sub_evals = user_response.get("substitution_evaluations", {})
    elif isinstance(user_response, str):
        # Try to extract rating from string
        import re
        nums = re.findall(r"\b[1-5]\b", user_response)
        if nums:
            rating = int(nums[0])
        taste_notes = user_response

    # Use LLM to extract preference signals from notes
    taste_tags_boost = rc.get("flavor_profile_tags", [])
    taste_tags_penalize = []
    summary = f"Rated {rating}/5"

    if taste_notes:
        llm = ChatOpenAI(
            model=settings.model,
            temperature=0.1,
            api_key=settings.openai_api_key,
        )
        structured_llm = llm.with_structured_output(FeedbackAnalysis)
        try:
            analysis: FeedbackAnalysis = structured_llm.invoke([
                SystemMessage(content=FEEDBACK_COLLECTOR_PROMPT),
                HumanMessage(
                    content=(
                        f"Recipe: {rc.get('name')}\n"
                        f"Rating: {rating}/5\n"
                        f"Would make again: {would_make_again}\n"
                        f"Notes: {taste_notes}\n"
                        f"Flavor tags: {rc.get('flavor_profile_tags', [])}"
                    )
                ),
            ])
            taste_tags_boost = analysis.taste_tags_boost
            taste_tags_penalize = analysis.taste_tags_penalize
            if analysis.substitution_ratings:
                sub_evals = {**sub_evals, **analysis.substitution_ratings}
            summary = analysis.summary
        except Exception:
            pass  # Use defaults

    # ── Update persistent memory ──
    memory = PersistentMemory(settings.memory_file)

    recipe_id = memory.apply_feedback_update(
        recipe_name=rc.get("name", "Unknown Recipe"),
        flavor_tags=rc.get("flavor_profile_tags", []),
        rating=rating,
        would_make_again=would_make_again,
        notes=taste_notes,
        boost_tags=taste_tags_boost,
        penalize_tags=taste_tags_penalize,
        substitution_ratings=sub_evals,
        ingredients_used=state["current_session"].get("available_ingredients", []),
        substitutions_used={k: (v if isinstance(v, str) else str(v)) for k, v in rc.get("substitutions", {}).items()},
    )

    # Build updated persistent_memory for state
    updated_memory = memory.as_dict()

    # Format confirmation message
    stars = "⭐" * rating
    history_summary = memory.get_history_summary()

    confirmation = (
        f"{'─' * 50}\n"
        f"  🧠 MEMORY UPDATED\n"
        f"{'─' * 50}\n"
        f"  Recipe: {rc.get('name')} (ID: {recipe_id})\n"
        f"  Rating: {stars} ({rating}/5)\n"
        f"  Make again: {'Yes ✓' if would_make_again else 'No ✗'}\n"
        f"  Summary: {summary}\n"
        f"  Library: {history_summary}\n"
        f"{'─' * 50}\n"
        f"  Your taste profile has been updated.\n"
        f"  Next recipe recommendations will improve! 🎯\n"
    )

    return Command(
        update={
            "persistent_memory": updated_memory,
            "messages": [AIMessage(content=confirmation)],
            "current_node": "FEEDBACK_COLLECTOR",
        },
        goto="__end__",
    )
