"""
visualize.py — Generate Mermaid diagram of the Recipe Rescue Chef graph.

Usage:
    python visualize.py
    python visualize.py --save graph.md
"""

from __future__ import annotations

import argparse
from graph import build_graph


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--save", help="Save Mermaid diagram to file")
    args = parser.parse_args()

    graph = build_graph(use_sqlite=False)

    print("\n📊 Recipe Rescue Chef — LangGraph Architecture\n")

    try:
        diagram = graph.get_graph().draw_mermaid()
        print(diagram)

        if args.save:
            with open(args.save, "w") as f:
                f.write(f"```mermaid\n{diagram}\n```\n")
            print(f"\n✅ Saved to {args.save}")

    except Exception as e:
        # Fallback: print the manual architecture
        print(f"Auto-visualization error: {e}")
        print("\nManual architecture diagram:\n")
        print(MANUAL_MERMAID)


MANUAL_MERMAID = """
stateDiagram-v2
    [*] --> INTAKE_PARSER
    INTAKE_PARSER --> CLARIFICATION : needs_clarification
    INTAKE_PARSER --> RECIPE_GENERATOR : parsed_ok
    CLARIFICATION --> INTAKE_PARSER : interrupt_resume
    RECIPE_GENERATOR --> PRESENT_RECIPE : confidence≥0.7 & no_subs
    RECIPE_GENERATOR --> SUBSTITUTION_NEGOTIATOR : needs_substitution
    RECIPE_GENERATOR --> CONSTRAINT_RESCUE : impossible | iter≥3 | low_confidence
    SUBSTITUTION_NEGOTIATOR --> PRESENT_RECIPE : accepted_subs
    SUBSTITUTION_NEGOTIATOR --> RECIPE_GENERATOR : rejected
    CONSTRAINT_RESCUE --> RECIPE_GENERATOR : add_ingredients | simple_meal
    CONSTRAINT_RESCUE --> INTAKE_PARSER : replan
    PRESENT_RECIPE --> COOKING_MODE : start_cooking
    PRESENT_RECIPE --> [*] : save_for_later
    PRESENT_RECIPE --> MODIFICATION_HANDLER : adjust_recipe
    PRESENT_RECIPE --> RECIPE_GENERATOR : reject
    MODIFICATION_HANDLER --> RECIPE_GENERATOR : flavor | ingredient_swap | time
    MODIFICATION_HANDLER --> SUBSTITUTION_NEGOTIATOR : equipment
    MODIFICATION_HANDLER --> PRESENT_RECIPE : scale
    COOKING_MODE --> FEEDBACK_COLLECTOR : complete | exit
    FEEDBACK_COLLECTOR --> [*] : updates_memory
"""

if __name__ == "__main__":
    main()
