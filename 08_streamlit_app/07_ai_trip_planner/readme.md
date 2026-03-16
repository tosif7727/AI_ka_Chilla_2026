# Autonomous Task Planner

Decomposes any natural-language request into a structured, dependency-aware execution plan using specialized LLM agents. Supports **OpenAI** and **Ollama**.

```
User request → Planner LLM → ExecutionPlan (DAG) → Parallel Executor
```

---

## Quick Start

```bash
# 1. Install dependencies
pip install langchain-core pydantic

# 2. Install your provider
pip install langchain-openai      # OpenAI
pip install langchain-ollama      # Ollama (local)

# 3. Set API key
export OPENAI_API_KEY="sk-..."
# Ollama needs no key — just run: ollama serve

# 4. Run
python planner.py "Plan a 3-day Tokyo trip under $1000"
```

---

## Provider Examples

```bash
# OpenAI (default)
python planner.py --provider openai "Launch a SaaS MVP in 90 days"

# Ollama (local, no internet required)
python planner.py --provider ollama --model llama3.2 "Build a mobile app"

# Custom model + skip simulated execution
python planner.py --provider openai --model gpt-4o --no-exec "Write a research paper"
```

---

## Architecture

```
planner.py
├── Pydantic Models       InputAnalysis, SubTask, ExecutionPlan, SynthesisPlan
├── get_llm()             Factory: returns OpenAI / Ollama chat model
├── AutonomousTaskPlanner LangChain chain: prompt | llm | JsonOutputParser
├── SimulatedExecutor     Runs parallel groups via ThreadPoolExecutor
└── CLI (argparse)        --provider, --model, --no-exec
```

### Agent Types

| Agent | Role | Default Tools |
|-------|------|---------------|
| `ResearchAgent` | Search & data gathering | web_search, api_fetch, scraper |
| `CalcAgent` | Math, budgeting, optimization | calculator, optimizer, spreadsheet |
| `CreativeAgent` | Content synthesis & scheduling | text_generator, scheduler, formatter |
| `VerifyAgent` | Constraint validation (always last) | constraint_checker, fact_verifier |

### Execution Graph (DAG)

Tasks are grouped by `parallel_group`. All tasks in the same group run concurrently; groups execute sequentially.

```
Group 1: T1, T2, T3  ──┐
Group 2: T4            ├── sequential groups, parallel within
Group 3: T5            │
Group 4: T6 (Verify) ──┘
```

---

## Output

- **Console**: colored execution graph with agent assignments, dependencies, tools
- **`execution_plan.json`**: full Pydantic model as JSON

---

## Provider Defaults

| Provider | Default Model |
|----------|--------------|
| openai   | `gpt-4o-mini` |
| ollama   | `llama3.2`    |

Override with `--model <name>`.

---

## Extending

Replace `SimulatedExecutor._run_task()` with real LangChain `AgentExecutor` calls to make agents actually use their tools.