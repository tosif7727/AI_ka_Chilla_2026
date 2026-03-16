"""
nodes/cooking_mode.py — Node 8: COOKING_MODE (Streaming + Interrupt)

Step-by-step cooking guide with interrupt() at each step.
Supports: next, repeat, help (technique explanation), pause, done.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.types import interrupt, Command

from config import settings, InterruptType
from state import RecipeState


TECHNIQUE_EXPLANATION_PROMPT = """\
You are a patient cooking teacher. The user is mid-recipe and needs a quick technique explanation.
Give a concise (2-3 sentence) practical explanation focused on what they need to do RIGHT NOW.
Be encouraging and specific.\
"""


def _format_step(step: dict, step_num: int, total: int) -> str:
    """Format a single cooking step for display."""
    text = step.get("text", "")
    time_m = step.get("time_minutes")
    tip = step.get("technique_tip", "")

    lines = [
        f"\n{'─' * 50}",
        f"  STEP {step_num} of {total}",
        f"{'─' * 50}",
        f"  {text}",
    ]
    if time_m:
        lines.append(f"\n  ⏱  Timer: {time_m} minute{'s' if time_m > 1 else ''}")
    if tip:
        lines.append(f"  💡 Tip: {tip}")
    lines.append(f"{'─' * 50}")
    lines.append("  [next] Continue  [repeat] Re-read  [help] Technique help  [done] Exit")
    return "\n".join(lines)


def cooking_mode_node(state: RecipeState) -> Command:
    """
    Node 8: COOKING_MODE

    Walks through recipe steps with interrupt() at each one.
    When complete or user exits, routes to FEEDBACK_COLLECTOR.

    interrupt() payload:
    {
        "question_type": "cooking_step",
        "content": str (formatted step),
        "step_index": int,
        "total_steps": int,
        "timer_minutes": int | None
    }

    Resume with Command(resume={
        "action": "next" | "repeat" | "help" | "pause" | "done",
        "help_question": str (optional, for help action)
    })
    """
    rc = state["recipe_candidate"]
    instructions = rc.get("instructions", [])
    total_steps = len(instructions)

    if not instructions:
        return Command(
            update={
                "messages": [AIMessage(content="No instructions found — skipping to feedback.")],
                "current_node": "COOKING_MODE",
            },
            goto="feedback_collector",
        )

    step_index = state.get("cooking_step_index", 0)

    # Loop through steps using interrupt at each
    while step_index < total_steps:
        step = instructions[step_index]
        step_display = _format_step(step, step_index + 1, total_steps)

        user_response = interrupt({
            "question_type": InterruptType.COOKING_STEP,
            "content": step_display,
            "step_index": step_index,
            "total_steps": total_steps,
            "timer_minutes": step.get("time_minutes"),
            "recipe_name": rc.get("name"),
        })

        action = "next"
        help_question = ""
        if isinstance(user_response, dict):
            action = user_response.get("action", "next").lower()
            help_question = user_response.get("help_question", step.get("text", ""))
        elif isinstance(user_response, str):
            action = user_response.lower()

        if action == "done" or action == "exit":
            break

        elif action == "repeat":
            # Stay on same step — loop continues, interrupts again
            continue

        elif action == "help":
            # Get technique explanation from LLM
            llm = ChatOpenAI(
                model=settings.model,
                temperature=0.3,
                api_key=settings.openai_api_key,
            )
            try:
                response = llm.invoke([
                    SystemMessage(content=TECHNIQUE_EXPLANATION_PROMPT),
                    HumanMessage(content=f"Recipe step: {step.get('text', '')}\nUser question: {help_question}"),
                ])
                explanation = response.content
            except Exception:
                explanation = "Focus on the key technique in this step — take it slow and you'll do great!"

            # Show explanation and loop back to same step
            interrupt({
                "question_type": InterruptType.COOKING_STEP,
                "content": f"\n  🎓 TECHNIQUE HELP\n  {'─' * 46}\n  {explanation}\n  {'─' * 46}\n  [next] Got it, continue",
                "step_index": step_index,
                "total_steps": total_steps,
                "timer_minutes": None,
            })
            continue

        else:  # "next" or "pause"
            step_index += 1

    # Cooking complete (or user exited)
    is_complete = step_index >= total_steps
    completion_msg = (
        f"🎉 Amazing! You've finished cooking **{rc.get('name')}**! How did it turn out?"
        if is_complete
        else f"👋 No problem — your {rc.get('name')} recipe is saved for when you're ready."
    )

    return Command(
        update={
            "cooking_step_index": step_index,
            "messages": [AIMessage(content=completion_msg)],
            "current_node": "COOKING_MODE",
        },
        goto="feedback_collector",
    )
