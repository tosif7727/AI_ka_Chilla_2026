"""
nodes/clarification.py — Node 2: CLARIFICATION (Interrupt Point)

Uses interrupt() to pause execution and surface a clarification question.
On resume, routes back to INTAKE_PARSER with the answer appended to messages.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage
from langgraph.types import interrupt, Command

from state import RecipeState
from config import InterruptType


def clarification_node(state: RecipeState) -> Command:
    """
    Node 2: CLARIFICATION

    Uses interrupt() to pause graph execution.
    Resumes when the runner calls graph.invoke(Command(resume={...}), config).

    Interrupt payload structure:
    {
        "question_type": "clarification",
        "content": str,          # The question to show the user
        "options": None,         # Free-text response expected
        "state_snapshot": dict   # What we've parsed so far
    }
    """
    payload = state.get("interrupt_payload") or {}
    question = payload.get("content") or state.get("pending_question") or \
        "Could you clarify your ingredients? Please list them with approximate quantities."

    # interrupt() pauses graph execution here.
    # The runner receives this payload and can display it to the user.
    # When the user answers, the runner calls:
    #   graph.invoke(Command(resume={"answer": user_answer}), config)
    answer = interrupt({
        "question_type": InterruptType.CLARIFICATION,
        "content": question,
        "options": None,
        "state_snapshot": payload.get("state_snapshot", {}),
    })

    # answer is whatever was passed in Command(resume={"answer": ...})
    user_answer = answer.get("answer", "") if isinstance(answer, dict) else str(answer)

    # Append the clarification answer as a HumanMessage and route back to INTAKE_PARSER
    return Command(
        update={
            "messages": [AIMessage(content=f"Got it! Let me re-analyze with that info: {user_answer}")],
            "flags": {**state["flags"], "needs_clarification": False},
            "pending_question": None,
            "interrupt_payload": None,
            "current_node": "CLARIFICATION",
        },
        goto="intake_parser",
    )
