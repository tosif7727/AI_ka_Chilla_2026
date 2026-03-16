"""
graph.py — LangGraph StateGraph Definition

Defines the complete Recipe Rescue Chef graph:
- All 9 nodes registered
- Conditional edges with router functions
- MemorySaver (dev) or SqliteSaver (prod) checkpointing
- Compiled graph with interrupt points

Usage:
    from graph import build_graph, get_checkpointer

    graph = build_graph(use_sqlite=True)  # or False for in-memory
    config = {"configurable": {"thread_id": "user_123_session_1"}}

    # Start session
    result = graph.invoke({"messages": [HumanMessage(content="eggs, garlic, pasta")]}, config)

    # Resume after interrupt
    result = graph.invoke(Command(resume={"action": "start_cooking"}), config)
"""

from __future__ import annotations

from typing import Literal

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

from config import settings, CONFIDENCE_THRESHOLD_PRESENT, CONFIDENCE_THRESHOLD_RESCUE
from state import RecipeState, make_initial_state

from nodes import (
    intake_parser_node,
    clarification_node,
    recipe_generator_node,
    substitution_negotiator_node,
    constraint_rescue_node,
    present_recipe_node,
    modification_handler_node,
    cooking_mode_node,
    feedback_collector_node,
)


# ─────────────────────────────────────────────
# Router functions (conditional edges)
# ─────────────────────────────────────────────

def route_after_intake(
    state: RecipeState,
) -> Literal["clarification", "recipe_generator"]:
    """
    After INTAKE_PARSER:
    - If needs clarification → CLARIFICATION (interrupt)
    - Otherwise → RECIPE_GENERATOR
    """
    if state["flags"].get("needs_clarification"):
        return "clarification"
    return "recipe_generator"


def route_after_generator(
    state: RecipeState,
) -> Literal["present_recipe", "substitution_negotiator", "constraint_rescue"]:
    """
    After RECIPE_GENERATOR:

    Decision tree (in priority order):
    1. Impossible constraints → CONSTRAINT_RESCUE (hard block)
    2. Max iterations reached → CONSTRAINT_RESCUE (loop guard)
    3. Good confidence + no substitutions → PRESENT_RECIPE
    4. Needs substitutions → SUBSTITUTION_NEGOTIATOR
    5. Low confidence fallback → CONSTRAINT_RESCUE
    """
    flags = state["flags"]
    rc = state["recipe_candidate"]
    confidence = rc.get("confidence_score", 0.0)
    iteration = state["iteration_count"]

    # Priority 1: Impossible constraints (allergen conflict, zero viable options)
    if flags.get("impossible_constraints"):
        return "constraint_rescue"

    # Priority 2: Iteration guard — forced rescue after max_iterations
    if iteration >= settings.max_iterations:
        return "constraint_rescue"

    # Priority 3: High confidence, all ingredients available
    if confidence >= CONFIDENCE_THRESHOLD_PRESENT and not flags.get("needs_substitution"):
        return "present_recipe"

    # Priority 4: Good enough but needs substitutions
    if flags.get("needs_substitution") and confidence >= CONFIDENCE_THRESHOLD_RESCUE:
        return "substitution_negotiator"

    # Priority 5: Low confidence → rescue
    return "constraint_rescue"


def route_after_present(
    state: RecipeState,
) -> Literal["cooking_mode", "recipe_generator", "modification_handler", "__end__"]:
    """
    After PRESENT_RECIPE interrupt — routing is handled by Command(goto=...)
    inside the node itself, so this function handles the non-interrupt fallthrough.
    """
    # This edge is a fallthrough safety net.
    # Primary routing happens via Command(goto=...) inside present_recipe_node.
    return "__end__"


# ─────────────────────────────────────────────
# Checkpointer factory
# ─────────────────────────────────────────────

def get_checkpointer(use_sqlite: bool = False):
    """
    Returns the appropriate checkpointer.

    MemorySaver: in-memory, for development/testing
    SqliteSaver: persistent across process restarts, for production

    The checkpointer enables:
    - Conversation resumption after interrupt()
    - Cross-session persistence (when using SqliteSaver)
    - State inspection with graph.get_state(config)
    - History with graph.get_state_history(config)
    """
    if use_sqlite:
        try:
            from langgraph.checkpoint.sqlite import SqliteSaver
            return SqliteSaver.from_conn_string(settings.sqlite_db)
        except ImportError:
            print("⚠️  SqliteSaver not available, falling back to MemorySaver")
    return MemorySaver()


# ─────────────────────────────────────────────
# Graph builder
# ─────────────────────────────────────────────

def build_graph(use_sqlite: bool = False):
    """
    Build and compile the complete Recipe Rescue Chef StateGraph.

    Returns a compiled LangGraph ready for invocation.
    """
    # Initialize StateGraph with our TypedDict schema
    builder = StateGraph(RecipeState)

    # ── Register all nodes ──
    builder.add_node("intake_parser", intake_parser_node)
    builder.add_node("clarification", clarification_node)
    builder.add_node("recipe_generator", recipe_generator_node)
    builder.add_node("substitution_negotiator", substitution_negotiator_node)
    builder.add_node("constraint_rescue", constraint_rescue_node)
    builder.add_node("present_recipe", present_recipe_node)
    builder.add_node("modification_handler", modification_handler_node)
    builder.add_node("cooking_mode", cooking_mode_node)
    builder.add_node("feedback_collector", feedback_collector_node)

    # ── Entry point ──
    builder.add_edge(START, "intake_parser")

    # ── Conditional edge: INTAKE_PARSER → [CLARIFICATION | RECIPE_GENERATOR] ──
    builder.add_conditional_edges(
        "intake_parser",
        route_after_intake,
        {
            "clarification": "clarification",
            "recipe_generator": "recipe_generator",
        },
    )

    # ── CLARIFICATION routes back to INTAKE_PARSER via Command(goto=...) ──
    # (No edge needed — handled inside clarification_node via Command)

    # ── Conditional edge: RECIPE_GENERATOR → [PRESENT | SUBSTITUTION | RESCUE] ──
    builder.add_conditional_edges(
        "recipe_generator",
        route_after_generator,
        {
            "present_recipe": "present_recipe",
            "substitution_negotiator": "substitution_negotiator",
            "constraint_rescue": "constraint_rescue",
        },
    )

    # ── SUBSTITUTION_NEGOTIATOR, CONSTRAINT_RESCUE, PRESENT_RECIPE ──
    # These nodes use Command(goto=...) for dynamic routing after interrupt()
    # No static edges needed — LangGraph handles Command routing automatically

    # ── MODIFICATION_HANDLER routes via Command ──
    # ── COOKING_MODE → FEEDBACK_COLLECTOR ──
    # ── FEEDBACK_COLLECTOR → END ──
    # All handled via Command(goto=...) inside each node

    # ── Compile with checkpointer ──
    checkpointer = get_checkpointer(use_sqlite)
    graph = builder.compile(checkpointer=checkpointer)

    return graph


# ─────────────────────────────────────────────
# Convenience: visualize
# ─────────────────────────────────────────────

def print_graph_mermaid(graph=None) -> str:
    """Print the Mermaid diagram of the graph architecture."""
    if graph is None:
        graph = build_graph()
    try:
        diagram = graph.get_graph().draw_mermaid()
        print(diagram)
        return diagram
    except Exception as e:
        print(f"Visualization not available: {e}")
        return ""


def inspect_state(graph, config: dict) -> None:
    """Debug helper: print current graph state for a thread."""
    try:
        state = graph.get_state(config)
        print(f"\n{'─' * 50}")
        print(f"CURRENT NODE: {state.values.get('current_node', 'unknown')}")
        print(f"ITERATION: {state.values.get('iteration_count', 0)}")
        print(f"FLAGS: {state.values.get('flags', {})}")
        confidence = state.values.get("recipe_candidate", {}).get("confidence_score", 0)
        print(f"CONFIDENCE: {confidence:.0%}")
        print(f"PENDING: {state.next}")
        print(f"{'─' * 50}\n")
    except Exception as e:
        print(f"State inspection error: {e}")
