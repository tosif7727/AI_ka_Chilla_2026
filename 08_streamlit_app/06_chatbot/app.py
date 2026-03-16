# ── app.py ─────────────────────────────────────────────────
# Streamlit UI for Steel Pro Customer Support Bot.
# Run with: streamlit run app.py
#
# Imports bot.py, config.py, ingest.py unchanged.
# All core logic stays exactly as-is.
# ───────────────────────────────────────────────────────────

import os
import sys
import streamlit as st

# ── Page config (must be first Streamlit call) ────────────────
st.set_page_config(
    page_title="Steel Pro Support",
    page_icon="🔩",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@300;400;500;600;700;900&family=Barlow+Condensed:wght@600;700;900&display=swap');

/* ── Root variables ── */
:root {
    --steel-dark:    #0d1117;
    --steel-panel:   #161b22;
    --steel-border:  #21262d;
    --steel-mid:     #30363d;
    --steel-accent:  #e8a000;
    --steel-orange:  #f0a500;
    --steel-red:     #da3633;
    --steel-green:   #238636;
    --steel-blue:    #1f6feb;
    --steel-text:    #e6edf3;
    --steel-muted:   #7d8590;
    --steel-subtle:  #b1bac4;
}

/* ── Global reset ── */
html, body, [class*="css"] {
    font-family: 'Barlow', sans-serif !important;
    background-color: var(--steel-dark) !important;
    color: var(--steel-text) !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
[data-testid="stToolbar"] { display: none; }

/* ── Main container ── */
.main .block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--steel-panel) !important;
    border-right: 1px solid var(--steel-border) !important;
    padding: 0 !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 0 !important;
}

/* ── Sidebar content padding ── */
.sidebar-content { padding: 1.5rem; }

/* ── Logo block ── */
.logo-block {
    background: linear-gradient(135deg, #1a1f2e 0%, #0d1117 100%);
    border-bottom: 2px solid var(--steel-accent);
    padding: 1.5rem;
    margin-bottom: 0;
}
.logo-title {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-size: 1.6rem;
    font-weight: 900;
    color: var(--steel-text);
    letter-spacing: 0.05em;
    text-transform: uppercase;
    line-height: 1;
    margin: 0;
}
.logo-subtitle {
    font-size: 0.7rem;
    font-weight: 500;
    color: var(--steel-accent);
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-top: 0.3rem;
}
.logo-icon {
    font-size: 2rem;
    margin-bottom: 0.5rem;
    display: block;
}

/* ── Section labels in sidebar ── */
.section-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--steel-muted);
    margin: 1.5rem 0 0.6rem 0;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid var(--steel-border);
}

/* ── Status pills ── */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.3rem 0.75rem;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
.status-ready   { background: rgba(35,134,54,0.15); color: #3fb950; border: 1px solid rgba(35,134,54,0.3); }
.status-offline { background: rgba(218,54,51,0.15); color: #f85149; border: 1px solid rgba(218,54,51,0.3); }
.status-waiting { background: rgba(230,160,0,0.15); color: var(--steel-accent); border: 1px solid rgba(230,160,0,0.3); }

/* ── Provider card ── */
.provider-card {
    background: var(--steel-dark);
    border: 1px solid var(--steel-border);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin: 0.4rem 0;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    cursor: pointer;
    transition: border-color 0.2s;
}
.provider-card.active {
    border-color: var(--steel-accent);
    background: rgba(232,160,0,0.05);
}
.provider-icon { font-size: 1.3rem; }
.provider-name { font-weight: 600; font-size: 0.85rem; }
.provider-desc { font-size: 0.7rem; color: var(--steel-muted); }

/* ── Stats row ── */
.stat-row {
    display: flex;
    gap: 0.5rem;
    margin: 0.5rem 0;
}
.stat-box {
    flex: 1;
    background: var(--steel-dark);
    border: 1px solid var(--steel-border);
    border-radius: 6px;
    padding: 0.6rem;
    text-align: center;
}
.stat-value {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--steel-accent);
    line-height: 1;
}
.stat-label {
    font-size: 0.6rem;
    color: var(--steel-muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.2rem;
}

/* ── Main chat area ── */
.chat-header {
    background: var(--steel-panel);
    border-bottom: 1px solid var(--steel-border);
    padding: 1rem 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 100;
}
.chat-title {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--steel-text);
}

/* ── Message bubbles ── */
.msg-wrap {
    display: flex;
    gap: 0.75rem;
    margin: 1.25rem 0;
    animation: fadeUp 0.3s ease;
}
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
.msg-wrap.user { flex-direction: row-reverse; }

.msg-avatar {
    width: 34px;
    height: 34px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
    font-weight: 700;
}
.avatar-user { background: var(--steel-blue); }
.avatar-bot  { background: linear-gradient(135deg, var(--steel-accent), #c87000); color: #000; }

.msg-bubble {
    max-width: 70%;
    padding: 0.85rem 1.1rem;
    border-radius: 12px;
    font-size: 0.9rem;
    line-height: 1.6;
    position: relative;
}
.bubble-user {
    background: var(--steel-blue);
    color: #fff;
    border-bottom-right-radius: 4px;
}
.bubble-bot {
    background: var(--steel-panel);
    border: 1px solid var(--steel-border);
    color: var(--steel-text);
    border-bottom-left-radius: 4px;
}
.bubble-bot.handoff {
    border-color: rgba(218,54,51,0.4);
    background: rgba(218,54,51,0.05);
}

/* ── Message metadata bar ── */
.msg-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.6rem;
    align-items: center;
}
.meta-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.2rem 0.55rem;
    border-radius: 4px;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.chip-answered { background: rgba(35,134,54,0.2);  color: #3fb950; }
.chip-handoff  { background: rgba(218,54,51,0.2);  color: #f85149; }
.chip-score    { background: rgba(31,111,235,0.2);  color: #79c0ff; }
.chip-sim      { background: rgba(232,160,0,0.15);  color: var(--steel-accent); }
.chip-source   { background: rgba(177,186,196,0.1); color: var(--steel-subtle); }

/* ── Ticket badge ── */
.ticket-badge {
    margin-top: 0.5rem;
    padding: 0.5rem 0.75rem;
    background: rgba(218,54,51,0.08);
    border: 1px solid rgba(218,54,51,0.25);
    border-radius: 6px;
    font-size: 0.72rem;
    color: #f85149;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* ── Welcome screen ── */
.welcome-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    text-align: center;
}
.welcome-icon {
    font-size: 4rem;
    margin-bottom: 1.5rem;
    filter: drop-shadow(0 0 30px rgba(232,160,0,0.3));
}
.welcome-title {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-size: 2.2rem;
    font-weight: 900;
    color: var(--steel-text);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.5rem;
}
.welcome-sub {
    font-size: 0.95rem;
    color: var(--steel-muted);
    max-width: 420px;
    line-height: 1.6;
    margin-bottom: 2rem;
}
.suggestion-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
    max-width: 540px;
    width: 100%;
}
.suggestion-chip {
    background: var(--steel-panel);
    border: 1px solid var(--steel-border);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    font-size: 0.8rem;
    color: var(--steel-subtle);
    text-align: left;
    cursor: pointer;
    transition: all 0.2s;
}
.suggestion-chip:hover {
    border-color: var(--steel-accent);
    color: var(--steel-text);
    background: rgba(232,160,0,0.05);
}
.suggestion-label {
    font-size: 0.65rem;
    color: var(--steel-accent);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.3rem;
}

/* ── Input area ── */
.input-wrap {
    background: var(--steel-panel);
    border-top: 1px solid var(--steel-border);
    padding: 1rem 2rem;
    position: sticky;
    bottom: 0;
}

/* ── Override Streamlit inputs ── */
.stTextInput input, .stTextArea textarea {
    background: var(--steel-dark) !important;
    border: 1px solid var(--steel-mid) !important;
    border-radius: 8px !important;
    color: var(--steel-text) !important;
    font-family: 'Barlow', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 0.75rem 1rem !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--steel-accent) !important;
    box-shadow: 0 0 0 2px rgba(232,160,0,0.15) !important;
}

/* ── Buttons ── */
.stButton button {
    background: var(--steel-accent) !important;
    color: #000 !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Barlow', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.04em !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.2s !important;
}
.stButton button:hover {
    background: #f0a500 !important;
    transform: translateY(-1px) !important;
}
.stButton button:active { transform: translateY(0) !important; }

/* ── Radio buttons ── */
.stRadio label {
    color: var(--steel-text) !important;
    font-size: 0.85rem !important;
}
.stRadio [data-testid="stMarkdownContainer"] p {
    font-size: 0.85rem !important;
    color: var(--steel-text) !important;
}

/* ── Select box ── */
.stSelectbox select {
    background: var(--steel-dark) !important;
    border: 1px solid var(--steel-mid) !important;
    color: var(--steel-text) !important;
    border-radius: 8px !important;
}

/* ── Divider ── */
hr { border-color: var(--steel-border) !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--steel-dark); }
::-webkit-scrollbar-thumb { background: var(--steel-mid); border-radius: 3px; }

/* ── Spinner ── */
.stSpinner > div { border-top-color: var(--steel-accent) !important; }

/* ── Alerts ── */
.stAlert {
    background: rgba(232,160,0,0.08) !important;
    border: 1px solid rgba(232,160,0,0.25) !important;
    border-radius: 8px !important;
    color: var(--steel-text) !important;
}

/* ── Chat messages area padding ── */
.chat-messages { padding: 1rem 2rem; }

/* ── Password input ── */
.stTextInput [type="password"] {
    background: var(--steel-dark) !important;
    border: 1px solid var(--steel-mid) !important;
    color: var(--steel-text) !important;
}

/* ── Ticket history in sidebar ── */
.ticket-row {
    background: var(--steel-dark);
    border: 1px solid var(--steel-border);
    border-left: 3px solid var(--steel-red);
    border-radius: 6px;
    padding: 0.6rem 0.75rem;
    margin: 0.4rem 0;
    font-size: 0.72rem;
}
.ticket-row-id { color: #f85149; font-weight: 700; font-size: 0.65rem; }
.ticket-row-q  { color: var(--steel-subtle); margin-top: 0.2rem; }

/* ── Clear button small ── */
.btn-clear {
    background: transparent !important;
    border: 1px solid var(--steel-border) !important;
    color: var(--steel-muted) !important;
    font-size: 0.72rem !important;
    padding: 0.3rem 0.8rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
}
.btn-clear:hover {
    border-color: var(--steel-red) !important;
    color: #f85149 !important;
    background: rgba(218,54,51,0.05) !important;
    transform: none !important;
}
</style>
""", unsafe_allow_html=True)


# ── Session state init ────────────────────────────────────────
def init_state():
    defaults = {
        "messages":          [],
        "tickets":           [],
        "bot":               None,
        "provider":          None,
        "ready":             False,
        "total_q":           0,
        "total_handoff":     0,
        "api_key_input":     "",
        "_pending_question": None,   # queue for suggestion chip clicks
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── Setup functions (unchanged from original) ─────────────────
def validate_docs(docs_dir: str) -> tuple[bool, str]:
    """
    Check that ./docs exists and has at least one .txt or .pdf file.
    Returns (is_valid, error_message).
    """
    if not os.path.exists(docs_dir):
        return False, (
            "📁 **`./docs` folder not found.**\n\n"
            "Please create a `./docs` folder and add your support documents "
            "(.txt or .pdf files) before starting the bot.\n\n"
            "See **README.md** for full setup instructions."
        )

    valid_files = [f for f in os.listdir(docs_dir) if f.endswith((".txt", ".pdf"))]
    if not valid_files:
        return False, (
            "📂 **`./docs` folder is empty.**\n\n"
            f"Found the folder `{docs_dir}/` but no `.txt` or `.pdf` files inside it.\n\n"
            "Add your support documents and click **Start Bot** again.\n\n"
            "See **README.md** for full setup instructions."
        )

    return True, f"✅ Found **{len(valid_files)} document(s)** in `{docs_dir}/`"


def setup_bot(provider: str, api_key: str = ""):
    """Patch config and initialise the bot — mirrors main.py logic exactly."""
    import config as cfg
    cfg.LLM_PROVIDER = provider
    if provider == "openai" and api_key:
        cfg.OPENAI_API_KEY = api_key
        os.environ["OPENAI_API_KEY"] = api_key

    from ingest import ingest, load_store
    from config import CHROMA_DIR, DOCS_DIR

    # Validate docs folder — raise clear error if missing or empty
    is_valid, message = validate_docs(DOCS_DIR)
    if not is_valid:
        raise FileNotFoundError(message)

    # Load or build vector store
    if os.path.exists(CHROMA_DIR) and os.listdir(CHROMA_DIR):
        store = load_store()
    else:
        store = ingest(DOCS_DIR)

    from bot import SupportBot
    return SupportBot(store)





# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:

    # Logo
    st.markdown("""
    <div class="logo-block">
        <span class="logo-icon">🔩</span>
        <div class="logo-title">Steel Pro</div>
        <div class="logo-subtitle">Customer Support AI</div>
    </div>
    """, unsafe_allow_html=True)

    # ── sidebar content ──

    # ── Provider selection ────────────────────────────────────
    st.markdown('<div class="section-label">AI Provider</div>', unsafe_allow_html=True)

    provider_choice = st.radio(
        "provider",
        options=["OpenAI (Fast)", "Ollama (Local & Free)"],
        index=0,
        label_visibility="collapsed",
    )
    provider = "openai" if "OpenAI" in provider_choice else "ollama"

    # OpenAI key input
    api_key = ""
    if provider == "openai":
        st.markdown('<div class="section-label">API Key</div>', unsafe_allow_html=True)
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            placeholder="sk-...",
            label_visibility="collapsed",
            help="Get your key at platform.openai.com/api-keys",
        )
        if api_key and not api_key.startswith("sk-"):
            st.error("Key must start with sk-")
            api_key = ""
    else:
        st.markdown("""
        <div style="background:rgba(232,160,0,0.08);border:1px solid rgba(232,160,0,0.2);
                    border-radius:6px;padding:0.6rem 0.75rem;margin:0.5rem 0;font-size:0.75rem;
                    color:#b1bac4;">
            🖥️ Make sure <strong style="color:#e8a000;">ollama serve</strong> is running locally
        </div>
        """, unsafe_allow_html=True)

    # ── Start / Status ────────────────────────────────────────
    st.markdown('<div class="section-label">Connection</div>', unsafe_allow_html=True)

    if not st.session_state.ready:
        st.markdown('<div class="status-pill status-waiting">⏳ Not connected</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        can_start = (provider == "ollama") or (provider == "openai" and api_key.startswith("sk-") and len(api_key) > 20)

        if st.button("🚀  Start Bot", use_container_width=True, disabled=not can_start):
            with st.spinner("Initialising knowledge base…"):
                try:
                    bot = setup_bot(provider, api_key)
                    st.session_state.bot      = bot
                    st.session_state.provider = provider
                    st.session_state.ready    = True
                    st.rerun()
                except FileNotFoundError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Failed to start: {e}")
    else:
        prov_label = "OpenAI" if st.session_state.provider == "openai" else "Ollama"
        prov_icon  = "☁️" if st.session_state.provider == "openai" else "🖥️"
        st.markdown(f'<div class="status-pill status-ready">✓ Connected via {prov_icon} {prov_label}</div>', unsafe_allow_html=True)

    # ── Session stats ─────────────────────────────────────────
    if st.session_state.ready:
        st.markdown('<div class="section-label">Session Stats</div>', unsafe_allow_html=True)
        answered = st.session_state.total_q - st.session_state.total_handoff
        st.markdown(f"""
        <div class="stat-row">
            <div class="stat-box">
                <div class="stat-value">{st.session_state.total_q}</div>
                <div class="stat-label">Asked</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{answered}</div>
                <div class="stat-label">Answered</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{st.session_state.total_handoff}</div>
                <div class="stat-label">Escalated</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Ticket history ────────────────────────────────────
        if st.session_state.tickets:
            st.markdown('<div class="section-label">Support Tickets</div>', unsafe_allow_html=True)
            for t in reversed(st.session_state.tickets[-5:]):
                q_short = t["question"][:45] + "…" if len(t["question"]) > 45 else t["question"]
                st.markdown(f"""
                <div class="ticket-row">
                    <div class="ticket-row-id">📋 {t['ticket_id'][-12:]} · {t['priority'].upper()}</div>
                    <div class="ticket-row-q">{q_short}</div>
                </div>
                """, unsafe_allow_html=True)

        # ── Clear chat ────────────────────────────────────────
        st.markdown('<div class="section-label">Actions</div>', unsafe_allow_html=True)
        if st.button("🗑️  Clear Chat", use_container_width=True, key="clear"):
            st.session_state.messages      = []
            st.session_state.tickets       = []
            st.session_state.total_q       = 0
            st.session_state.total_handoff = 0
            if st.session_state.bot:
                st.session_state.bot.history = []
                st.session_state.bot.tickets = []
            st.rerun()

    # ── end sidebar ──


# ── Main chat area ────────────────────────────────────────────
col_main = st.container()

with col_main:

    # ── Header bar ───────────────────────────────────────────
    st.markdown("""
    <div class="chat-header">
        <div class="chat-title">🔩 Steel Pro — Support Chat</div>
        <div style="font-size:0.75rem;color:#7d8590;">
            Ask about products, pricing, services & store info
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Message display ───────────────────────────────────────
    # ── chat messages ──

    if not st.session_state.ready:
        # Not connected yet — show setup prompt
        st.markdown("""
        <div class="welcome-wrap">
            <div class="welcome-icon">🔩</div>
            <div class="welcome-title">Steel Pro Support</div>
            <div class="welcome-sub">
                Select your AI provider in the sidebar and click
                <strong style="color:#e8a000;">Start Bot</strong> to begin.
            </div>
            <div style="font-size:0.8rem;color:#7d8590;margin-bottom:1.5rem;">
                OpenAI gives faster answers &nbsp;·&nbsp; Ollama is free and runs locally
            </div>
            <div style="background:rgba(232,160,0,0.07);border:1px solid rgba(232,160,0,0.2);
                        border-radius:10px;padding:1.2rem 1.5rem;max-width:420px;text-align:left;">
                <div style="font-size:0.7rem;font-weight:700;letter-spacing:0.1em;
                            text-transform:uppercase;color:#e8a000;margin-bottom:0.7rem;">
                    ⚠ Before you start
                </div>
                <div style="font-size:0.8rem;color:#b1bac4;line-height:1.7;">
                    Make sure your <code style="background:#21262d;padding:0.1rem 0.4rem;
                    border-radius:4px;color:#e8a000;">./docs</code> folder exists and contains
                    your support documents <code style="background:#21262d;padding:0.1rem 0.4rem;
                    border-radius:4px;color:#e8a000;">(.txt or .pdf)</code>.<br><br>
                    See <strong style="color:#e6edf3;">README.md</strong> for setup instructions.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    elif not st.session_state.messages:
        # Connected but no messages yet — welcome + suggestions
        st.markdown("""
        <div class="welcome-wrap">
            <div class="welcome-icon">🔩</div>
            <div class="welcome-title">How can I help?</div>
            <div class="welcome-sub">
                Ask me anything about Steel Pro products, cutting services,
                pricing, delivery, or store information.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Suggestion chips — clicking one sets the input
        suggestions = [
            ("Products",  "What mild steel sections do you stock?"),
            ("Pricing",   "How much does plasma cutting cost?"),
            ("Services",  "Do you offer custom fabrication?"),
            ("Store",     "What are your trading hours?"),
            ("Delivery",  "What are your delivery charges?"),
            ("Returns",   "What is your returns policy?"),
        ]
        cols = st.columns(2)
        for i, (label, q) in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(f"**{label}**\n{q}", key=f"sug_{i}", use_container_width=True):
                    # Store as pending so it gets processed after the form renders
                    st.session_state["_pending_question"] = q
                    st.rerun()

    else:
        # Render conversation history
        for msg in st.session_state.messages:
            role   = msg["role"]
            text   = msg["content"]
            meta   = msg.get("meta", {})

            if role == "user":
                st.markdown(f"""
                <div class="msg-wrap user">
                    <div class="msg-avatar avatar-user">U</div>
                    <div class="msg-bubble bubble-user">{text}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                is_handoff  = meta.get("status") == "handoff"
                bubble_cls  = "bubble-bot handoff" if is_handoff else "bubble-bot"
                status_chip = (
                    '<span class="meta-chip chip-handoff">⚠ Escalated</span>'
                    if is_handoff else
                    '<span class="meta-chip chip-answered">✓ Answered</span>'
                )
                score  = meta.get("score", "—")
                sim    = meta.get("similarity", 0)
                sources = list(dict.fromkeys(meta.get("sources", [])))  # deduplicate
                src_chips = "".join(
                    f'<span class="meta-chip chip-source">📄 {s}</span>'
                    for s in sources
                ) if sources else '<span class="meta-chip chip-source">no source</span>'

                ticket_html = ""
                if meta.get("ticket"):
                    t = meta["ticket"]
                    ticket_html = (
                        f'<div class="ticket-badge">'
                        f'📋 Ticket <strong>{t["ticket_id"]}</strong> created &nbsp;·&nbsp; Priority: <strong>{t["priority"].upper()}</strong>'
                        f'</div>'
                    )

                # Build HTML as a single compact string — avoids Markdown
                # interpreting indented closing tags as code blocks
                html = (
                    f'<div class="msg-wrap">'
                    f'<div class="msg-avatar avatar-bot">SP</div>'
                    f'<div style="max-width:72%;">'
                    f'<div class="msg-bubble {bubble_cls}">{text}</div>'
                    f'<div class="msg-meta">'
                    f'{status_chip}'
                    f'<span class="meta-chip chip-score">⚡ {score}/10</span>'
                    f'<span class="meta-chip chip-sim">◎ {sim:.2f}</span>'
                    f'{src_chips}'
                    f'</div>'
                    f'{ticket_html}'
                    f'</div>'
                    f'</div>'
                )
                st.markdown(html, unsafe_allow_html=True)

    # ── end chat messages ──


# ── Input area (only shown when bot is ready) ─────────────────
if st.session_state.ready:

    st.markdown("---")

    # ── Check for prefilled suggestion from welcome chips ─────
    prefill = st.session_state.pop("prefill", "")
    if prefill:
        st.session_state["_pending_question"] = prefill

    # ── Input form — using st.form prevents double-submit ─────
    # st.form only triggers on explicit submit (Enter or button click)
    # and clears the input after submission automatically.
    with st.form(key="chat_form", clear_on_submit=True):
        col_input, col_send = st.columns([6, 1])
        with col_input:
            question = st.text_input(
                "message",
                placeholder="Ask about products, pricing, services…",
                label_visibility="collapsed",
            )
        with col_send:
            send = st.form_submit_button("Send →", use_container_width=True)

    # ── Process submitted question ────────────────────────────
    # Use a pending queue so the form clears before processing.
    # This prevents the same question firing twice on rerun.
    pending = st.session_state.pop("_pending_question", None)
    submitted_q = question.strip() if (send and question.strip()) else None

    # Pick whichever is set — submitted input takes priority
    q = submitted_q or pending

    if q:
        # Guard: don't process the same question twice in a row
        last_user_msg = next(
            (m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"),
            None,
        )
        if q == last_user_msg:
            pass   # duplicate — skip silently
        else:
            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": q})
            st.session_state.total_q += 1

            # Get bot response
            with st.spinner("Thinking…"):
                result = st.session_state.bot.chat(q)

            # Track handoffs and tickets
            if result["status"] == "handoff":
                st.session_state.total_handoff += 1
                if result.get("ticket"):
                    st.session_state.tickets.append(result["ticket"])

            # Add bot response to history
            st.session_state.messages.append({
                "role":    "assistant",
                "content": result["response"],
                "meta": {
                    "status":     result["status"],
                    "score":      result["confidence"].get("score", "—"),
                    "similarity": result.get("similarity", 0),
                    "sources":    result.get("sources", []),
                    "ticket":     result.get("ticket"),
                },
            })

            st.rerun()

    # Hint text
    st.markdown(
        '<div style="text-align:center;font-size:0.68rem;color:#7d8590;margin-top:0.3rem;">'
        'Press <strong style="color:#e8a000;">Enter</strong> or click '
        '<strong style="color:#e8a000;">Send</strong> to submit'
        '</div>',
        unsafe_allow_html=True,
    )