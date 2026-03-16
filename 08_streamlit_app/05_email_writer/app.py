import streamlit as st
import os
import json
from pathlib import Path
from email_generator import init_llm, generate_email_enhanced

# ── Page config ───────────────────────────────
st.set_page_config(
    page_title="MailCraft — AI Email Writer",
    page_icon="✉️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Credentials file (saved next to app.py) ───
CONFIG_FILE = Path(__file__).parent / ".mailcraft_config.json"

def load_config():
    """Load saved credentials from disk."""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception:
            return {}
    return {}

def save_config(data: dict):
    """Persist credentials to disk."""
    CONFIG_FILE.write_text(json.dumps(data, indent=2))

cfg = load_config()

# ── CSS ───────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --bg:      #f5f7fa;
    --white:   #ffffff;
    --border:  #e2e6ed;
    --muted:   #8a94a6;
    --body:    #374151;
    --heading: #111827;
    --blue:    #3b82f6;
    --blue-lt: #eff6ff;
    --purple:  #7c3aed;
    --green:   #059669;
    --red:     #dc2626;
    --r:       10px;
    --shadow:  0 1px 4px rgba(0,0,0,0.07), 0 4px 16px rgba(0,0,0,0.05);
}

*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp {
    background: var(--bg) !important;
    font-family: 'Inter', sans-serif !important;
    color: var(--body) !important;
}

#MainMenu, footer, header { visibility: hidden !important; }

.block-container {
    padding: 2.5rem 1.5rem 4rem !important;
    max-width: 700px !important;
}

/* Labels */
label, .stTextArea label, .stTextInput label, .stSelectbox label {
    font-size: 0.73rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
    color: var(--muted) !important;
}

/* Inputs */
.stTextArea textarea, .stTextInput input {
    background: var(--white) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r) !important;
    color: var(--heading) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.93rem !important;
    box-shadow: none !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: var(--blue) !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.12) !important;
    outline: none !important;
}

/* Selectbox */
.stSelectbox [data-baseweb="select"] > div {
    background: var(--white) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r) !important;
    color: var(--heading) !important;
    box-shadow: none !important;
}
[data-baseweb="popover"] [role="listbox"] {
    background: var(--white) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r) !important;
    box-shadow: var(--shadow) !important;
}
[data-baseweb="popover"] [role="option"] {
    color: var(--body) !important;
    font-size: 0.9rem !important;
}
[data-baseweb="popover"] [role="option"]:hover,
[data-baseweb="popover"] [aria-selected="true"] {
    background: var(--blue-lt) !important;
    color: var(--blue) !important;
}

/* Primary button */
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    border-radius: var(--r) !important;
    border: none !important;
    background: linear-gradient(135deg, var(--blue) 0%, var(--purple) 100%) !important;
    color: #fff !important;
    padding: 0.65rem 1.4rem !important;
    box-shadow: 0 2px 10px rgba(59,130,246,0.25) !important;
    transition: filter 0.15s ease, transform 0.15s ease !important;
}
.stButton > button:hover { filter: brightness(1.07) !important; transform: translateY(-1px) !important; }
.stButton > button:active { transform: none !important; }

/* Download button */
.stDownloadButton > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    border-radius: var(--r) !important;
    background: var(--white) !important;
    color: var(--body) !important;
    border: 1px solid var(--border) !important;
    box-shadow: none !important;
}
.stDownloadButton > button:hover { border-color: var(--blue) !important; color: var(--blue) !important; }

/* Alerts */
div[data-testid="stNotification"], .stAlert {
    animation: none !important;
    transition: none !important;
    border-radius: var(--r) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.87rem !important;
}

/* Spinner */
.stSpinner > div { border-top-color: var(--blue) !important; }

/* Expander */
.streamlit-expanderHeader {
    background: var(--white) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r) !important;
    color: var(--body) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.87rem !important;
}
.streamlit-expanderContent {
    background: var(--white) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
    border-bottom-left-radius: var(--r) !important;
    border-bottom-right-radius: var(--r) !important;
    padding: 1rem !important;
}

/* Divider */
hr { border: none !important; border-top: 1px solid var(--border) !important; margin: 1.4rem 0 !important; }

/* Checkbox */
.stCheckbox label { text-transform: none !important; letter-spacing: 0 !important; font-size: 0.83rem !important; color: var(--muted) !important; }

/* Saved badge */
.mc-saved {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    background: #ecfdf5;
    border: 1px solid #a7f3d0;
    color: #059669;
    border-radius: 999px;
    padding: 0.2rem 0.7rem;
    font-size: 0.75rem;
    font-weight: 600;
}

/* Email output */
.mc-out {
    background: #fafbfc;
    border: 1px solid var(--border);
    border-left: 3px solid var(--blue);
    border-radius: var(--r);
    padding: 1.3rem 1.5rem;
    font-size: 0.92rem;
    line-height: 1.85;
    color: var(--body);
    white-space: pre-wrap;
    word-break: break-word;
    margin-bottom: 0.9rem;
}

/* Tip box */
.mc-tip {
    background: var(--blue-lt);
    border: 1px solid #bfdbfe;
    border-radius: var(--r);
    padding: 0.7rem 1rem;
    font-size: 0.81rem;
    color: #374151;
    line-height: 1.55;
    margin-top: 0.8rem;
}

[data-testid="stSidebar"] {
    background: var(--white) !important;
    border-right: 1px solid var(--border) !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────
if "email_out" not in st.session_state:
    st.session_state.email_out = None

TONES = {
    "Professional": "💼", "Friendly": "😊", "Casual": "👋",
    "Formal": "🎩", "Urgent": "⚡", "Apologetic": "🙏",
}

# ── Header ────────────────────────────────────
st.markdown(
    '<h1 style="font-family:Inter,sans-serif;font-size:1.9rem;font-weight:700;'
    'color:#111827;letter-spacing:-0.02em;margin-bottom:0.1rem;">✉️ MailCraft</h1>'
    '<p style="color:#8a94a6;margin-bottom:1rem;font-size:0.9rem;">'
    'Turn bullet points into a polished email in seconds.</p>',
    unsafe_allow_html=True,
)

# ════════════════════════════════════════════
# SETTINGS — saved credentials (collapsible)
# ════════════════════════════════════════════
creds_saved = bool(cfg.get("api_key"))
expander_label = "⚙️ Settings  ✓ Credentials saved" if creds_saved else "⚙️ Settings — set up your credentials once"

with st.expander(expander_label, expanded=not creds_saved):
    st.markdown(
        '<p style="font-size:0.82rem;color:#8a94a6;margin-bottom:0.8rem;">'
        'Saved once on your machine — no need to re-enter every visit.</p>',
        unsafe_allow_html=True,
    )

    e1, e2 = st.columns(2)
    with e1:
        inp_api = st.text_input(
            "OpenAI API Key",
            type="password",
            value=cfg.get("api_key", ""),
            placeholder="sk-...",
        )
        inp_from_name = st.text_input(
            "Your name (sender)",
            value=cfg.get("from_name", ""),
            placeholder="Jane Doe",
        )
        inp_provider = st.selectbox(
            "Email provider",
            ["auto", "gmail", "outlook", "yahoo"],
            index=["auto", "gmail", "outlook", "yahoo"].index(cfg.get("provider", "auto")),
            format_func=lambda x: {"auto": "🔄 Auto", "gmail": "Gmail",
                                    "outlook": "Outlook", "yahoo": "Yahoo"}[x],
        )
    with e2:
        inp_from_email = st.text_input(
            "Your email (sender)",
            value=cfg.get("from_email", ""),
            placeholder="you@gmail.com",
        )
        inp_app_pw = st.text_input(
            "App password",
            type="password",
            value=cfg.get("app_pw", ""),
        )

    st.markdown(
        '<div class="mc-tip">'
        '<strong>Gmail / Yahoo:</strong> use an App Password, not your login password. '
        '<strong>Outlook:</strong> normal password works if SMTP is enabled.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 Save credentials", use_container_width=True):
        save_config({
            "api_key":    inp_api.strip(),
            "from_name":  inp_from_name.strip(),
            "from_email": inp_from_email.strip(),
            "app_pw":     inp_app_pw.strip(),
            "provider":   inp_provider,
        })
        cfg = load_config()
        st.success("Credentials saved! This expander will stay collapsed from now on.")
        st.rerun()

# ── Pull saved values for use below ───────────
api_key    = cfg.get("api_key", "").strip()
from_name  = cfg.get("from_name", "").strip()
from_email = cfg.get("from_email", "").strip()
app_pw     = cfg.get("app_pw", "").strip()
provider   = cfg.get("provider", "auto")

if not api_key:
    st.warning("Open ⚙️ Settings above and save your OpenAI API key to get started.")
    st.stop()

st.markdown("---")

# ════════════════════════════════════════════
# COMPOSE — the only thing user does daily
# ════════════════════════════════════════════
notes = st.text_area(
    "Your notes",
    height=120,
    placeholder="• Follow up on proposal sent Monday\n• Ask about budget approval\n• Suggest a quick call this week",
)

col1, col2, col3 = st.columns(3)
with col1:
    tone = st.selectbox("Tone", list(TONES.keys()), format_func=lambda x: f"{TONES[x]} {x}")
with col2:
    to_name = st.text_input("Recipient name", placeholder="John Smith")
with col3:
    to_email = st.text_input("Recipient email", placeholder="john@company.com")

if st.button("✨ Generate Email", use_container_width=True):
    if not notes.strip():
        st.error("Please add some notes first.")
    else:
        with st.spinner("Writing your email…"):
            llm = init_llm(api_key)
            st.session_state.email_out = generate_email_enhanced(
                notes, tone, to_name or None, from_name or None, llm
            )

# ════════════════════════════════════════════
# OUTPUT + ONE-CLICK SEND
# ════════════════════════════════════════════
if st.session_state.email_out:
    st.markdown("---")

    st.markdown(
        f'<div class="mc-out">{st.session_state.email_out}</div>',
        unsafe_allow_html=True,
    )

    a1, a2, a3, _ = st.columns([1.4, 1.1, 1.1, 1])
    with a1:
        st.download_button(
            "📥 Download",
            data=st.session_state.email_out,
            file_name="email.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with a2:
        # One-click send — credentials already saved
        if st.button("🚀 Send", use_container_width=True):
            if not to_email.strip():
                st.error("Enter a recipient email above.")
            elif not from_email or not app_pw:
                st.error("Open ⚙️ Settings and save your sender email & app password first.")
            else:
                lines = st.session_state.email_out.strip().splitlines()
                subj, body = "", []
                for i, ln in enumerate(lines):
                    if ln.lower().startswith("subject:"):
                        subj, body = ln[8:].strip(), lines[i + 1:]
                        break
                if not subj and lines:
                    subj, body = lines[0], lines[1:]
                try:
                    from email_sender import send_email as send
                    send(
                        generated_content={
                            "subject": subj or "Email",
                            "body": "\n".join(body).strip(),
                        },
                        recipient_email=to_email.strip(),
                        sender_email=from_email,
                        sender_password=app_pw,
                        provider=provider,
                    )
                    st.success(f"Sent to {to_email} ✓")
                except Exception as e:
                    st.error(str(e))
    with a3:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.email_out = None
            st.rerun()

# ── Footer ────────────────────────────────────
st.markdown(
    '<p style="text-align:center;color:#c0c8d4;font-size:0.75rem;margin-top:2.5rem;">'
    'Built by <a href="https://github.com/tosif7727" style="color:#3b82f6;text-decoration:none;">Touseef Afridi</a>'
    ' · Mentored by <a href="https://www.youtube.com/c/Codanics" style="color:#7c3aed;text-decoration:none;">Dr. Ammar Tufail @ Codanics</a>'
    '</p>',
    unsafe_allow_html=True,
)