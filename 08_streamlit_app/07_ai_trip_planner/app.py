"""
Autonomous Task Planner — supports OpenAI and Ollama.
Usage:
    python planner.py --provider openai  "Plan a 3-day Pakistan trip under $1000"
    python planner.py --provider ollama  "Build a mobile app MVP"
"""

import os, json, argparse
from dotenv import load_dotenv
load_dotenv()  # loads .env file automatically
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser


# ── Pydantic Models ────────────────────────────────────────────────────────────

class AgentType(str, Enum):
    ResearchAgent = "ResearchAgent"
    CalcAgent     = "CalcAgent"
    CreativeAgent = "CreativeAgent"
    VerifyAgent   = "VerifyAgent"

class InputAnalysis(BaseModel):
    goal:             str
    hard_constraints: list[str]
    soft_preferences: list[str]
    success_criteria: list[str]

class SubTask(BaseModel):
    task_id:          str
    description:      str
    agent_type:       AgentType
    tools:            list[str]
    dependencies:     list[str] = Field(default_factory=list)
    expected_output:  str
    validation_rules: list[str]
    parallel_group:   int

class SynthesisPlan(BaseModel):
    final_output_format: str
    compilation_logic:   str
    fallback_strategy:   str

class ExecutionPlan(BaseModel):
    input_analysis:  InputAnalysis
    execution_graph: list[SubTask]
    synthesis_plan:  SynthesisPlan
    risk_flags:      list[str]


# ── Prompts ────────────────────────────────────────────────────────────────────

PLANNER_PROMPT = """You are an expert autonomous task planner. Decompose the user request into a structured execution plan.

Agent types:
- ResearchAgent: search/APIs  (tools: web_search, api_fetch, scraper)
- CalcAgent: math/budgeting   (tools: calculator, optimizer, spreadsheet)
- CreativeAgent: synthesis    (tools: text_generator, scheduler, formatter)
- VerifyAgent: validation     (tools: constraint_checker, fact_verifier, validator)

STRICT RULES:
1. PARALLEL GROUPS: Tasks with no deps = group 1. Each dependency layer increments the group. NEVER assign all tasks to group 1.
2. VALIDATION RULES: Every task needs at least 1 specific rule. Rules MUST be plain strings, NOT objects.
3. Always include a CreativeAgent task to compile the final document/itinerary.
4. Final task must always be VerifyAgent.
5. Generate 5-7 tasks total.
6. hard_constraints, soft_preferences, success_criteria, and validation_rules MUST ALL be arrays of plain strings.
7. NEVER use objects in these arrays. For example: "Total budget under $1000" is correct, {{"key":"budget","value":"1000"}} is WRONG.

EXAMPLE JSON OUTPUT:
{{
  "input_analysis": {{
    "goal": "Plan a 3-day trip to Pakistan under $1000",
    "hard_constraints": [
      "Total spend must not exceed $1000",
      "All flights must depart from my city",
      "Trip duration: exactly 3 days"
    ],
    "soft_preferences": [
      "Prefer budget hotels",
      "Include local food experiences",
      "Minimize travel time between locations"
    ],
    "success_criteria": [
      "Complete itinerary with daily schedule",
      "Budget breakdown showing all costs",
      "Hotel and flight recommendations"
    ]
  }},
  "execution_graph": [
    {{
      "task_id": "T1",
      "description": "Research flight options and prices",
      "agent_type": "ResearchAgent",
      "tools": ["web_search", "api_fetch"],
      "dependencies": [],
      "expected_output": "List of 3+ flights with prices from my city to Pakistan",
      "validation_rules": [
        "At least 3 different airlines or options",
        "Prices must be realistic for this route",
        "All flights must depart from my city"
      ],
      "parallel_group": 1
    }}
  ],
  "synthesis_plan": {{
    "final_output_format": "Markdown document with itinerary, budget table, and recommendations",
    "compilation_logic": "Combine all agent outputs into a cohesive travel guide",
    "fallback_strategy": "Use placeholder data if any agent fails"
  }},
  "risk_flags": [
    "Visa processing may take time for Pakistan",
    "Budget is tight, limited room for contingencies"
  ]
}}

Respond ONLY with valid JSON (no markdown, no extra text)."""


REPORT_PROMPT = """You are a professional travel/project consultant. Write a comprehensive, detailed Markdown report.

CRITICAL BUDGET RULE: The TOTAL of ALL costs in the budget table MUST NOT exceed {budget}. 
Every price you write (flights, hotels, food, activities) must be realistic AND sum to under {budget}.
If needed, pick cheaper options — but never exceed the budget. This is non-negotiable.

# {title}

## 📋 Trip Overview
- Goal, duration, total budget ({budget}), travel style

## ✈️ Flights & Transport
- Departure city: {origin}
- Compare at least 3 airlines/services flying from {origin} with estimated ticket prices
- Cheapest vs best value option
- Booking tips (when to buy, which sites)

## 🏨 Accommodation
- 3 specific hotels/guesthouses: name, area, price/night, star rating, why recommended

## 📍 Locations to Visit
- Each place: what it is, entry fee, best time to visit, how many hours to spend

## 🗓️ Day-by-Day Itinerary
- Day 1 / Day 2 / Day 3 with Morning / Afternoon / Evening breakdown
- Include transport between spots and estimated travel time

## 🍽️ Food & Dining
- 3 must-try local dishes with price range
- 3 recommended restaurants/food spots with location and cost

## 💰 Budget Breakdown
| Category | Estimated Cost |
|----------|---------------|
| Flights |  |
| Accommodation |  |
| Activities & Entry Fees |  |
| Food & Dining |  |
| Local Transport |  |
| Misc / Buffer |  |
| **TOTAL** | **** |

NOTE: TOTAL must be under {budget}. Double-check before writing.

## ⚠️ Risks & Mitigation
- Each risk with a specific actionable tip

## ✅ Packing Checklist
- Items specific to this destination and trip type

Be specific. Use real place names. All costs must be realistic and within budget.

Execution Plan JSON:
{plan_json}"""


# ── LLM Factory ───────────────────────────────────────────────────────────────

def get_llm(provider: str, model: str | None):
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise SystemExit(
                "❌  OPENAI_API_KEY not found.\n"
                "    Add it to your .env file:\n"
                "        OPENAI_API_KEY=sk-proj-xxxxxxxx\n"
                "    Then run again.\n"
            )
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model or "gpt-4o-mini", api_key=api_key, temperature=0.3)
    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=model or "llama3.2",
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0.3,
        )
    raise ValueError(f"Unknown provider '{provider}'. Choose: openai | ollama")


# ── Planner ────────────────────────────────────────────────────────────────────

class AutonomousTaskPlanner:
    def __init__(self, provider: str = "openai", model: str | None = None):
        self.llm = get_llm(provider, model)

        self.plan_chain = (
            ChatPromptTemplate.from_messages([
                ("system", PLANNER_PROMPT),
                ("human",  "User request: {request}\nDeparture city: {origin}\n\nGenerate ExecutionPlan JSON. All flights must depart from {origin}."),
            ])
            | self.llm
            | JsonOutputParser(pydantic_object=ExecutionPlan)
        )

        self.report_chain = (
            ChatPromptTemplate.from_messages([("human", REPORT_PROMPT)])
            | self.llm
            | StrOutputParser()
        )

    def plan(self, request: str, origin: str = "my city") -> ExecutionPlan:
        safe = request.replace("$", "USD ")
        raw  = self.plan_chain.invoke({"request": safe, "origin": origin})
        
        if raw is None:
            raise ValueError("❌ LLM returned None for execution plan. The response may not be valid JSON.")
        
        if not isinstance(raw, dict):
            raise ValueError(f"❌ LLM returned invalid format: {type(raw).__name__}. Expected dict. Got: {raw}")
        
        # Post-process: convert any dict items in string arrays to strings
        raw = self._clean_plan_json(raw)
        
        return ExecutionPlan(**raw)

    @staticmethod
    def _clean_plan_json(plan_dict: dict) -> dict:
        """Convert dict items in string arrays to plain strings."""
        # Clean hard_constraints, soft_preferences, success_criteria
        for key in ["hard_constraints", "soft_preferences", "success_criteria"]:
            if key in plan_dict.get("input_analysis", {}):
                arr = plan_dict["input_analysis"][key]
                plan_dict["input_analysis"][key] = [
                    item.get("value", str(item)) if isinstance(item, dict) else str(item)
                    for item in arr
                ]
        
        # Clean validation_rules for each task
        if "execution_graph" in plan_dict:
            for task in plan_dict["execution_graph"]:
                if "validation_rules" in task:
                    rules = task["validation_rules"]
                    task["validation_rules"] = [
                        rule.get("value", str(rule)) if isinstance(rule, dict) else str(rule)
                        for rule in rules
                    ]
        
        return plan_dict

    def generate_report(self, plan: ExecutionPlan, title: str, origin: str = "my city") -> str:
        """Second LLM call — turns execution plan into a rich markdown report."""
        # Extract budget from hard constraints e.g. "Total spend <= USD 1000"
        import re
        budget = "the stated budget"
        for c in plan.input_analysis.hard_constraints:
            match = re.search(r"USD\s*([\d,]+)", c, re.IGNORECASE)
            if match:
                budget = f"${match.group(1)}"
                break
        return self.report_chain.invoke({
            "title":     title,
            "plan_json": plan.model_dump_json(indent=2),
            "budget":    budget,
            "origin":    origin,
        })

    def run(self, request: str, origin: str = "my city") -> tuple[ExecutionPlan, str]:
        """Full pipeline: plan → display → simulate → report → save."""
        print("\n⚙️  Step 1/3 — Generating execution plan…")
        plan = self.plan(request, origin)
        _display(plan, request, origin)

        print("⚙️  Step 2/3 — Simulating agent execution…")
        SimulatedExecutor().execute(plan)

        print("⚙️  Step 3/3 — Generating detailed markdown report…")
        report = self.generate_report(plan, request, origin)

        _save(plan, report, request)
        return plan, report


# ── Pretty Printer ─────────────────────────────────────────────────────────────

COLORS = {
    "ResearchAgent": "\033[96m", "CalcAgent": "\033[93m",
    "CreativeAgent": "\033[95m", "VerifyAgent": "\033[92m",
}
B, R, RED = "\033[1m", "\033[0m", "\033[91m"

def _display(plan: ExecutionPlan, request: str, origin: str = ""):
    print(f"\n{B}{'═'*60}{R}")
    print(f"{B}  EXECUTION PLAN{R}")
    print(f"{'═'*60}")
    print(f"{B}Request:{R} {request}")
    if origin:
        print(f"{B}From   :{R} {origin}")
    print()

    a = plan.input_analysis
    print(f"{B}📋 INPUT ANALYSIS{R}")
    print(f"  Goal        : {a.goal}")
    print(f"  Constraints : {', '.join(a.hard_constraints)}")
    print(f"  Preferences : {', '.join(a.soft_preferences)}")
    print(f"  Criteria    : {', '.join(a.success_criteria)}")

    print(f"\n{B}🔗 EXECUTION GRAPH{R}")
    cur = 0
    for t in sorted(plan.execution_graph, key=lambda x: (x.parallel_group, x.task_id)):
        if t.parallel_group != cur:
            cur = t.parallel_group
            count = sum(1 for x in plan.execution_graph if x.parallel_group == cur)
            print(f"\n  {B}── Group {cur}  ({count} task{'s' if count > 1 else ''}) ──{R}")
        c   = COLORS.get(t.agent_type, R)
        dep = f"deps={t.dependencies}" if t.dependencies else "no deps"
        print(f"  {c}{B}{t.task_id}{R} [{c}{t.agent_type}{R}] {dep}")
        print(f"     {t.description}")
        print(f"     Tools : {', '.join(t.tools)}")
        print(f"     Rules : {' | '.join(t.validation_rules)}")

    s = plan.synthesis_plan
    print(f"\n{B}🧩 SYNTHESIS{R}")
    print(f"  Format   : {s.final_output_format}")
    print(f"  Fallback : {s.fallback_strategy}")

    if plan.risk_flags:
        print(f"\n{B}{RED}⚠  RISKS{R}")
        for f in plan.risk_flags:
            print(f"  • {f}")
    print(f"\n{'═'*60}\n")


# ── Simulated Executor ─────────────────────────────────────────────────────────

class SimulatedExecutor:
    def execute(self, plan: ExecutionPlan) -> dict:
        import time, random
        groups: dict[int, list] = {}
        for t in plan.execution_graph:
            groups.setdefault(t.parallel_group, []).append(t)

        results = {}
        for gid in sorted(groups):
            tasks = groups[gid]
            print(f"  ▶ Group {gid}: {[t.task_id for t in tasks]}")
            with ThreadPoolExecutor(max_workers=len(tasks)) as pool:
                futures = {pool.submit(self._run, t): t for t in tasks}
                for fut in as_completed(futures):
                    t = futures[fut]
                    results[t.task_id] = fut.result()
                    print(f"    ✔ {t.task_id} ({t.agent_type})")
        print(f"\n✅ Simulation complete.\n")
        return results

    def _run(self, task: SubTask) -> str:
        import time, random
        time.sleep(random.uniform(0.05, 0.2))
        return f"[{task.agent_type}] {task.expected_output}"


# ── File Saver ─────────────────────────────────────────────────────────────────

def _save(plan: ExecutionPlan, report: str, request: str):
    from pathlib import Path
    from datetime import datetime

    # Build slug from request
    slug = "_".join(request.lower().split()[:6])
    slug = "".join(c if c.isalnum() or c == "_" else "" for c in slug)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create folder: outputs/<slug>_<timestamp>/
    folder = Path("outputs") / f"{slug}_{timestamp}"
    folder.mkdir(parents=True, exist_ok=True)

    # Save JSON plan
    json_path = folder / "execution_plan.json"
    json_path.write_text(plan.model_dump_json(indent=2), encoding="utf-8")

    # Save markdown report
    if report:
        md_path = folder / "report.md"
        md_path.write_text(report, encoding="utf-8")
        print(f"📋 Report         → {md_path}")

    print(f"📄 Execution plan → {json_path}")
    print(f"📁 Output folder  → {folder}/\n")


# ── CLI ────────────────────────────────────────────────────────────────────────

def _ask(prompt: str, fallback: str) -> str:
    """Ask user a question, return fallback if empty."""
    val = input(prompt).strip()
    return val if val else fallback


def main():
    parser = argparse.ArgumentParser(description="Autonomous Task Planner")
    parser.add_argument("--provider",  default="openai", choices=["openai", "ollama"])
    parser.add_argument("--model",     default=None)
    parser.add_argument("--from",      dest="origin",      default=None, help="Departure city")
    parser.add_argument("--to",        dest="destination", default=None, help="Destination city/country")
    parser.add_argument("--days",      dest="days",        default=None, help="Number of days")
    parser.add_argument("--budget",    dest="budget",      default=None, help="Total budget e.g. 1000")
    parser.add_argument("--plan-only", action="store_true", help="Skip report, only generate execution plan")
    args = parser.parse_args()

    print(f"\n{'─'*50}")
    print("  🌍  AUTONOMOUS TRIP PLANNER")
    print(f"{'─'*50}\n")

    # Collect all inputs interactively if not passed as flags
    destination = args.destination or _ask("📍 Where do you want to travel TO?   : ", "Pakistan")
    origin      = args.origin      or _ask("✈️  Where are you traveling FROM?     : ", "my city")
    days        = args.days        or _ask("🗓️  How many days?                    : ", "3")
    budget      = args.budget      or _ask("💰 What is your total budget (USD)?  : ", "1000")

    # Validate days and budget are numbers
    try:
        days = str(int(days))
    except ValueError:
        print("⚠️  Invalid days value, defaulting to 3.")
        days = "3"
    try:
        budget = str(int(budget))
    except ValueError:
        print("⚠️  Invalid budget value, defaulting to 1000.")
        budget = "1000"

    # Build the natural language request
    request = f"Plan a {days}-day trip to {destination} under USD {budget}"

    print(f"\n{'─'*50}")
    print(f"  Request : {request}")
    print(f"  From    : {origin}")
    print(f"{'─'*50}\n")

    planner = AutonomousTaskPlanner(provider=args.provider, model=args.model)

    if args.plan_only:
        plan = planner.plan(request, origin)
        _display(plan, request, origin)
        SimulatedExecutor().execute(plan)
        _save(plan, "", request)
    else:
        planner.run(request, origin)

if __name__ == "__main__":
    main()