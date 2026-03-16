"""
main.py — Interactive CLI Runner for Recipe Rescue Chef

Handles the human-in-the-loop flow:
1. Invoke graph with user message
2. Check for __interrupt__ in result
3. Display interrupt payload and collect user input
4. Resume via Command(resume={...})
5. Repeat until END
"""

from __future__ import annotations

import json
import sys
import uuid
from typing import Any

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from graph import build_graph, inspect_state
from state import make_initial_state
from memory import PersistentMemory
from config import settings, InterruptType, THICK_DIVIDER, DIVIDER


# ─────────────────────────────────────────────
# Interrupt handlers — one per question_type
# ─────────────────────────────────────────────

def handle_clarification(payload: dict) -> dict:
    """Present clarification question and collect free-text answer."""
    print(f"\n{'─' * 50}")
    print(f"  🤔 QUESTION")
    print(f"{'─' * 50}")
    print(f"  {payload.get('content', 'Could you clarify?')}")
    print(f"{'─' * 50}")
    answer = input("  Your answer: ").strip()
    return {"answer": answer}


def handle_substitution_choice(payload: dict) -> dict:
    """Present substitution options and collect user choices."""
    print(f"\n{'─' * 50}")
    print(f"  ⚗️  SUBSTITUTIONS NEEDED")
    print(f"{'─' * 50}")
    print(f"  {payload.get('content', '')}")
    print()

    substitutions = payload.get("substitutions", {})
    for ingredient, sub_data in substitutions.items():
        print(f"  Missing: {ingredient} ({sub_data.get('purpose', 'ingredient')})")
        opt_a = sub_data.get("option_a", {})
        opt_b = sub_data.get("option_b", {})
        avail_a = "✓ available" if opt_a.get("available") else "⚠ need to buy"
        avail_b = "✓ available" if opt_b.get("available") else "⚠ need to buy"
        print(f"    A) {opt_a.get('ingredient', '?')} ({opt_a.get('ratio', '')}) — {avail_a}")
        print(f"       Trade-offs: {opt_a.get('trade_offs', '')}")
        print(f"    B) {opt_b.get('ingredient', '?')} ({opt_b.get('ratio', '')}) — {avail_b}")
        print(f"       Trade-offs: {opt_b.get('trade_offs', '')}")
        print()

    print("  Options:")
    print("    [1] Accept all (use Option A for each)")
    print("    [2] Reject — try a different recipe")
    print("    [3] Custom — choose per ingredient")
    print(f"{'─' * 50}")

    choice = input("  Your choice (1/2/3): ").strip()

    if choice == "1":
        return {"choice": "accept_all"}
    elif choice == "3":
        accepted = {}
        for ingredient, sub_data in substitutions.items():
            opt_a = sub_data.get("option_a", {})
            opt_b = sub_data.get("option_b", {})
            ing_choice = input(
                f"  For '{ingredient}': [A] {opt_a.get('ingredient')} or [B] {opt_b.get('ingredient')}? "
            ).strip().upper()
            if ing_choice == "B":
                accepted[ingredient] = opt_b.get("ingredient", opt_a.get("ingredient", ""))
            else:
                accepted[ingredient] = opt_a.get("ingredient", "")
        return {"choice": "custom", "accepted_substitutions": accepted}
    else:
        return {"choice": "reject_all"}


def handle_rescue_option(payload: dict) -> dict:
    """Present constraint rescue options."""
    print(f"\n{'─' * 50}")
    print(f"  🆘 RECIPE RESCUE")
    print(f"{'─' * 50}")
    print(f"  {payload.get('content', 'No viable recipe found.')}")
    if payload.get("bottleneck"):
        print(f"  ⚡ Issue: {payload['bottleneck']}")
    print()

    paths = payload.get("rescue_paths", [])
    for i, path in enumerate(paths, 1):
        print(f"  [{i}] {path.get('title', path.get('id', '?'))}")
        print(f"      {path.get('description', '')}")
        if path.get("additions"):
            print(f"      → Add: {', '.join(path['additions'])}")
        print()

    print(f"{'─' * 50}")
    choice_str = input(f"  Choose (1-{len(paths)}): ").strip()

    try:
        idx = int(choice_str) - 1
        if 0 <= idx < len(paths):
            return {"path": paths[idx]["id"]}
    except ValueError:
        pass
    return {"path": "simple_meal"}  # default


def handle_recipe_review(payload: dict) -> dict:
    """Display recipe and collect user action."""
    print(payload.get("content", "Recipe ready!"))
    print()
    print("  What would you like to do?")
    print("    [1] Start cooking 🍳")
    print("    [2] Save for later 💾")
    print("    [3] Adjust recipe ✏️")
    print("    [4] Try a different recipe 🔄")
    print(f"{'─' * 50}")

    choice = input("  Your choice (1/2/3/4): ").strip()

    if choice == "1":
        return {"action": "start_cooking"}
    elif choice == "2":
        return {"action": "save_for_later"}
    elif choice == "3":
        mod = input("  What would you like to change? ").strip()
        return {"action": "adjust_recipe", "modification_request": mod}
    else:
        return {"action": "reject"}


def handle_cooking_step(payload: dict) -> dict:
    """Display cooking step and collect navigation action."""
    print(payload.get("content", ""))

    action_raw = input("  > ").strip().lower()

    if action_raw in ("h", "help", "?"):
        question = input("  What technique help do you need? ").strip()
        return {"action": "help", "help_question": question}
    elif action_raw in ("r", "repeat", "again"):
        return {"action": "repeat"}
    elif action_raw in ("q", "quit", "done", "exit"):
        return {"action": "done"}
    else:
        return {"action": "next"}


def handle_feedback(payload: dict) -> dict:
    """Collect recipe feedback."""
    print(f"\n{'─' * 50}")
    print(f"  ⭐ RECIPE FEEDBACK")
    print(f"{'─' * 50}")
    print(f"  {payload.get('content', 'How was it?')}")
    print()

    rating_str = input("  Rating (1-5 stars): ").strip()
    try:
        rating = max(1, min(5, int(rating_str)))
    except ValueError:
        rating = 3

    again_str = input("  Would you make it again? (y/n): ").strip().lower()
    would_make_again = again_str in ("y", "yes", "1", "true")

    notes = input("  Any notes? (press Enter to skip): ").strip()

    print(f"{'─' * 50}")
    return {
        "rating": rating,
        "would_make_again": would_make_again,
        "taste_notes": notes,
        "substitution_evaluations": {},
    }


# ─────────────────────────────────────────────
# Interrupt dispatcher
# ─────────────────────────────────────────────

INTERRUPT_HANDLERS = {
    InterruptType.CLARIFICATION: handle_clarification,
    InterruptType.SUBSTITUTION_CHOICE: handle_substitution_choice,
    InterruptType.RESCUE_OPTION: handle_rescue_option,
    InterruptType.RECIPE_REVIEW: handle_recipe_review,
    InterruptType.COOKING_STEP: handle_cooking_step,
    InterruptType.FEEDBACK: handle_feedback,
}


def dispatch_interrupt(interrupt_data: dict) -> dict:
    """Route interrupt to the appropriate handler."""
    question_type = interrupt_data.get("question_type", "")
    handler = INTERRUPT_HANDLERS.get(question_type)
    if handler:
        return handler(interrupt_data)
    # Generic fallback
    print(f"\n  [{question_type.upper()}] {interrupt_data.get('content', '')}")
    response = input("  Response: ").strip()
    return {"answer": response}


# ─────────────────────────────────────────────
# Main session runner
# ─────────────────────────────────────────────

def run_session(thread_id: str | None = None, use_sqlite: bool = True) -> None:
    """
    Run a complete Recipe Rescue Chef session.

    Args:
        thread_id: Unique session ID. If None, generates a new one.
                   Reuse the same thread_id to resume an interrupted session.
        use_sqlite: Use SqliteSaver for cross-session persistence.
    """
    if thread_id is None:
        thread_id = f"{settings.thread_id_prefix}_{uuid.uuid4().hex[:8]}"

    config = {"configurable": {"thread_id": thread_id}}

    print(THICK_DIVIDER)
    print("  🍳  RECIPE RESCUE CHEF")
    print("  Powered by LangGraph · Claude Sonnet")
    print(THICK_DIVIDER)
    print(f"  Session: {thread_id}")
    print(f"  Type 'quit' to exit at any prompt.")
    print(THICK_DIVIDER)

    # Build graph
    graph = build_graph(use_sqlite=use_sqlite)

    # Load existing memory if available
    memory = PersistentMemory(settings.memory_file)
    initial_state = make_initial_state(persistent_memory=memory.as_dict())

    # Get initial user input
    print()
    user_input = input("  What ingredients do you have? Tell me everything!\n  > ").strip()
    if user_input.lower() in ("quit", "exit", "q"):
        print("  Goodbye! 👋")
        return

    # Add as HumanMessage to state
    initial_state["messages"] = [HumanMessage(content=user_input)]

    # ── Main graph loop ──
    result = graph.invoke(initial_state, config)

    while True:
        # Check if graph is done
        current_state = graph.get_state(config)
        if not current_state.next:
            # Graph reached END
            print(f"\n{THICK_DIVIDER}")
            print("  Session complete! Your memory has been updated.")
            print(f"  History: {memory.get_history_summary()}")
            print(THICK_DIVIDER)
            break

        # Check for interrupts
        interrupts = current_state.tasks
        has_interrupt = any(
            hasattr(task, "interrupts") and task.interrupts
            for task in (interrupts or [])
        )

        if not has_interrupt:
            # Graph is paused but no interrupt — shouldn't happen normally
            print("  [Graph paused with no interrupt — this is unexpected]")
            if settings.debug:
                inspect_state(graph, config)
            break

        # Find interrupt payload
        interrupt_payload = None
        for task in (interrupts or []):
            if hasattr(task, "interrupts") and task.interrupts:
                for intr in task.interrupts:
                    if hasattr(intr, "value"):
                        interrupt_payload = intr.value
                        break
                if interrupt_payload:
                    break

        if interrupt_payload is None:
            # Fallback: check state directly
            interrupt_payload = current_state.values.get("interrupt_payload", {})

        if settings.debug:
            inspect_state(graph, config)

        # Dispatch to appropriate handler
        resume_data = dispatch_interrupt(interrupt_payload or {})

        # Check for quit at any prompt
        if isinstance(resume_data, dict) and resume_data.get("answer", "").lower() in ("quit", "exit"):
            print("  Goodbye! 👋")
            break

        # Resume graph with user response
        result = graph.invoke(Command(resume=resume_data), config)


# ─────────────────────────────────────────────
# Multi-session manager
# ─────────────────────────────────────────────

def list_sessions() -> None:
    """List recent sessions from memory."""
    memory = PersistentMemory(settings.memory_file)
    history = memory._data.get("recipe_history", [])
    if not history:
        print("No sessions found.")
        return
    print(f"\n{'─' * 50}")
    print("  RECIPE HISTORY")
    print(f"{'─' * 50}")
    for entry in history[-10:]:  # Last 10
        rating = "⭐" * (entry.get("rating") or 0) or "unrated"
        print(f"  {entry['timestamp'][:10]}  {entry['name']:<30} {rating}")
    print(f"{'─' * 50}")
    print(f"  {memory.get_history_summary()}")


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Recipe Rescue Chef — LangGraph")
    parser.add_argument("--thread", "-t", help="Resume a specific thread ID")
    parser.add_argument("--history", action="store_true", help="Show recipe history")
    parser.add_argument("--no-sqlite", action="store_true", help="Use in-memory checkpointer")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    args = parser.parse_args()

    if args.debug:
        settings.debug = True

    if args.history:
        list_sessions()
        sys.exit(0)

    run_session(
        thread_id=args.thread,
        use_sqlite=not args.no_sqlite,
    )
