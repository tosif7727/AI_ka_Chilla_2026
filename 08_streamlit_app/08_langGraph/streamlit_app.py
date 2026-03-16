"""
streamlit_app.py — Recipe Rescue Chef · Streamlit UI

Full human-in-the-loop Streamlit interface for the LangGraph Recipe Rescue Chef.
Handles all interrupt types with polished UI components.

Run with:
    streamlit run streamlit_app.py
"""

from __future__ import annotations

import sys
import os
import uuid
import json

import streamlit as st
from langchain_core.messages import HumanMessage
from langgraph.types import Command

# ── path setup so we can import from the project root ──
sys.path.insert(0, os.path.dirname(__file__))

from graph import build_graph
from state import make_initial_state
from memory.persistent import PersistentMemory
from config import settings, InterruptType

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Recipe Rescue Chef",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@300;400;500;600&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
  }

  /* Dark warm background */
  .stApp {
    background: #0f0e0c;
    color: #e8dcc8;
  }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background: #130f0b !important;
    border-right: 1px solid #2a2010;
  }
  [data-testid="stSidebar"] * { color: #c8b898 !important; }

  /* Main header */
  .chef-header {
    font-family: 'Playfair Display', serif;
    font-size: 2.4rem;
    font-weight: 700;
    color: #f5deb3;
    letter-spacing: -0.02em;
    line-height: 1.1;
  }
  .chef-sub {
    font-size: 0.78rem;
    color: #7a6e5f;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 4px;
  }

  /* Cards */
  .card {
    background: #1a1712;
    border: 1px solid #2a2620;
    border-radius: 12px;
    padding: 20px 24px;
    margin: 12px 0;
  }
  .card-accent {
    border-left: 3px solid #e67e22;
  }
  .card-success {
    border-left: 3px solid #3d7a35;
    background: #141a12;
  }
  .card-warning {
    border-left: 3px solid #c0392b;
    background: #1a1210;
  }
  .card-info {
    border-left: 3px solid #2060c0;
    background: #10121a;
  }

  /* Recipe title */
  .recipe-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.6rem;
    font-weight: 700;
    color: #f5deb3;
    margin-bottom: 6px;
  }

  /* Node badge */
  .node-badge {
    display: inline-block;
    padding: 3px 10px;
    background: #1e1a16;
    border: 1px solid #3a3020;
    border-radius: 20px;
    font-size: 0.7rem;
    color: #c0a875;
    letter-spacing: 0.1em;
    text-transform: uppercase;
  }

  /* Ingredient chips */
  .ing-available { color: #5db855; font-weight: 500; }
  .ing-missing   { color: #e07050; font-weight: 500; }
  .ing-sub       { color: #c0a875; font-weight: 500; }

  /* Confidence bar */
  .conf-bar-wrap {
    background: #2a2620;
    border-radius: 6px;
    height: 8px;
    margin: 6px 0 12px;
    overflow: hidden;
  }
  .conf-bar {
    height: 8px;
    border-radius: 6px;
    transition: width 0.4s ease;
  }

  /* Step progress */
  .step-done   { opacity: 0.4; }
  .step-active { color: #e67e22; font-weight: 600; }

  /* Divider */
  .divider {
    border: none;
    border-top: 1px solid #2a2620;
    margin: 16px 0;
  }

  /* Message bubbles */
  .msg-human {
    background: #1e1810;
    border: 1px solid #3a2a10;
    border-radius: 12px 12px 4px 12px;
    padding: 10px 16px;
    color: #f0e0c0;
    margin: 6px 0 6px 20%;
    font-size: 0.9rem;
  }
  .msg-ai {
    background: #141210;
    border: 1px solid #2a2620;
    border-radius: 12px 12px 12px 4px;
    padding: 10px 16px;
    color: #c8b898;
    margin: 6px 20% 6px 0;
    font-size: 0.9rem;
  }

  /* Stacked input row */
  .stButton > button {
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
  }

  /* Hide Streamlit branding */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 1.5rem !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Session state init
# ─────────────────────────────────────────────

def _init_session():
    if "graph" not in st.session_state:
        st.session_state.graph = build_graph(use_sqlite=False)
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = f"session_{uuid.uuid4().hex[:8]}"
    if "graph_config" not in st.session_state:
        st.session_state.graph_config = {
            "configurable": {"thread_id": st.session_state.thread_id}
        }
    if "messages" not in st.session_state:
        st.session_state.messages = []   # display chat history
    if "phase" not in st.session_state:
        st.session_state.phase = "input"   # input | thinking | interrupt | done
    if "interrupt_data" not in st.session_state:
        st.session_state.interrupt_data = None
    if "current_node" not in st.session_state:
        st.session_state.current_node = "IDLE"
    if "recipe" not in st.session_state:
        st.session_state.recipe = None
    if "cooking_step" not in st.session_state:
        st.session_state.cooking_step = 0
    if "memory" not in st.session_state:
        st.session_state.memory = PersistentMemory(settings.memory_file)
    if "profile_set" not in st.session_state:
        st.session_state.profile_set = False
    if "initial_profile" not in st.session_state:
        st.session_state.initial_profile = {}


_init_session()


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def add_message(role: str, content: str):
    st.session_state.messages.append({"role": role, "content": content})


def get_interrupt_payload() -> dict | None:
    """Extract interrupt payload from current graph state."""
    try:
        graph_state = st.session_state.graph.get_state(st.session_state.graph_config)
        for task in (graph_state.tasks or []):
            if hasattr(task, "interrupts") and task.interrupts:
                for intr in task.interrupts:
                    if hasattr(intr, "value"):
                        return intr.value
        # Fallback to state value
        return graph_state.values.get("interrupt_payload")
    except Exception:
        return None


def run_graph(initial_state: dict | None = None, resume_data: dict | None = None):
    """Invoke or resume the LangGraph graph."""
    with st.spinner("🍳 Chef is thinking..."):
        try:
            if resume_data is not None:
                result = st.session_state.graph.invoke(
                    Command(resume=resume_data),
                    st.session_state.graph_config,
                )
            else:
                result = st.session_state.graph.invoke(
                    initial_state,
                    st.session_state.graph_config,
                )

            # Update node tracking
            graph_state = st.session_state.graph.get_state(st.session_state.graph_config)
            st.session_state.current_node = (
                graph_state.values.get("current_node", "IDLE") if graph_state else "IDLE"
            )

            # Check if done or interrupted
            if graph_state and graph_state.next:
                # Still running — check for interrupt
                payload = get_interrupt_payload()
                if payload:
                    st.session_state.interrupt_data = payload
                    st.session_state.phase = "interrupt"
                    # Update recipe if available
                    rc = graph_state.values.get("recipe_candidate", {})
                    if rc.get("name"):
                        st.session_state.recipe = rc
                else:
                    st.session_state.phase = "thinking"
            else:
                # Graph finished
                st.session_state.phase = "done"
                st.session_state.interrupt_data = None
                if graph_state:
                    rc = graph_state.values.get("recipe_candidate", {})
                    if rc.get("name"):
                        st.session_state.recipe = rc

        except Exception as e:
            st.error(f"Graph error: {e}")
            st.session_state.phase = "input"


def reset_session():
    """Start a new cooking session, keeping memory and profile."""
    old_memory = st.session_state.memory
    old_profile = st.session_state.initial_profile
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    _init_session()
    st.session_state.memory = old_memory
    st.session_state.initial_profile = old_profile
    st.session_state.profile_set = bool(old_profile)


# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown('<div class="chef-header" style="font-size:1.4rem;">🍳 Recipe Rescue</div>', unsafe_allow_html=True)
    st.markdown('<div class="chef-sub">LangGraph · OpenAI GPT-4o</div>', unsafe_allow_html=True)
    st.markdown("---")

    # Node indicator
    node_colors = {
        "INTAKE_PARSER": "#3d7a35",
        "RECIPE_GENERATOR": "#c0a875",
        "SUBSTITUTION_NEGOTIATOR": "#6080c0",
        "CONSTRAINT_RESCUE": "#c0392b",
        "PRESENT_RECIPE": "#e67e22",
        "COOKING_MODE": "#5ab0c0",
        "FEEDBACK_COLLECTOR": "#9060c0",
        "CLARIFICATION": "#60a070",
        "IDLE": "#3a3020",
    }
    current = st.session_state.current_node
    color = node_colors.get(current, "#3a3020")
    st.markdown(
        f'<div style="margin-bottom:12px;">'
        f'<div style="font-size:0.65rem;color:#5a5040;text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px;">Active Node</div>'
        f'<div style="display:flex;align-items:center;gap:8px;">'
        f'<div style="width:10px;height:10px;border-radius:50%;background:{color};box-shadow:0 0 6px {color};"></div>'
        f'<span style="font-size:0.8rem;color:{color};font-weight:600;">{current}</span>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    # Graph flow visualization
    st.markdown("**Graph Flow**")
    nodes_order = [
        ("INTAKE_PARSER", "📥"),
        ("CLARIFICATION", "🤔"),
        ("RECIPE_GENERATOR", "🧑‍🍳"),
        ("SUBSTITUTION_NEGOTIATOR", "⚗️"),
        ("CONSTRAINT_RESCUE", "🆘"),
        ("PRESENT_RECIPE", "🍽️"),
        ("COOKING_MODE", "🔥"),
        ("FEEDBACK_COLLECTOR", "⭐"),
    ]
    for node_name, icon in nodes_order:
        c = node_colors.get(node_name, "#3a3020")
        is_active = node_name == current
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;padding:3px 0;opacity:{"1" if is_active else "0.45"};">'
            f'<div style="width:6px;height:6px;border-radius:50%;background:{c};{"box-shadow:0 0 5px "+c+";" if is_active else ""}"></div>'
            f'<span style="font-size:0.75rem;color:{c if is_active else "#6a5a4a"};">{icon} {node_name}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Profile settings
    with st.expander("👤 My Profile", expanded=not st.session_state.profile_set):
        dietary = st.multiselect(
            "Dietary restrictions",
            ["vegetarian", "vegan", "gluten-free", "dairy-free", "keto", "halal", "kosher"],
            default=st.session_state.initial_profile.get("dietary_restrictions", []),
            key="sidebar_dietary",
        )
        allergies_input = st.text_input(
            "Allergies (comma-separated)",
            value=", ".join(st.session_state.initial_profile.get("allergies", [])),
            placeholder="nuts, shellfish...",
            key="sidebar_allergies",
        )
        skill = st.select_slider(
            "Skill level",
            options=["beginner", "intermediate", "advanced"],
            value=st.session_state.initial_profile.get("skill_level", "intermediate"),
            key="sidebar_skill",
        )
        spice = st.select_slider(
            "Spice tolerance",
            options=["mild", "medium", "hot", "very_hot"],
            value=st.session_state.initial_profile.get("spice_tolerance", "medium"),
            key="sidebar_spice",
        )
        if st.button("Save Profile", use_container_width=True):
            st.session_state.initial_profile = {
                "dietary_restrictions": dietary,
                "allergies": [a.strip() for a in allergies_input.split(",") if a.strip()],
                "skill_level": skill,
                "spice_tolerance": spice,
            }
            st.session_state.profile_set = True
            st.success("Profile saved!")

    st.markdown("---")

    # Memory / history
    history = st.session_state.memory._data.get("recipe_history", [])
    if history:
        st.markdown(f"**📚 Recipe History** ({len(history)})")
        for entry in reversed(history[-5:]):
            rating = "⭐" * (entry.get("rating") or 0) or "—"
            st.markdown(
                f'<div style="font-size:0.75rem;padding:4px 0;border-bottom:1px solid #2a2620;">'
                f'<span style="color:#c8b898;">{entry["name"][:28]}</span><br>'
                f'<span style="color:#6a5a4a;">{rating} · {entry["timestamp"][:10]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.caption(f"Session: `{st.session_state.thread_id}`")
    if st.button("🔄 New Session", use_container_width=True):
        reset_session()
        st.rerun()


# ─────────────────────────────────────────────
# Main layout
# ─────────────────────────────────────────────

col_main, col_info = st.columns([3, 1])

with col_main:
    # Header
    st.markdown(
        '<div class="chef-header">Recipe Rescue Chef 🍳</div>'
        '<div class="chef-sub">Powered by LangGraph · OpenAI GPT-4o · Human-in-the-Loop</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ── Chat messages ──
    if st.session_state.messages:
        for msg in st.session_state.messages:
            cls = "msg-human" if msg["role"] == "human" else "msg-ai"
            icon = "👤" if msg["role"] == "human" else "🍳"
            st.markdown(
                f'<div class="{cls}">{icon} {msg["content"]}</div>',
                unsafe_allow_html=True,
            )

    # ══════════════════════════════════════════
    # PHASE: INPUT
    # ══════════════════════════════════════════
    if st.session_state.phase == "input":
        if not st.session_state.messages:
            st.markdown(
                '<div class="card" style="text-align:center;padding:32px;">'
                '<div style="font-size:3rem;margin-bottom:12px;">🥘</div>'
                '<div style="font-family:Playfair Display,serif;font-size:1.3rem;color:#f5deb3;margin-bottom:8px;">What\'s in your kitchen?</div>'
                '<div style="color:#7a6e5f;font-size:0.9rem;line-height:1.7;">Tell me your ingredients, time constraints, and dietary needs.<br>I\'ll rescue a meal from whatever you\'ve got.</div>'
                '</div>',
                unsafe_allow_html=True,
            )
            # Example prompts
            st.markdown("**Try an example:**")
            ex_cols = st.columns(3)
            examples = [
                "eggs, cheese, spinach, 20 min",
                "chicken, garlic, pasta, no dairy",
                "flour, butter, sugar, eggs — baking!",
            ]
            for i, ex in enumerate(examples):
                with ex_cols[i]:
                    if st.button(ex, key=f"ex_{i}", use_container_width=True):
                        st.session_state["prefill"] = ex
                        st.rerun()

        with st.form("ingredient_form", clear_on_submit=True):
            prefill = st.session_state.pop("prefill", "")
            user_input = st.text_area(
                "Your ingredients & constraints",
                value=prefill,
                placeholder="e.g. 2 chicken breasts, garlic, pasta, olive oil, 30 minutes, no dairy...",
                height=100,
                label_visibility="collapsed",
            )
            submitted = st.form_submit_button("🍳 Find Me a Recipe", use_container_width=True)

        if submitted and user_input.strip():
            add_message("human", user_input.strip())
            add_message("ai", "🔍 Parsing your ingredients and generating a recipe...")
            st.session_state.phase = "thinking"

            # Build initial state
            profile = st.session_state.initial_profile
            initial_state = make_initial_state(
                dietary_restrictions=profile.get("dietary_restrictions", []),
                allergies=profile.get("allergies", []),
                skill_level=profile.get("skill_level", "intermediate"),
                spice_tolerance=profile.get("spice_tolerance", "medium"),
                persistent_memory=st.session_state.memory.as_dict(),
            )
            initial_state["messages"] = [HumanMessage(content=user_input.strip())]
            run_graph(initial_state=initial_state)
            st.rerun()

    # ══════════════════════════════════════════
    # PHASE: INTERRUPT — dispatch to handlers
    # ══════════════════════════════════════════
    elif st.session_state.phase == "interrupt" and st.session_state.interrupt_data:
        idata = st.session_state.interrupt_data
        qtype = idata.get("question_type", "")

        # ── CLARIFICATION ──
        if qtype == InterruptType.CLARIFICATION:
            st.markdown(
                f'<div class="card card-info">'
                f'<div style="color:#6090d0;font-size:0.75rem;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px;">🤔 Clarification Needed</div>'
                f'<div style="color:#c8b898;font-size:0.95rem;">{idata.get("content","")}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            with st.form("clarify_form", clear_on_submit=True):
                answer = st.text_input("Your answer", placeholder="Type your answer here...")
                if st.form_submit_button("Send →", use_container_width=True):
                    add_message("human", answer)
                    add_message("ai", "Got it! Re-analyzing with that information...")
                    run_graph(resume_data={"answer": answer})
                    st.rerun()

        # ── SUBSTITUTION CHOICE ──
        elif qtype == InterruptType.SUBSTITUTION_CHOICE:
            st.markdown(
                f'<div class="card card-accent">'
                f'<div style="color:#e67e22;font-size:0.75rem;text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px;">⚗️ Substitution Options</div>'
                f'<div style="color:#c8b898;">{idata.get("content","")}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            subs = idata.get("substitutions", {})
            user_choices = {}

            for ingredient, sub_data in subs.items():
                st.markdown(f"**Missing: `{ingredient}`** — *{sub_data.get('purpose', '')}*")
                opt_a = sub_data.get("option_a", {})
                opt_b = sub_data.get("option_b", {})

                sub_cols = st.columns(2)
                with sub_cols[0]:
                    avail_a = "✅ Available" if opt_a.get("available") else "🛒 Need to buy"
                    st.markdown(
                        f'<div class="card" style="padding:14px;">'
                        f'<div style="color:#f5deb3;font-weight:600;margin-bottom:4px;">A · {opt_a.get("ingredient","")}</div>'
                        f'<div style="color:#7a6e5f;font-size:0.8rem;">{opt_a.get("ratio","")}</div>'
                        f'<div style="color:#a09080;font-size:0.8rem;margin-top:4px;">{opt_a.get("trade_offs","")}</div>'
                        f'<div style="font-size:0.75rem;margin-top:6px;">{avail_a}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with sub_cols[1]:
                    avail_b = "✅ Available" if opt_b.get("available") else "🛒 Need to buy"
                    st.markdown(
                        f'<div class="card" style="padding:14px;">'
                        f'<div style="color:#f5deb3;font-weight:600;margin-bottom:4px;">B · {opt_b.get("ingredient","")}</div>'
                        f'<div style="color:#7a6e5f;font-size:0.8rem;">{opt_b.get("ratio","")}</div>'
                        f'<div style="color:#a09080;font-size:0.8rem;margin-top:4px;">{opt_b.get("trade_offs","")}</div>'
                        f'<div style="font-size:0.75rem;margin-top:6px;">{avail_b}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                choice = st.radio(
                    f"Choose for {ingredient}",
                    options=[f"A — {opt_a.get('ingredient','?')}", f"B — {opt_b.get('ingredient','?')}"],
                    key=f"sub_choice_{ingredient}",
                    horizontal=True,
                    label_visibility="collapsed",
                )
                user_choices[ingredient] = opt_a.get("ingredient") if choice.startswith("A") else opt_b.get("ingredient")

            btn_cols = st.columns([2, 1])
            with btn_cols[0]:
                if st.button("✅ Confirm Substitutions & Continue", use_container_width=True):
                    add_message("ai", f"Substitutions confirmed: {', '.join(f'{k}→{v}' for k,v in user_choices.items())}")
                    run_graph(resume_data={"choice": "custom", "accepted_substitutions": user_choices})
                    st.rerun()
            with btn_cols[1]:
                if st.button("🔄 Try Different Recipe", use_container_width=True):
                    add_message("ai", "Looking for a recipe that better matches what you have...")
                    run_graph(resume_data={"choice": "reject_all"})
                    st.rerun()

        # ── CONSTRAINT RESCUE ──
        elif qtype == InterruptType.RESCUE_OPTION:
            st.markdown(
                f'<div class="card card-warning">'
                f'<div style="color:#c0392b;font-size:0.75rem;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px;">🆘 Recipe Rescue</div>'
                f'<div style="color:#d4c9b5;font-size:0.95rem;line-height:1.6;">{idata.get("content","")}</div>'
                + (f'<div style="color:#c0392b;font-size:0.8rem;margin-top:8px;">⚡ Issue: {idata["bottleneck"]}</div>' if idata.get("bottleneck") else "")
                + f'</div>',
                unsafe_allow_html=True,
            )

            paths = idata.get("rescue_paths", [])
            path_icons = {"add_ingredients": "🛒", "simple_meal": "🥄", "replan": "🔄"}
            path_cols = st.columns(len(paths))
            for i, path in enumerate(paths):
                with path_cols[i]:
                    icon = path_icons.get(path.get("id", ""), "•")
                    additions = path.get("additions", [])
                    additions_html = (
                        f'<div style="color:#c0a875;font-size:0.78rem;margin-top:6px;">+ {", ".join(additions)}</div>'
                        if additions else ""
                    )
                    st.markdown(
                        f'<div class="card" style="padding:16px;cursor:pointer;">'
                        f'<div style="font-size:1.4rem;margin-bottom:6px;">{icon}</div>'
                        f'<div style="color:#f5deb3;font-weight:600;font-size:0.9rem;">{path.get("title","")}</div>'
                        f'<div style="color:#7a6e5f;font-size:0.8rem;margin-top:4px;line-height:1.5;">{path.get("description","")}</div>'
                        f'{additions_html}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    if st.button(f"Choose: {path.get('title','')}", key=f"rescue_{i}", use_container_width=True):
                        add_message("ai", f"Chosen: {path.get('title','')} — {path.get('description','')}")
                        run_graph(resume_data={"path": path.get("id", "simple_meal")})
                        st.rerun()

        # ── RECIPE REVIEW ──
        elif qtype == InterruptType.RECIPE_REVIEW:
            rc = st.session_state.recipe or {}
            if not rc:
                # Try to get from interrupt snapshot
                rc = idata.get("state_snapshot", {}).get("recipe", {})

            if rc:
                confidence = rc.get("confidence_score", 0)
                conf_color = "#5db855" if confidence >= 0.8 else "#e0c060" if confidence >= 0.6 else "#e07050"

                st.markdown(f'<div class="recipe-title">{rc.get("name","Recipe")}</div>', unsafe_allow_html=True)

                meta_cols = st.columns(4)
                with meta_cols[0]:
                    st.metric("⏱ Time", f'{rc.get("total_time","?")} min')
                with meta_cols[1]:
                    st.metric("👨‍🍳 Difficulty", rc.get("difficulty","?").title())
                with meta_cols[2]:
                    st.metric("✓ Confidence", f'{confidence:.0%}')
                with meta_cols[3]:
                    tags = rc.get("flavor_profile_tags", [])
                    st.metric("🏷 Tags", ", ".join(tags[:2]) if tags else "—")

                # Confidence bar
                bar_w = int(confidence * 100)
                st.markdown(
                    f'<div class="conf-bar-wrap"><div class="conf-bar" style="width:{bar_w}%;background:{conf_color};"></div></div>',
                    unsafe_allow_html=True,
                )

                # Ingredients + Instructions side by side
                ing_col, inst_col = st.columns([1, 1])

                with ing_col:
                    st.markdown("**Ingredients**")
                    for ing in rc.get("required_ingredients", []):
                        icon = "✅" if ing.get("available") else "⚠️"
                        st.markdown(
                            f'<div style="font-size:0.88rem;padding:3px 0;border-bottom:1px solid #1e1a16;">'
                            f'{icon} {ing.get("quantity","")} <span style="color:#f5deb3;">{ing.get("name","")}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    for orig, sub in rc.get("substitutions", {}).items():
                        st.markdown(
                            f'<div style="font-size:0.88rem;padding:3px 0;border-bottom:1px solid #1e1a16;">'
                            f'↻ <span style="color:#c0a875;">{sub}</span> <span style="color:#5a4a30;">for {orig}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                with inst_col:
                    st.markdown("**Instructions**")
                    for step in rc.get("instructions", []):
                        num = step.get("step", "")
                        text = step.get("text", "")
                        mins = step.get("time_minutes")
                        time_str = f' <span style="color:#7a6e5f;font-size:0.78rem;">[{mins}m]</span>' if mins else ""
                        st.markdown(
                            f'<div style="font-size:0.85rem;padding:4px 0;border-bottom:1px solid #1e1a16;">'
                            f'<span style="color:#e67e22;font-weight:600;">{num}.</span> {text}{time_str}'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                if rc.get("chef_notes"):
                    st.markdown(
                        f'<div class="card" style="padding:12px 16px;background:#100e0a;margin-top:8px;">'
                        f'<span style="color:#7a6e5f;">👨‍🍳 </span>'
                        f'<span style="color:#a09080;font-style:italic;font-size:0.88rem;">{rc["chef_notes"]}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            # Action buttons
            st.markdown('<hr class="divider">', unsafe_allow_html=True)
            action_cols = st.columns(4)
            with action_cols[0]:
                if st.button("🍳 Start Cooking", use_container_width=True):
                    add_message("ai", f"Let's cook **{rc.get('name','')}**! I'll guide you step by step.")
                    run_graph(resume_data={"action": "start_cooking"})
                    st.rerun()
            with action_cols[1]:
                if st.button("💾 Save for Later", use_container_width=True):
                    add_message("ai", f"Saved **{rc.get('name','')}** to your recipe book!")
                    run_graph(resume_data={"action": "save_for_later"})
                    st.rerun()
            with action_cols[2]:
                mod_text = st.text_input("Adjustment request", placeholder="Make it spicier, scale to 4 people...", label_visibility="collapsed", key="mod_input")
                if st.button("✏️ Adjust", use_container_width=True) and mod_text:
                    add_message("human", f"Adjust: {mod_text}")
                    add_message("ai", f"Making that change: {mod_text}")
                    run_graph(resume_data={"action": "adjust_recipe", "modification_request": mod_text})
                    st.rerun()
            with action_cols[3]:
                if st.button("🔄 Try Another", use_container_width=True):
                    add_message("ai", "Let me try a completely different approach...")
                    run_graph(resume_data={"action": "reject"})
                    st.rerun()

        # ── COOKING STEP ──
        elif qtype == InterruptType.COOKING_STEP:
            rc = st.session_state.recipe or {}
            instructions = rc.get("instructions", [])
            step_idx = idata.get("step_index", 0)
            total = idata.get("total_steps", len(instructions))
            timer_mins = idata.get("timer_minutes")

            # Progress bar
            st.progress((step_idx) / max(total, 1), text=f"Step {step_idx + 1} of {total}")

            if instructions and step_idx < len(instructions):
                step = instructions[step_idx]
                st.markdown(
                    f'<div class="card card-accent" style="padding:24px;">'
                    f'<div style="color:#e67e22;font-size:0.75rem;text-transform:uppercase;letter-spacing:.1em;margin-bottom:10px;">Step {step_idx+1} of {total}</div>'
                    f'<div style="color:#f5deb3;font-size:1.05rem;line-height:1.7;">{step.get("text","")}</div>'
                    + (f'<div style="color:#c0a875;margin-top:10px;">⏱ Timer: <strong>{timer_mins} minutes</strong></div>' if timer_mins else "")
                    + (f'<div style="color:#7a6e5f;font-size:0.82rem;margin-top:6px;font-style:italic;">💡 {step.get("technique_tip","")}</div>' if step.get("technique_tip") else "")
                    + f'</div>',
                    unsafe_allow_html=True,
                )

            nav_cols = st.columns([1, 1, 2, 1])
            with nav_cols[0]:
                if st.button("← Back", use_container_width=True, disabled=step_idx == 0):
                    run_graph(resume_data={"action": "back"})
                    st.rerun()
            with nav_cols[1]:
                if st.button("🔁 Repeat", use_container_width=True):
                    run_graph(resume_data={"action": "repeat"})
                    st.rerun()
            with nav_cols[2]:
                help_q = st.text_input("Need help?", placeholder="Ask about technique...", label_visibility="collapsed", key="cook_help")
                if st.button("🎓 Get Help", use_container_width=True) and help_q:
                    run_graph(resume_data={"action": "help", "help_question": help_q})
                    st.rerun()
            with nav_cols[3]:
                is_last = step_idx >= total - 1
                label = "🎉 Done!" if is_last else "Next Step →"
                if st.button(label, use_container_width=True):
                    action = "done" if is_last else "next"
                    run_graph(resume_data={"action": action})
                    st.rerun()

        # ── FEEDBACK ──
        elif qtype == InterruptType.FEEDBACK:
            rc = st.session_state.recipe or {}
            st.markdown(
                f'<div class="card card-success" style="padding:20px;">'
                f'<div style="color:#5db855;font-size:0.75rem;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px;">⭐ Recipe Feedback</div>'
                f'<div style="font-family:Playfair Display,serif;font-size:1.2rem;color:#f5deb3;">How did <em>{rc.get("name","it")}</em> turn out?</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            fb_cols = st.columns([1, 1])
            with fb_cols[0]:
                rating = st.slider("Rating", 1, 5, 4, key="fb_rating",
                                   format="%d ⭐")
                again = st.radio("Would you make it again?", ["Yes 👍", "No 👎"],
                                 key="fb_again", horizontal=True)
            with fb_cols[1]:
                notes = st.text_area("Notes (optional)",
                                     placeholder="Too salty, needed more garlic, kids loved it...",
                                     height=100, key="fb_notes")

            if st.button("Submit Feedback & Update Taste Profile 🧠", use_container_width=True):
                would_make_again = again == "Yes 👍"
                add_message("ai", f"{'⭐' * rating} Thanks! Taste profile updated.")
                run_graph(resume_data={
                    "rating": rating,
                    "would_make_again": would_make_again,
                    "taste_notes": notes,
                    "substitution_evaluations": {},
                })
                st.rerun()

    # ══════════════════════════════════════════
    # PHASE: DONE
    # ══════════════════════════════════════════
    elif st.session_state.phase == "done":
        st.markdown(
            '<div class="card card-success" style="text-align:center;padding:32px;">'
            '<div style="font-size:2.5rem;margin-bottom:12px;">✅</div>'
            '<div style="font-family:Playfair Display,serif;font-size:1.3rem;color:#f5deb3;margin-bottom:8px;">Session complete!</div>'
            '<div style="color:#7a6e5f;">Your taste profile has been updated. Next recipe will be even better.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button("🍳 Cook Another Recipe", use_container_width=True):
            reset_session()
            st.rerun()

    # ══════════════════════════════════════════
    # PHASE: THINKING (auto-continue)
    # ══════════════════════════════════════════
    elif st.session_state.phase == "thinking":
        st.info("Processing... please wait.")
        # Check if interrupted now
        payload = get_interrupt_payload()
        if payload:
            st.session_state.interrupt_data = payload
            st.session_state.phase = "interrupt"
            st.rerun()


# ─────────────────────────────────────────────
# Right info column
# ─────────────────────────────────────────────

with col_info:
    st.markdown("### 🧠 Memory")

    # Taste preferences
    taste_prefs = st.session_state.memory._data.get("taste_preferences", {})
    if taste_prefs:
        st.markdown("**Top taste tags**")
        sorted_prefs = sorted(taste_prefs.items(), key=lambda x: x[1], reverse=True)[:6]
        for tag, score in sorted_prefs:
            bar_w = int(score * 100)
            color = "#3d7a35" if score > 0.6 else "#c0a875" if score > 0.4 else "#7a3020"
            st.markdown(
                f'<div style="margin-bottom:6px;">'
                f'<div style="display:flex;justify-content:space-between;font-size:0.78rem;margin-bottom:2px;">'
                f'<span style="color:#c8b898;">{tag}</span><span style="color:{color};">{score:.0%}</span>'
                f'</div>'
                f'<div style="background:#2a2620;border-radius:4px;height:5px;">'
                f'<div style="width:{bar_w}%;height:5px;background:{color};border-radius:4px;"></div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("Cook recipes and rate them to build your taste profile!")

    st.markdown("---")

    # Kitchen staples
    staples = st.session_state.memory._data.get("kitchen_staples", {})
    if staples:
        st.markdown("**Top kitchen staples**")
        top = sorted(staples.items(), key=lambda x: x[1], reverse=True)[:5]
        for name, count in top:
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;font-size:0.8rem;padding:2px 0;">'
                f'<span style="color:#c8b898;">{name}</span>'
                f'<span style="color:#7a6e5f;">×{count}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # Current recipe summary (if any)
    if st.session_state.recipe and st.session_state.recipe.get("name"):
        rc = st.session_state.recipe
        confidence = rc.get("confidence_score", 0)
        color = "#5db855" if confidence >= 0.8 else "#e0c060" if confidence >= 0.6 else "#e07050"
        st.markdown("**Current Recipe**")
        st.markdown(
            f'<div class="card" style="padding:12px;">'
            f'<div style="font-weight:600;color:#f5deb3;font-size:0.9rem;">{rc["name"]}</div>'
            f'<div style="color:{color};font-size:0.8rem;margin-top:4px;">{confidence:.0%} confidence</div>'
            f'<div style="color:#7a6e5f;font-size:0.78rem;">⏱ {rc.get("total_time","?")} min · {rc.get("difficulty","?").title()}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("**How it works**")
    st.markdown(
        '<div style="font-size:0.78rem;color:#6a5a4a;line-height:1.8;">'
        '1. Parse ingredients<br>'
        '2. Generate recipe<br>'
        '3. Negotiate subs<br>'
        '4. Rescue if needed<br>'
        '5. Cook step-by-step<br>'
        '6. Learn your taste'
        '</div>',
        unsafe_allow_html=True,
    )
