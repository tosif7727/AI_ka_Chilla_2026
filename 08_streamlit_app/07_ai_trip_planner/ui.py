"""
ui.py — Streamlit UI for the Autonomous Trip Planner
------------------------------------------------------
Theme  : Cartographic Luxury — warm parchment, forest green, coral accents
Run    : streamlit run ui.py
Needs  : app.py in the same directory

╔══════════════════════════════════════════════════════════════════════════════╗
║  QUICK REFERENCE: Common Change Points                                       ║
║  ─────────────────────────────────                                           ║
║  • THEME:    Search for [THEME-EDIT] to change colors, fonts, spacing       ║
║  • LAYOUT:   Search for [LAYOUT-EDIT] to adjust column widths, padding      ║
║  • CONTENT:  Search for [CONTENT-EDIT] to modify text, labels, placeholders ║
║  • LOGIC:    Search for [LOGIC-EDIT] to change validation, defaults, flow   ║
║  • STYLING:  Search for [STYLE-EDIT] to tweak CSS without touching tokens   ║
║  • DATA:     Search for [DATA-EDIT] to change destinations, options, lists  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ══════════════════════════════════════════════════════════════════════
# SECTION 1 — IMPORTS
# ══════════════════════════════════════════════════════════════════════
# [LOGIC-EDIT] Add new imports here for additional functionality
# [THEME-EDIT] Import additional font libraries or icon packs here

import streamlit as st
import json, os, traceback
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════
# SECTION 2 — PAGE CONFIG  (must be first Streamlit call)
# ══════════════════════════════════════════════════════════════════════
# [CONTENT-EDIT] Change page_title, page_icon, or layout mode below
# [LAYOUT-EDIT] Adjust initial_sidebar_state: "collapsed", "expanded", or "auto"

st.set_page_config(
    page_title  = "Trip Planner AI",      # [CONTENT-EDIT] Browser tab title
    page_icon   = "🧭",                    # [CONTENT-EDIT] Emoji or path to .ico
    layout      = "wide",                  # [LAYOUT-EDIT] "wide" or "centered"
    initial_sidebar_state = "expanded",   # [LAYOUT-EDIT] Sidebar default state
)

# ══════════════════════════════════════════════════════════════════════
# SECTION 3 — DESIGN TOKENS  (edit here to retheme everything)
# ══════════════════════════════════════════════════════════════════════
# [THEME-EDIT] ════════════════════════════════════════════════════════
# This dictionary controls EVERY visual aspect. Change values here to 
# retheme the entire app instantly. All CSS references these variables.
# 
# COLOR STRATEGY:
#   --bg-*     = Background layers (page → surface → sunken → dark)
#   --tx-*     = Text colors (primary → secondary → dim → invert for dark bg)
#   --ac-*     = Accents (coral=CTA, green=success, gold=highlight)
#   --ag-*     = Agent badge colors (research=blue, calc=gold, etc)
#
# GEOMETRY:
#   --radius   = Corner roundness (increase for softer, decrease for crisp)
#   --shadow-* = Elevation depth (sm=subtle, md=cards, lg=modals)
#
# TYPOGRAPHY:
#   --font-*   = Font families (display=headers, body=UI, mono=code)

TOKENS = {
    # Backgrounds ──────────────────────────────────────────────────────
    # [THEME-EDIT] Adjust warmth/coolness of the parchment aesthetic
    "--bg-page"      : "#F5F0E8",   # warm parchment (main canvas)
    "--bg-surface"   : "#FDFAF4",   # lighter card surface (elevated elements)
    "--bg-sunken"    : "#EDE8DC",   # recessed / input bg (depressed elements)
    "--bg-dark"      : "#1C2B1E",   # deep forest green (sidebar)
    "--bg-dark-2"    : "#243328",   # slightly lighter forest (sidebar inputs)

    # Text ─────────────────────────────────────────────────────────────
    # [THEME-EDIT] Adjust contrast ratios here for accessibility
    "--tx-primary"   : "#1A1F1B",   # near-black on light (headlines)
    "--tx-secondary" : "#5A6655",   # muted green-grey (body text)
    "--tx-dim"       : "#9BA896",   # very muted (placeholders, hints)
    "--tx-invert"    : "#EEF2EA",   # text on dark bg (sidebar text)
    "--tx-invert-dim": "#8DA487",   # muted on dark bg (sidebar labels)

    # Accent ───────────────────────────────────────────────────────────
    # [THEME-EDIT] Primary brand colors — change these for instant rebranding
    "--ac-coral"     : "#D95F3B",   # primary CTA coral (buttons, active tabs)
    "--ac-coral-dim" : "#D95F3B22", # tinted bg (hover states, subtle fills)
    "--ac-coral-mid" : "#D95F3B44", # mid opacity (focus rings, borders)
    "--ac-green"     : "#2D6A4F",   # secondary accent (success, validation)
    "--ac-gold"      : "#C8920A",   # highlight / success banners
    "--ac-gold-dim"  : "#C8920A18", # subtle gold tint

    # Agent colors ─────────────────────────────────────────────────────
    # [THEME-EDIT] Change agent badge colors to match your brand palette
    "--ag-research"  : "#1B7DB8",   # ResearchAgent = blue
    "--ag-calc"      : "#C8920A",   # CalcAgent = gold  
    "--ag-creative"  : "#8B3FA8",   # CreativeAgent = purple
    "--ag-verify"    : "#2D6A4F",   # VerifyAgent = green

    # UI Geometry ──────────────────────────────────────────────────────
    # [THEME-EDIT] Adjust these for denser or more spacious layouts
    "--border"       : "#DDD8CC",   # standard borders
    "--border-dark"  : "#2D3D2F",   # borders on dark backgrounds
    "--radius"       : "8px",       # standard corner radius
    "--radius-lg"    : "14px",      # large corners (cards, modals)
    "--shadow-sm"    : "0 1px 4px rgba(26,31,27,0.08)",   # subtle lift
    "--shadow-md"    : "0 4px 16px rgba(26,31,27,0.12)",  # cards
    "--shadow-lg"    : "0 12px 40px rgba(26,31,27,0.16)", # modals, dropdowns

    # Typography ───────────────────────────────────────────────────────
    # [THEME-EDIT] Change font families (ensure Google Fonts are imported)
    "--font-display" : "'Playfair Display', Georgia, serif",  # Headers
    "--font-body"    : "'Lato', 'Gill Sans', sans-serif",     # UI text
    "--font-mono"    : "'JetBrains Mono', monospace",         # Code, IDs
}

# ══════════════════════════════════════════════════════════════════════
# SECTION 4 — GLOBAL CSS  (all visual rules live here)
# ══════════════════════════════════════════════════════════════════════
# [STYLE-EDIT] ════════════════════════════════════════════════════════
# This function generates all CSS. Modify selectors here to tweak 
# specific components without changing the TOKENS dictionary.
#
# ORGANIZATION:
#   1. CSS Variables injection
#   2. Base reset & Streamlit chrome hiding
#   3. Layout components (sidebar, main content)
#   4. Form elements (inputs, buttons, selects)
#   5. Data display (tabs, metrics, tables, expanders)
#   6. Utilities (scrollbars, focus rings, animations)

def build_css(t: dict) -> str:
    """Build the full CSS string from design tokens."""
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400 ;600;700;900&family=Lato:wght@300;400;700&family=JetBrains+Mono:wght@400;600&display=swap');

/* ── CSS Variables ── */
:root {{
    {''.join(f'{k}: {v};' for k, v in t.items())}
}}

/* ── Base reset ── */
*, *::before, *::after {{ box-sizing: border-box; }}

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {{
    background: var(--bg-page) !important;
    font-family: var(--font-body) !important;
    color: var(--tx-primary) !important;
}}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header,
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] {{ display: none !important; }}

/* ── Main content ── */
.block-container {{
    padding: 0 !important;
    max-width: 100% !important;
}}
section[data-testid="stMain"] > div {{
    padding: 0 !important;
}}

/* ── Sidebar (dark forest) ── */
[data-testid="stSidebar"] {{
    background: var(--bg-dark) !important;
    border-right: 1px solid var(--border-dark) !important;
    min-width: 280px !important;  /* [LAYOUT-EDIT] Sidebar width */
}}
[data-testid="stSidebar"] *:not(button) {{
    color: var(--tx-invert) !important;
}}
[data-testid="stSidebar"] label p {{
    color: var(--tx-invert-dim) !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}}
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] [data-baseweb="select"] {{
    background: var(--bg-dark-2) !important;
    border-color: var(--border-dark) !important;
    color: var(--tx-invert) !important;
}}
[data-testid="stSidebar"] hr {{
    border-color: var(--border-dark) !important;
}}

/* ── Inputs ── */
input, textarea,
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {{
    background: var(--bg-sunken) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--tx-primary) !important;
    font-family: var(--font-body) !important;
    font-size: 0.95rem !important;
    padding: 0.55rem 0.85rem !important;  /* [LAYOUT-EDIT] Input padding */
    transition: border-color 0.18s, box-shadow 0.18s !important;
}}
input:focus, textarea:focus {{
    border-color: var(--ac-green) !important;
    box-shadow: 0 0 0 3px rgba(45,106,79,0.15) !important;
    outline: none !important;
}}

/* ── Labels ── */
label p, [data-testid="stWidgetLabel"] p {{
    color: var(--tx-secondary) !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
    margin-bottom: 4px !important;
}}

/* ── Primary button (coral CTA) ── */
.stButton > button[kind="primary"],
button[data-testid="baseButton-primary"] {{
    background: var(--ac-coral) !important;
    color: #fff !important;
    border: none !important;
    border-radius: var(--radius) !important;
    font-family: var(--font-body) !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.03em !important;
    padding: 0.65rem 2rem !important;  /* [LAYOUT-EDIT] Button padding */
    box-shadow: 0 4px 14px rgba(217,95,59,0.35) !important;
    transition: all 0.18s !important;
}}
.stButton > button[kind="primary"]:hover,
button[data-testid="baseButton-primary"]:hover {{
    background: #C04E2B !important;  /* [THEME-EDIT] Darker coral on hover */
    box-shadow: 0 6px 20px rgba(217,95,59,0.45) !important;
    transform: translateY(-1px) !important;
}}
.stButton > button[kind="primary"]:focus-visible {{
    outline: 3px solid var(--ac-coral) !important;
    outline-offset: 2px !important;
}}

/* ── Secondary button ── */
.stButton > button[kind="secondary"],
button[data-testid="baseButton-secondary"] {{
    background: transparent !important;
    color: var(--tx-secondary) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius) !important;
    font-family: var(--font-body) !important;
    transition: all 0.18s !important;
    box-shadow: none !important;
}}
.stButton > button[kind="secondary"]:hover {{
    border-color: var(--ac-green) !important;
    color: var(--ac-green) !important;
    background: rgba(45,106,79,0.06) !important;
}}

/* ── Tabs ── */
[data-testid="stTabs"] [role="tablist"] {{
    border-bottom: 2px solid var(--border) !important;
    gap: 0 !important;
    background: transparent !important;
}}
[data-testid="stTabs"] [role="tab"] {{
    font-family: var(--font-body) !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    color: var(--tx-dim) !important;
    padding: 0.6rem 1.4rem !important;  /* [LAYOUT-EDIT] Tab padding */
    border-radius: 0 !important;
    transition: all 0.18s !important;
    border-bottom: 2px solid transparent !important;
    margin-bottom: -2px !important;
}}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
    color: var(--ac-coral) !important;
    border-bottom: 2px solid var(--ac-coral) !important;
    background: var(--ac-coral-dim) !important;
}}
[data-testid="stTabs"] [role="tab"]:hover:not([aria-selected="true"]) {{
    color: var(--tx-primary) !important;
    background: var(--bg-sunken) !important;
}}

/* ── Metrics ── */
[data-testid="stMetric"] {{
    background: var(--bg-surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 1rem 1.2rem !important;  /* [LAYOUT-EDIT] Metric card padding */
    box-shadow: var(--shadow-sm) !important;
}}
[data-testid="stMetricValue"] {{
    color: var(--tx-primary) !important;
    font-family: var(--font-display) !important;
    font-size: 1.8rem !important;  /* [STYLE-EDIT] Metric number size */
}}
[data-testid="stMetricLabel"] {{
    color: var(--tx-secondary) !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}}

/* ── Expander ── */
[data-testid="stExpander"] {{
    background: var(--bg-surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    box-shadow: var(--shadow-sm) !important;
}}
[data-testid="stExpander"] summary {{
    color: var(--tx-primary) !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
}}

/* ── Download button ── */
[data-testid="stDownloadButton"] button {{
    background: var(--bg-surface) !important;
    border: 1.5px solid var(--border) !important;
    color: var(--tx-secondary) !important;
    border-radius: var(--radius) !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.04em !important;
    transition: all 0.18s !important;
}}
[data-testid="stDownloadButton"] button:hover {{
    border-color: var(--ac-green) !important;
    color: var(--ac-green) !important;
    background: rgba(45,106,79,0.06) !important;
}}

/* ── Toggle ── */
[data-testid="stToggle"] {{
    accent-color: var(--ac-coral) !important;
}}

/* ── Alerts ── */
[data-testid="stSuccess"] {{
    background: var(--ac-gold-dim) !important;
    border-left: 3px solid var(--ac-gold) !important;
    border-radius: var(--radius) !important;
    color: var(--tx-primary) !important;
}}
[data-testid="stError"] {{
    background: rgba(217,95,59,0.08) !important;
    border-left: 3px solid var(--ac-coral) !important;
    border-radius: var(--radius) !important;
}}
[data-testid="stInfo"] {{
    background: rgba(45,106,79,0.07) !important;
    border-left: 3px solid var(--ac-green) !important;
    border-radius: var(--radius) !important;
}}

/* ── Markdown tables ── */
[data-testid="stMarkdownContainer"] table {{
    border-collapse: collapse !important;
    width: 100% !important;
    font-size: 0.88rem !important;
}}
[data-testid="stMarkdownContainer"] th {{
    background: var(--bg-sunken) !important;
    color: var(--tx-primary) !important;
    font-weight: 700 !important;
    font-size: 0.75rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    padding: 0.6rem 1rem !important;
    border: 1px solid var(--border) !important;
}}
[data-testid="stMarkdownContainer"] td {{
    padding: 0.5rem 1rem !important;
    border: 1px solid var(--border) !important;
    color: var(--tx-primary) !important;
}}
[data-testid="stMarkdownContainer"] tr:nth-child(even) td {{
    background: var(--bg-sunken) !important;
}}
[data-testid="stMarkdownContainer"] code {{
    background: var(--bg-sunken) !important;
    color: var(--ac-green) !important;
    padding: 0.1em 0.4em !important;
    border-radius: 4px !important;
    font-family: var(--font-mono) !important;
    font-size: 0.83em !important;
}}
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {{
    font-family: var(--font-display) !important;
    color: var(--tx-primary) !important;
}}
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {{
    color: var(--tx-secondary) !important;
    line-height: 1.75 !important;  /* [STYLE-EDIT] Paragraph line height */
}}
[data-testid="stMarkdownContainer"] strong {{
    color: var(--tx-primary) !important;
}}

/* ── Number input arrows ── */
[data-testid="stNumberInput"] button {{
    background: var(--bg-sunken) !important;
    border-color: var(--border) !important;
    color: var(--tx-secondary) !important;
}}

/* ── Spinner ── */
[data-testid="stSpinner"] p {{ color: var(--tx-secondary) !important; }}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}  /* [STYLE-EDIT] Scrollbar thickness */
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: var(--tx-dim); }}

/* ── Focus ring (accessibility) ── */
:focus-visible {{
    outline: 2px solid var(--ac-coral) !important;
    outline-offset: 2px !important;
}}

/* ── Selectbox ── */
[data-baseweb="select"] > div {{
    background: var(--bg-sunken) !important;
    border-color: var(--border) !important;
    border-radius: var(--radius) !important;
}}
[data-baseweb="popover"] {{
    background: var(--bg-surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    box-shadow: var(--shadow-lg) !important;
}}
[role="option"]:hover {{
    background: var(--bg-sunken) !important;
}}

</style>
"""


# ══════════════════════════════════════════════════════════════════════
# SECTION 5 — HTML COMPONENTS
# Each function returns an HTML string. Edit markup & inline styles here.
# ══════════════════════════════════════════════════════════════════════
# [CONTENT-EDIT] ═══════════════════════════════════════════════════════
# These functions generate HTML components. Modify text, icons, or 
# structure here. All use inline styles referencing CSS variables.
#
# [STYLE-EDIT] Adjust inline style values (padding, font-size, colors)
# without touching the TOKENS dictionary.

def c_header() -> str:
    """Top page header — logo, title, subtitle."""
    # [CONTENT-EDIT] Change logo emoji, title text, or subtitle below
    # [THEME-EDIT] Adjust gradient colors in logo background
    return """
    <div style="
        background: var(--bg-dark);
        padding: 1.6rem 2.5rem;  /* [LAYOUT-EDIT] Header padding */
        border-bottom: 1px solid var(--border-dark);
        display: flex;
        align-items: center;
        justify-content: space-between;
    ">
        <div style="display:flex;align-items:center;gap:14px;">
            <div style="
                width:42px;height:42px;  /* [LAYOUT-EDIT] Logo size */
                background:linear-gradient(135deg,#D95F3B,#C8920A);  /* [THEME-EDIT] Logo gradient */
                border-radius:10px;
                display:flex;align-items:center;justify-content:center;
                font-size:20px;
                box-shadow:0 4px 14px rgba(217,95,59,0.45);
                flex-shrink:0;
            " role="img" aria-label="compass">🧭</div>  <!-- [CONTENT-EDIT] Logo emoji -->
            <div>
                <h1 style="
                    font-family:var(--font-display);
                    font-size:1.4rem;font-weight:900;  /* [STYLE-EDIT] Title size */
                    color:var(--tx-invert);
                    margin:0;letter-spacing:-0.02em;
                ">Trip Planner <span style='color:#D95F3B;'>AI</span></h1>  <!-- [CONTENT-EDIT] Brand name -->
                <p style="
                    color:var(--tx-invert-dim);
                    font-size:0.75rem;margin:2px 0 0;  /* [STYLE-EDIT] Subtitle size */
                    letter-spacing:0.04em;text-transform:uppercase;
                ">Autonomous multi-agent travel planning</p>  <!-- [CONTENT-EDIT] Tagline -->
            </div>
        </div>
        <div style="display:flex;gap:20px;align-items:center;">
            <span style="color:var(--tx-invert-dim);font-size:0.75rem;letter-spacing:0.05em;">
                Powered by LangChain  <!-- [CONTENT-EDIT] Tech stack label -->
            </span>
        </div>
    </div>
    """


def c_section_title(icon: str, title: str, subtitle: str = "") -> str:
    """Consistent section heading with icon, title, optional subtitle."""
    # [STYLE-EDIT] Adjust spacing, font sizes, or icon sizing here
    sub_html = f'<p style="color:var(--tx-secondary);font-size:0.82rem;margin:3px 0 0;">{subtitle}</p>' if subtitle else ""
    return f"""
    <div style="margin:0 0 1.2rem;">  <!-- [LAYOUT-EDIT] Section margin bottom -->
        <div style="display:flex;align-items:center;gap:10px;">
            <span style="font-size:1.1rem;" role="img" aria-hidden="true">{icon}</span>
            <h2 style="
                font-family:var(--font-display);
                font-size:1.15rem;font-weight:700;  /* [STYLE-EDIT] Section title size */
                color:var(--tx-primary);
                margin:0;letter-spacing:-0.01em;
            ">{title}</h2>
        </div>
        {sub_html}
    </div>
    """


def render_quick_picks(places: list[dict]):
    """
    Quick-pick destination buttons using Streamlit + CSS.
    Avoids JavaScript issues by using session state.
    Shows only flag emoji, text removed for clean UI.
    """
    # [STYLE-EDIT] ═════════════════════════════════════════════════════
    # Modify the CSS below to change quick-pick button appearance
    # without affecting other buttons in the app.
    st.markdown("""
    <style>
    .quick-pick-container {
        margin: 1.8rem 0 1.2rem;  /* [LAYOUT-EDIT] Spacing around quick picks */
    }
    
    .quick-pick-label {
        color: var(--tx-dim);
        font-size: 0.66rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 10px;
    }
    
    .quick-picks {
        display: flex;
        gap: 10px;  /* [LAYOUT-EDIT] Space between quick-pick buttons */
        flex-wrap: wrap;
    }
    
    /* Override Streamlit button styling for quick-picks */
    .stButton > button {
        background: linear-gradient(135deg, var(--bg-surface) 0%, var(--bg-sunken) 100%) !important;
        border: 1.5px solid var(--border) !important;
        border-radius: 26px !important;  /* [STYLE-EDIT] Pill shape roundness */
        padding: 12px 16px !important;   /* [LAYOUT-EDIT] Button padding */
        font-size: 1.4rem !important;    /* [STYLE-EDIT] Emoji size */
        font-weight: 700 !important;
        color: var(--tx-secondary) !important;
        transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
        box-shadow: 0 3px 12px rgba(26, 31, 27, 0.1) !important;
        white-space: nowrap !important;
        min-width: 50px !important;
        height: 50px !important;         /* [LAYOUT-EDIT] Fixed button height */
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #d95f3b22 0%, rgba(217, 95, 59, 0.08) 100%) !important;
        border-color: var(--ac-coral) !important;
        color: var(--ac-coral) !important;
        transform: translateY(-4px) scale(1.08) !important;  /* [STYLE-EDIT] Hover lift amount */
        box-shadow: 0 10px 28px rgba(217, 95, 59, 0.3) !important;
    }
    
    .stButton > button:active {
        transform: translateY(-2px) scale(0.96) !important;
        box-shadow: 0 5px 16px rgba(217, 95, 59, 0.2) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # [CONTENT-EDIT] Change the label text below
    st.markdown(
        '<div class="quick-pick-label">✦ FEATURED DESTINATIONS</div>',
        unsafe_allow_html=True
    )

    # [LAYOUT-EDIT] Adjust column layout logic here if needed
    cols = st.columns(len(places), gap="small")
    for i, p in enumerate(places):
        with cols[i]:
            if st.button(
                p['flag'],  # Only flag emoji displayed
                key=f"qp_{p['dest']}_{p['from']}",
                use_container_width=True,
                help=f"Trip to {p['dest']} from {p['from']}"  # [CONTENT-EDIT] Tooltip text
            ):
                # [LOGIC-EDIT] Change which form fields are auto-populated here
                st.session_state.f_dest = p['dest']
                st.session_state.f_origin = p['from']
                st.rerun()


def c_agent_badge(agent_type: str) -> str:
    """Color-coded agent type badge. High contrast for accessibility."""
    # [THEME-EDIT] Change agent colors or icons here
    # Format: "AgentName": ("text_color", "bg_color", "emoji_icon")
    cfg = {
        "ResearchAgent": ("#1B7DB8", "rgba(27,125,184,0.1)",  "🔍"),
        "CalcAgent":     ("#C8920A", "rgba(200,146,10,0.1)",  "🧮"),
        "CreativeAgent": ("#8B3FA8", "rgba(139,63,168,0.1)",  "✨"),
        "VerifyAgent":   ("#2D6A4F", "rgba(45,106,79,0.1)",   "✓"),
    }
    color, bg, icon = cfg.get(agent_type, ("#5A6655","rgba(90,102,85,0.1)","•"))
    return f"""
    <span style="
        background:{bg};color:{color};
        border:1.5px solid {color}44;
        border-radius:5px;padding:2px 9px;  /* [LAYOUT-EDIT] Badge padding */
        font-family:var(--font-body);
        font-size:0.7rem;font-weight:700;   /* [STYLE-EDIT] Badge font size */
        letter-spacing:0.05em;white-space:nowrap;
    " role="status" aria-label="{agent_type}">{icon} {agent_type}</span>
    """


def c_task_card(task: dict) -> str:
    """
    Single task card in the execution graph.
    Hierarchy: task_id > agent type > description > details.
    Progressive disclosure: validation rules are secondary.
    """
    # [THEME-EDIT] Agent accent colors for task card left border
    cfg = {
        "ResearchAgent": "#1B7DB8",
        "CalcAgent":     "#C8920A",
        "CreativeAgent": "#8B3FA8",
        "VerifyAgent":   "#2D6A4F",
    }
    agent = task.get("agent_type","")
    color = cfg.get(agent,"#5A6655")
    deps  = task.get("dependencies",[])

    # [STYLE-EDIT] Dependency pill styling
    dep_pills = "".join(
        f'<span style="background:var(--bg-sunken);color:var(--tx-dim);'
        f'border-radius:4px;padding:1px 7px;font-size:0.7rem;margin-right:4px;'
        f'font-family:var(--font-mono);">→ {d}</span>'
        for d in deps
    ) if deps else '<span style="color:var(--tx-dim);font-size:0.72rem;font-style:italic;">independent</span>'

    # [STYLE-EDIT] Tool tag styling
    tools = "  ".join(
        f'<code style="background:var(--bg-sunken);color:{color};padding:1px 6px;'
        f'border-radius:4px;font-size:0.72rem;font-family:var(--font-mono);">{t}</code>'
        for t in task.get("tools",[])
    )
    
    # [STYLE-EDIT] Validation rule row styling
    rules = "".join(
        f'<div style="color:var(--tx-secondary);font-size:0.75rem;padding:3px 0;'
        f'border-bottom:1px solid var(--border);line-height:1.4;">'
        f'<span style="color:{color};margin-right:5px;">✓</span>{r}</div>'
        for r in task.get("validation_rules",[])
    )
    output = task.get("expected_output","")

    # [LAYOUT-EDIT] Task card padding, border-left width, shadow
    return f"""
    <article style="
        background:var(--bg-surface);
        border:1px solid var(--border);
        border-left:3px solid {color};  /* [STYLE-EDIT] Left accent border width */
        border-radius:var(--radius);
        padding:14px 16px;              /* [LAYOUT-EDIT] Card internal spacing */
        box-shadow:var(--shadow-sm);
        transition:box-shadow 0.18s;
    " aria-label="Task {task.get('task_id','')}">

        <!-- Header row: task id + badge -->
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:9px;">
            <span style="
                font-family:var(--font-display);
                font-size:1.05rem;font-weight:700;  /* [STYLE-EDIT] Task ID size */
                color:{color};
            ">{task.get("task_id","")}</span>
            {c_agent_badge(agent)}
        </div>

        <!-- Description (primary info) -->
        <p style="
            color:var(--tx-primary);
            font-size:0.85rem;          /* [STYLE-EDIT] Description text size */
            line-height:1.55;
            margin:0 0 10px;
        ">{task.get("description","")}</p>

        <!-- Tools row -->
        <div style="margin-bottom:8px;">{tools}</div>

        <!-- Dependencies -->
        <div style="margin-bottom:10px;font-size:0.72rem;">
            <span style="color:var(--tx-dim);text-transform:uppercase;letter-spacing:0.07em;margin-right:6px;">Deps</span>
            {dep_pills}
        </div>

        <!-- Validation rules (secondary / progressive disclosure) -->
        <details style="margin-top:8px;">
            <summary style="
                color:var(--tx-secondary);
                font-size:0.72rem;
                font-weight:700;
                text-transform:uppercase;
                letter-spacing:0.07em;
                cursor:pointer;
                list-style:none;
                display:flex;align-items:center;gap:6px;
                padding:4px 0;
            ">
                <span style="font-size:0.9rem;">▸</span> Validation &amp; Output
            </summary>
            <div style="margin-top:8px;padding-top:8px;border-top:1px solid var(--border);">
                {rules}
                <div style="margin-top:6px;color:var(--tx-dim);font-size:0.73rem;">
                    <span style="font-weight:700;text-transform:uppercase;letter-spacing:0.06em;">Outputs → </span>{output}
                </div>
            </div>
        </details>

    </article>
    """


def c_group_divider(n: int, count: int) -> str:
    """Visual group separator between parallel execution layers."""
    # [STYLE-EDIT] Adjust divider line thickness, label padding, or colors
    return f"""
    <div style="
        display:flex;align-items:center;gap:12px;
        margin:18px 0 12px;  /* [LAYOUT-EDIT] Spacing between layers */
    " role="separator" aria-label="Parallel group {n}">
        <div style="flex:1;height:1px;background:var(--border);"></div>
        <div style="
            background:var(--bg-sunken);
            border:1.5px solid var(--border);
            border-radius:20px;
            padding:3px 14px;   /* [LAYOUT-EDIT] Label padding */
            font-family:var(--font-body);
            font-size:0.68rem;font-weight:700;
            color:var(--tx-secondary);
            letter-spacing:0.08em;
            text-transform:uppercase;
            white-space:nowrap;
        ">Layer {n} · {count} task{'s' if count>1 else ''}</div>
        <div style="flex:1;height:1px;background:var(--border);"></div>
    </div>
    """


def c_risk_pill(text: str) -> str:
    """Single risk flag card."""
    # [THEME-EDIT] Change risk colors from coral to another accent
    return f"""
    <div style="
        display:flex;align-items:flex-start;gap:10px;
        background:rgba(217,95,59,0.05);    /* [THEME-EDIT] Risk background tint */
        border:1px solid rgba(217,95,59,0.2);
        border-left:3px solid var(--ac-coral);  /* [STYLE-EDIT] Left border width */
        border-radius:var(--radius);
        padding:10px 14px;                  /* [LAYOUT-EDIT] Risk card padding */
        margin-bottom:8px;
    " role="alert">
        <span style="color:var(--ac-coral);font-size:0.9rem;flex-shrink:0;margin-top:1px;">⚠</span>
        <span style="color:var(--tx-secondary);font-size:0.84rem;line-height:1.5;">{text}</span>
    </div>
    """


def c_synthesis_block(s: dict) -> str:
    """Synthesis plan 3-row card."""
    # [CONTENT-EDIT] Change which synthesis fields are displayed or their labels
    rows = [
        ("Output Format",    s.get("final_output_format","—"), "var(--tx-primary)"),
        ("Compilation",      s.get("compilation_logic","—"),   "var(--tx-secondary)"),
        ("Fallback Strategy",s.get("fallback_strategy","—"),   "var(--ac-gold)"),
    ]
    # [STYLE-EDIT] Row spacing, border colors, or font sizes
    rows_html = "".join(f"""
    <div style="padding:10px 0;{'border-top:1px solid var(--border);' if i>0 else ''}">
        <div style="
            color:var(--tx-dim);
            font-size:0.68rem;font-weight:700;
            text-transform:uppercase;letter-spacing:0.08em;
            margin-bottom:4px;
        ">{label}</div>
        <div style="color:{color};font-size:0.85rem;line-height:1.5;">{val}</div>
    </div>
    """ for i,(label,val,color) in enumerate(rows))

    # [STYLE-EDIT] Top border color (currently green) or card padding
    return f"""
    <div style="
        background:var(--bg-surface);
        border:1px solid var(--border);
        border-top:3px solid var(--ac-green);  /* [THEME-EDIT] Top accent color */
        border-radius:var(--radius);
        padding:14px 18px;                     /* [LAYOUT-EDIT] Card padding */
        box-shadow:var(--shadow-sm);
    " aria-label="Synthesis plan">{rows_html}</div>
    """


def c_constraint_tag(text: str, variant: str = "hard") -> str:
    """Inline constraint / preference tag."""
    # [THEME-EDIT] Constraint type colors: hard=coral, soft=green, crit=gold
    colors = {
        "hard": ("var(--ac-coral)", "rgba(217,95,59,0.08)"),
        "soft": ("var(--ac-green)", "rgba(45,106,79,0.08)"),
        "crit": ("var(--ac-gold)",  "var(--ac-gold-dim)"),
    }
    color, bg = colors.get(variant, colors["soft"])
    return f"""
    <span style="
        background:{bg};color:{color};
        border:1px solid {color}33;
        border-radius:4px;
        padding:3px 10px;           /* [LAYOUT-EDIT] Tag padding */
        font-size:0.75rem;font-weight:700;
        display:inline-block;margin:3px 3px 3px 0;
        line-height:1.4;
    ">{text}</span>
    """


def c_empty_state() -> str:
    """Illustrated empty state shown before first submission."""
    # [CONTENT-EDIT] Change the empty state message, icon, or call-to-action
    # [STYLE-EDIT] Adjust padding, icon size, or max-width
    return """
    <div style="
        text-align:center;
        padding:5rem 2rem;          /* [LAYOUT-EDIT] Vertical padding */
        background:var(--bg-surface);
        border:1px dashed var(--border);
        border-radius:var(--radius-lg);
        margin-top:1rem;
    " role="region" aria-label="Empty state">
        <div style="font-size:3.5rem;margin-bottom:1.2rem;opacity:0.6;">🗺️</div>  <!-- [CONTENT-EDIT] Icon -->
        <h3 style="
            font-family:var(--font-display);
            font-size:1.3rem;font-weight:700;
            color:var(--tx-primary);margin:0 0 0.5rem;
        ">Plan your next adventure</h3>  <!-- [CONTENT-EDIT] Headline -->
        <p style="
            color:var(--tx-secondary);
            font-size:0.88rem;line-height:1.6;
            max-width:360px;margin:0 auto 1.5rem;  /* [LAYOUT-EDIT] Text max-width */
        ">
            Fill in your destination, departure city, trip length and budget
            — then hit <strong>Generate Trip Plan</strong>.
        </p>
        <div style="
            display:inline-flex;gap:8px;
            background:var(--bg-sunken);
            border-radius:20px;padding:6px 16px;
            font-size:0.75rem;color:var(--tx-dim);
            font-weight:700;letter-spacing:0.06em;
        ">✦ Powered by 4 AI agents working in parallel</div>  <!-- [CONTENT-EDIT] Footer tag -->
    </div>
    """


# ══════════════════════════════════════════════════════════════════════
# SECTION 6 — SIDEBAR RENDERER
# ══════════════════════════════════════════════════════════════════════
# [CONTENT-EDIT] ═══════════════════════════════════════════════════════
# Modify labels, options, or help text in the sidebar settings panel.
# [DATA-EDIT] Add new LLM providers or models to the dropdown lists.
# [LOGIC-EDIT] Change API key handling or environment variable names.

def render_sidebar() -> dict:
    """
    Dark forest sidebar — provider, model, API key, options.
    Returns settings dict.
    """
    with st.sidebar:
        # [CONTENT-EDIT] Sidebar header text and styling
        st.markdown("""
        <div style="padding:1.4rem 0 1.2rem;">
            <div style="
                font-family:var(--font-display);
                font-size:1.1rem;font-weight:700;
                color:var(--tx-invert);margin-bottom:4px;
            ">⚙ Settings</div>
            <div style="
                color:var(--tx-invert-dim);
                font-size:0.72rem;text-transform:uppercase;letter-spacing:0.07em;
            ">Provider & Model</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # [DATA-EDIT] Add new providers here (requires backend support in app.py)
        provider = st.selectbox(
            "LLM Provider",           # [CONTENT-EDIT] Label text
            options=["openai", "ollama"],
            key="sb_provider",
        )

        # [DATA-EDIT] Model defaults per provider — add new models here
        model_opts = {
            "openai": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
            "ollama": ["llama3.2", "mistral", "llama3.1:8b", "gemma2"],
        }
        model = st.selectbox(
            "Model",                  # [CONTENT-EDIT] Label text
            options=model_opts[provider],
            key="sb_model",
        )

        # [LOGIC-EDIT] API key handling for OpenAI
        if provider == "openai":
            st.markdown("---")
            env_key = os.getenv("OPENAI_API_KEY","")  # [LOGIC-EDIT] Env var name
            if env_key:
                # [CONTENT-EDIT] Success message when key is pre-loaded
                st.markdown("""
                <div style="
                    background:rgba(45,106,79,0.15);
                    border:1px solid rgba(45,106,79,0.4);
                    border-radius:6px;padding:8px 12px;
                    font-size:0.78rem;color:#7DC9A0;
                ">✓ API key loaded from .env</div>
                """, unsafe_allow_html=True)
            else:
                # [CONTENT-EDIT] Input placeholder and help text
                api_input = st.text_input(
                    "OpenAI API Key",
                    type="password",
                    placeholder="sk-proj-...",
                    key="sb_apikey",
                    help="Paste your OpenAI key here. It's only stored for this session.",
                )
                if api_input:
                    os.environ["OPENAI_API_KEY"] = api_input  # [LOGIC-EDIT] Session storage
                    st.markdown("""
                    <div style="
                        background:rgba(45,106,79,0.15);
                        border:1px solid rgba(45,106,79,0.4);
                        border-radius:6px;padding:8px 12px;
                        font-size:0.78rem;color:#7DC9A0;margin-top:6px;
                    ">✓ Key active for this session</div>
                    """, unsafe_allow_html=True)

        # [CONTENT-EDIT] Ollama endpoint display
        if provider == "ollama":
            st.markdown("---")
            url = os.getenv("OLLAMA_BASE_URL","http://localhost:11434")  # [LOGIC-EDIT] Default URL
            st.markdown(f"""
            <div style="
                background:rgba(255,255,255,0.04);
                border:1px solid var(--border-dark);
                border-radius:6px;padding:10px 12px;
                font-size:0.78rem;
            ">
                <div style="color:var(--tx-invert-dim);margin-bottom:3px;font-size:0.68rem;
                    text-transform:uppercase;letter-spacing:0.07em;">Endpoint</div>
                <code style="color:#D95F3B;font-family:var(--font-mono);">{url}</code>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # [CONTENT-EDIT] Toggle label and help text
        plan_only = st.toggle(
            "Plan only (skip report)",
            value=False,
            key="sb_planonly",
            help="Generate just the execution graph without the full markdown report.",
        )

        st.markdown("---")

        # [CONTENT-EDIT] Sidebar footer text and links
        st.markdown("""
        <div style="
            color:var(--tx-invert-dim);
            font-size:0.72rem;line-height:1.8;
            padding-bottom:1rem;
        ">
            <div style="margin-bottom:6px;color:var(--tx-invert);font-weight:700;">
                Trip Planner AI
            </div>
            LangChain · Pydantic · Streamlit<br>
            Multi-agent autonomous planning<br><br>
            <a href="https://github.com " style="color:#D95F3B;text-decoration:none;font-weight:700;">
                GitHub ↗
            </a>
        </div>
        """, unsafe_allow_html=True)

    return {"provider": provider, "model": model, "plan_only": plan_only}


# ══════════════════════════════════════════════════════════════════════
# SECTION 7 — INPUT FORM
# ══════════════════════════════════════════════════════════════════════
# [DATA-EDIT] ═════════════════════════════════════════════════════════
# Modify the QUICK_PICKS list to change featured destinations.
# Format: {"flag": "emoji", "dest": "Destination", "from": "Origin City"}
#
# [CONTENT-EDIT] Change form labels, placeholders, or help text.
# [LOGIC-EDIT] Adjust validation rules, min/max values, or defaults.

# Popular destinations for quick-pick shortcuts
QUICK_PICKS = [
    # [DATA-EDIT] Add, remove, or modify destinations here
    {"flag":"🇵🇰","dest":"Pakistan",   "from":"Karachi"},
    {"flag":"🇯🇵","dest":"Japan",      "from":"London"},
    {"flag":"🇦🇪","dest":"Dubai",      "from":"Lahore"},
    {"flag":"🇹🇷","dest":"Turkey",     "from":"Islamabad"},
    {"flag":"🇮🇩","dest":"Bali",       "from":"Singapore"},
    {"flag":"🇮🇹","dest":"Italy",      "from":"New York"},
]

def render_form() -> dict | None:
    """
    Trip input form. Returns inputs dict or None if not submitted.
    Hierarchy: destination first (biggest decision), then logistics.
    """
    # [CONTENT-EDIT] Section title and subtitle
    st.markdown(c_section_title("🗺️","Plan Your Trip","Tell us where you want to go"), unsafe_allow_html=True)

    # Quick-pick shortcuts (effortless / shortcut principles)
    render_quick_picks(QUICK_PICKS)
    
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # Form fields — 2 column layout
    # [LAYOUT-EDIT] Adjust column ratios or gap size
    col1, col2 = st.columns(2, gap="medium")
    with col1:
        # [CONTENT-EDIT] Destination field label, placeholder, help
        destination = st.text_input(
            "📍 Destination",
            placeholder="Country, city or region",
            key="f_dest",
            help="Where do you want to travel to?",
        )
    with col2:
        # [CONTENT-EDIT] Origin field label, placeholder, help
        origin = st.text_input(
            "✈️ Departure City",
            placeholder="Your city or airport",
            key="f_origin",
            help="Where will you be flying from?",
        )

    # [LAYOUT-EDIT] Second row of columns
    col3, col4 = st.columns(2, gap="medium")
    with col3:
        # [LOGIC-EDIT] Duration min/max values and default
        days = st.number_input(
            "🗓️ Duration (days)",
            min_value=1, max_value=30, value=3, step=1,  # [LOGIC-EDIT] Constraints
            key="f_days",
            help="How many days is your trip?",
        )
    with col4:
        # [LOGIC-EDIT] Budget min/max values, default, and step
        budget = st.number_input(
            "💰 Budget (USD)",
            min_value=100, max_value=50000, value=1000, step=100,  # [LOGIC-EDIT] Constraints
            key="f_budget",
            help="Your total trip budget in US dollars.",
        )

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # Primary CTA
    # [CONTENT-EDIT] Button text and key
    go = st.button(
        "✦  Generate My Trip Plan",  # [CONTENT-EDIT] Button label
        type="primary",
        use_container_width=True,
        key="f_submit",
    )

    if go:
        # [LOGIC-EDIT] Add or modify form validation rules here
        errors = []
        if not destination.strip(): errors.append("Please enter a destination.")
        if not origin.strip():      errors.append("Please enter your departure city.")
        if errors:
            for e in errors: st.error(e)
            return None
        return {
            "destination": destination.strip(),
            "origin":      origin.strip(),
            "days":        int(days),
            "budget":      int(budget),
        }
    return None


# ══════════════════════════════════════════════════════════════════════
# SECTION 8 — EXECUTION GRAPH RENDERER
# ══════════════════════════════════════════════════════════════════════
# [LAYOUT-EDIT] ═══════════════════════════════════════════════════════
# Modify how tasks are grouped and displayed. Currently groups by
# parallel_group and displays in columns.

def render_graph(tasks: list[dict]):
    """
    Render tasks grouped by parallel_group.
    Tasks in the same group are shown side-by-side.
    """
    groups: dict[int, list] = {}
    for t in tasks:
        groups.setdefault(t["parallel_group"], []).append(t)

    for gid in sorted(groups):
        group = groups[gid]
        st.markdown(c_group_divider(gid, len(group)), unsafe_allow_html=True)

        if len(group) == 1:
            st.markdown(c_task_card(group[0]), unsafe_allow_html=True)
        else:
            # [LAYOUT-EDIT] Adjust column gap or equalize widths
            cols = st.columns(len(group), gap="small")
            for col, task in zip(cols, group):
                with col:
                    st.markdown(c_task_card(task), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# SECTION 9 — RESULTS RENDERER
# ══════════════════════════════════════════════════════════════════════
# [CONTENT-EDIT] ═══════════════════════════════════════════════════════
# Modify tab names, section labels, or the order of information display.
# [LAYOUT-EDIT] Adjust metric column count, tab layout, or card spacing.
# [STYLE-EDIT] Change banner colors, border accents, or font sizes.

def render_results(plan_data: dict, report_md: str | None, inputs: dict):
    """
    Display full results with progressive disclosure:
    metrics → tabs (overview / report / graph / synthesis / risks).
    """
    ia    = plan_data.get("input_analysis", {})
    tasks = plan_data.get("execution_graph", [])
    risks = plan_data.get("risk_flags", [])
    synth = plan_data.get("synthesis_plan", {})

    # ── Success banner ──
    # [CONTENT-EDIT] Success message text and structure
    # [STYLE-EDIT] Banner background, border colors, or padding
    st.markdown(f"""
    <div style="
        background:var(--ac-gold-dim);
        border:1px solid rgba(200,146,10,0.3);
        border-left:3px solid var(--ac-gold);
        border-radius:var(--radius);
        padding:12px 18px;          /* [LAYOUT-EDIT] Banner padding */
        margin-bottom:1.4rem;
        display:flex;align-items:center;gap:12px;
    " role="status" aria-live="polite">
        <span style="font-size:1.2rem;">✓</span>
        <div>
            <strong style="color:var(--tx-primary);font-size:0.9rem;">
                Plan ready — {inputs['days']}-day trip to {inputs['destination']}
            </strong>
            <div style="color:var(--tx-secondary);font-size:0.78rem;margin-top:2px;">
                From {inputs['origin']} · Budget USD {inputs['budget']:,}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Metric strip ──
    # [LOGIC-EDIT] Add or modify calculated metrics here
    agent_counts: dict[str,int] = {}
    for t in tasks:
        a = t.get("agent_type","?")
        agent_counts[a] = agent_counts.get(a, 0) + 1
    groups_count = len(set(t["parallel_group"] for t in tasks))

    # [LAYOUT-EDIT] Change number of metric columns (currently 4)
    m1, m2, m3, m4 = st.columns(4, gap="small")
    with m1: st.metric("Total Tasks",     len(tasks))
    with m2: st.metric("Parallel Layers", groups_count)
    with m3: st.metric("Risk Flags",      len(risks))
    with m4: st.metric("Agent Types",     len(agent_counts))

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Tabs (progressive disclosure) ──
    # [CONTENT-EDIT] Change tab names, icons, or order
    tab_names = ["📋 Overview", "🔗 Execution Graph", "🧩 Synthesis", "⚠️ Risks"]
    if report_md:
        tab_names.insert(1, "📄 Full Report")  # [LOGIC-EDIT] Conditional tab insertion

    tabs = st.tabs(tab_names)
    tidx = 0

    # Tab: Overview
    with tabs[tidx]:
        tidx += 1
        # [CONTENT-EDIT] Goal card text and structure
        st.markdown(f"""
        <div style="
            background:var(--bg-surface);
            border:1px solid var(--border);
            border-radius:var(--radius);
            padding:18px 20px;      /* [LAYOUT-EDIT] Card padding */
            box-shadow:var(--shadow-sm);
            margin-bottom:1rem;
        ">
            <div style="color:var(--tx-dim);font-size:0.68rem;text-transform:uppercase;
                letter-spacing:0.08em;margin-bottom:6px;">Goal</div>
            <p style="
                font-family:var(--font-display);
                font-size:1rem;font-weight:600;
                color:var(--tx-primary);margin:0;line-height:1.5;
            ">{ia.get('goal','—')}</p>
        </div>
        """, unsafe_allow_html=True)

        # [LAYOUT-EDIT] Overview column ratio (currently equal 2-column)
        oc1, oc2 = st.columns(2, gap="medium")
        with oc1:
            # [CONTENT-EDIT] Left column section titles
            st.markdown("**🔒 Hard Constraints**")
            constraints_html = "".join(
                c_constraint_tag(item, "hard")
                for item in ia.get("hard_constraints", [])
            )
            st.markdown(constraints_html or "*None*", unsafe_allow_html=True)
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            st.markdown("**🎯 Success Criteria**")
            for item in ia.get("success_criteria",[]):
                st.markdown(f"<div style='font-size:0.84rem;color:var(--tx-secondary);padding:3px 0;'>✓ {item}</div>", unsafe_allow_html=True)

        with oc2:
            # [CONTENT-EDIT] Right column section titles
            st.markdown("**💭 Preferences**")
            prefs = ia.get("soft_preferences",[])
            if prefs:
                prefs_html = "".join(c_constraint_tag(p, "soft") for p in prefs)
                st.markdown(prefs_html, unsafe_allow_html=True)
            else:
                st.markdown("<em style='color:var(--tx-dim);font-size:0.84rem;'>None specified</em>", unsafe_allow_html=True)
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            st.markdown("**🤖 Agents Used**")
            for agent, cnt in agent_counts.items():
                st.markdown(
                    f"<div style='margin:4px 0;'>{c_agent_badge(agent)}"
                    f"<span style='color:var(--tx-secondary);font-size:0.78rem;margin-left:8px;'>{cnt} task{'s' if cnt>1 else ''}</span></div>",
                    unsafe_allow_html=True,
                )

    # Tab: Full Report (only shown when report_md exists)
    if report_md:
        with tabs[tidx]:
            tidx += 1
            # [LAYOUT-EDIT] Download button column width ratio
            dl_col, _ = st.columns([1, 3])
            with dl_col:
                # [CONTENT-EDIT] Download button text and filename format
                st.download_button(
                    "⬇ Download Report",
                    data=report_md,
                    file_name=f"trip_{inputs['destination'].lower().replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.md",
                    mime="text/markdown",
                    key="dl_report",
                )
            st.markdown("---")
            st.markdown(report_md)
    else:
        tidx  # no tab consumed, skip

    # Tab: Execution Graph
    with tabs[tidx]:
        tidx += 1
        render_graph(tasks)

    # Tab: Synthesis
    with tabs[tidx]:
        tidx += 1
        st.markdown(c_synthesis_block(synth), unsafe_allow_html=True)

    # Tab: Risks
    with tabs[tidx]:
        if risks:
            for r in risks:
                st.markdown(c_risk_pill(r), unsafe_allow_html=True)
        else:
            # [CONTENT-EDIT] No risks message
            st.success("No risk flags identified for this plan.")


# ══════════════════════════════════════════════════════════════════════
# SECTION 10 — BACKEND RUNNER
# Calls app.py without modifying it.
# ══════════════════════════════════════════════════════════════════════
# [LOGIC-EDIT] ════════════════════════════════════════════════════════
# Modify how the planner is instantiated or how results are processed.
# Change the request prompt format, error handling, or data extraction.

def run_planner(inputs: dict, settings: dict) -> tuple[dict, str | None]:
    """
    Import AutonomousTaskPlanner from app.py and run the full pipeline.
    Returns (plan_data_dict, report_markdown_or_none).
    """
    import importlib, sys
    if "app" in sys.modules:
        importlib.reload(sys.modules["app"])
    from app import AutonomousTaskPlanner, _save

    # [LOGIC-EDIT] Extract and format inputs for the backend
    destination = inputs["destination"]
    origin      = inputs["origin"]
    days        = inputs["days"]
    budget      = inputs["budget"]
    
    # [CONTENT-EDIT] Modify the request prompt format sent to the planner
    request     = f"Plan a {days}-day trip to {destination} under USD {budget}"

    # [LOGIC-EDIT] Planner initialization with provider/model settings
    planner   = AutonomousTaskPlanner(provider=settings["provider"], model=settings["model"])
    plan      = planner.plan(request, origin)
    plan_data = json.loads(plan.model_dump_json())

    # [LOGIC-EDIT] Conditional report generation based on settings
    report_md = None
    if not settings["plan_only"]:
        report_md = planner.generate_report(plan, request, origin)

    # [LOGIC-EDIT] Save plan to disk (function from app.py)
    _save(plan, report_md or "", request)
    return plan_data, report_md


# ══════════════════════════════════════════════════════════════════════
# SECTION 11 — MAIN  (entry point)
# ══════════════════════════════════════════════════════════════════════
# [LAYOUT-EDIT] ═══════════════════════════════════════════════════════
# Modify the main layout structure, column ratios, or component order.
# [LOGIC-EDIT] Add initialization, session state setup, or routing.

def main():
    # 1. Inject CSS
    st.markdown(build_css(TOKENS), unsafe_allow_html=True)

    # 2. Top header bar
    st.markdown(c_header(), unsafe_allow_html=True)

    # 3. Sidebar
    settings = render_sidebar()

    # 4. Main layout: form (left) | results (right) on wide screens
    #    On mobile Streamlit stacks them vertically automatically.
    # [LAYOUT-EDIT] Adjust column ratio: [1, 1.6] means results are 1.6x wider
    form_col, result_col = st.columns([1, 1.6], gap="large")

    with form_col:
        # [LAYOUT-EDIT] Top padding for form column
        st.markdown("<div style='padding:1.8rem 0 0;'></div>", unsafe_allow_html=True)
        inputs = render_form()

    with result_col:
        # [LAYOUT-EDIT] Top padding for results column
        st.markdown("<div style='padding:1.8rem 0 0;'></div>", unsafe_allow_html=True)

        if inputs:
            # [CONTENT-EDIT] Loading spinner message
            with st.spinner("🤖  Agents working — this takes ~30 seconds…"):
                try:
                    plan_data, report_md = run_planner(inputs, settings)
                    render_results(plan_data, report_md, inputs)
                except SystemExit as e:
                    st.error(str(e))
                except Exception:
                    # [CONTENT-EDIT] Generic error message
                    st.error("Something went wrong. Check the details below.")
                    with st.expander("Error details"):
                        st.code(traceback.format_exc())
        else:
            st.markdown(c_empty_state(), unsafe_allow_html=True)


if __name__ == "__main__":
    main()