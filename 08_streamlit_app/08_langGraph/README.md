# Recipe Improviser & Rescue Chef
### Built with LangGraph · OpenAI GPT-4o · Streamlit UI

A conversational AI that transforms random ingredients into viable recipes through iterative refinement, substitution negotiation, and persistent taste learning — fully orchestrated by LangGraph's `StateGraph`.

---

## Architecture

```
INTAKE_PARSER
    │
    ├─[needs_clarification]──► CLARIFICATION (interrupt) ──► INTAKE_PARSER
    │
    └──────────────────────────► RECIPE_GENERATOR
                                        │
                    ┌───────────────────┼──────────────────────┐
                    │                   │                        │
              [confidence≥0.7]   [needs_substitution]   [impossible/iter≥3]
                    │                   │                        │
             PRESENT_RECIPE   SUBSTITUTION_NEGOTIATOR   CONSTRAINT_RESCUE
                    │          (interrupt)                (interrupt)
                    │                   │                        │
              (interrupt)        ├─[accept]──► PRESENT_RECIPE   ├─[simple_meal]──► PRESENT_RECIPE
                    │            └─[reject]──► RECIPE_GENERATOR  ├─[add_items]───► RECIPE_GENERATOR
          ┌─────────┤                                            └─[replan]──────► INTAKE_PARSER
          │         │
    [cook]  [save/reject/modify]
          │         │
    COOKING_MODE  MODIFICATION_HANDLER / END
          │
    FEEDBACK_COLLECTOR ──► (updates persistent_memory) ──► END
```

---

## Installation

```bash
pip install -r requirements.txt
```

## Setup

```bash
cp .env.example .env
# Add your OPENAI_API_KEY to .env
```

## Run

### Streamlit UI (recommended)
```bash
streamlit run streamlit_app.py
```

### CLI (terminal)
```bash
python main.py
```

### Run Tests
```bash
python -m pytest tests/ -v
```

### Visualize Graph
```bash
python visualize.py
```

---

## Project Structure

```
recipe_rescue/
├── streamlit_app.py         # ★ Streamlit UI — main web interface
├── main.py                  # CLI runner
├── graph.py                 # StateGraph definition, compilation, checkpointing
├── state.py                 # TypedDict state schema + Pydantic models
├── config.py                # Settings, prompts (OpenAI GPT-4o), constants
├── visualize.py             # Graph visualization via Mermaid
├── nodes/
│   ├── intake_parser.py     # Node 1: Parse ingredients
│   ├── clarification.py     # Node 2: interrupt() for ambiguous input
│   ├── recipe_generator.py  # Node 3: Generate recipe with confidence scoring
│   ├── substitution.py      # Node 4: interrupt() substitution negotiation
│   ├── constraint_rescue.py # Node 5: interrupt() rescue when impossible
│   ├── present_recipe.py    # Node 6: interrupt() show final recipe
│   ├── modification.py      # Node 7: Handle recipe modifications
│   ├── cooking_mode.py      # Node 8: Step-by-step cooking guide
│   └── feedback.py          # Node 9: Collect feedback + update memory
├── tools/
│   └── recipe_tools.py      # LangChain @tool definitions
├── memory/
│   └── persistent.py        # Long-term memory: taste prefs, recipe history
└── tests/
    ├── test_happy_path.py
    ├── test_substitution.py
    └── test_memory.py
```

## Tech Stack

| Component | Library |
|---|---|
| Graph orchestration | `langgraph` StateGraph |
| LLM | OpenAI `gpt-4o` via `langchain-openai` |
| Human-in-the-loop | `langgraph.types.interrupt` + `Command(resume=...)` |
| Checkpointing | `MemorySaver` (dev) / `SqliteSaver` (prod) |
| Structured output | `llm.with_structured_output(PydanticModel)` |
| Tool calling | `llm.bind_tools(ALL_RECIPE_TOOLS)` |
| UI | `streamlit` |
| Memory | JSON file (swap to Chroma/Pinecone for vectors) |
