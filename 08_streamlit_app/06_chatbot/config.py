# ── config.py ──────────────────────────────────────────────
# All settings in one place. Only edit this file to configure
# the bot — no need to touch bot.py, ingest.py, or main.py.
# ───────────────────────────────────────────────────────────

import os

# ── Provider ─────────────────────────────────────────────────
# This is set at runtime by main.py when the user picks a provider.
# Do not change this manually — it will be overwritten on startup.
LLM_PROVIDER = "ollama"   # "openai" or "ollama"

# ── OpenAI Settings ──────────────────────────────────────────
# Used when LLM_PROVIDER = "openai"
# Set via environment variable or entered at startup — do not hardcode keys here.
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY", "")
OPENAI_CHAT_MODEL = "gpt-4o-mini"   # chat only. Options: gpt-4o, gpt-4-turbo
# OPENAI_EMBED_MODEL = "text-embedding-3-small"  # used regardless of LLM_PROVIDER

# ── Ollama Settings ───────────────────────────────────────────
# Ollama is ALWAYS used for embeddings (free, local, no API cost).
# If LLM_PROVIDER = "ollama", Ollama is also used for chat.
# Make sure Ollama is running: ollama serve
OLLAMA_CHAT_MODEL  = "llama3.2"
OLLAMA_EMBED_MODEL = "nomic-embed-text"   # used regardless of LLM_PROVIDER

# ── Paths ─────────────────────────────────────────────────────
CHROMA_DIR = "./chroma_db"   # where ChromaDB stores vectors
DOCS_DIR   = "./docs"        # where your support documents live

# ── Retrieval ─────────────────────────────────────────────────
TOP_K         = 4     # number of doc chunks to retrieve per query
SIM_THRESHOLD = 0.15  # similarity below this → handoff
                      # Scores use 1/(1+distance), typical range 0.2–0.6
                      # 0.15 = only truly irrelevant queries escalate

# ── Confidence ────────────────────────────────────────────────
CONF_THRESHOLD = 4    # keyword confidence score below this → handoff

# ── Uncertainty phrases ───────────────────────────────────────
# If the bot's response contains any of these, it triggers a handoff
UNCERTAINTY_PHRASES = [
    "i don't know", "not sure", "i cannot", "i can't",
    "no information", "outside my knowledge", "i do not have",
    "i'm not sure", "i am not sure", "cannot provide",
]

# ── Prompts ───────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a professional customer support assistant for a steel hardware shop.
Answer ONLY using the information from the context below.
Always cite your source using [Source: filename] at the end of your answer.
If the context does not contain enough information to answer, say exactly:
"I don't have enough information to answer that."

Context:
{context}"""

HANDOFF_PROMPT = """Write a short 2-3 sentence professional message to a customer explaining:
- They are being transferred to a human specialist
- The specialist will have full context of their issue
- They should expect a response shortly

Customer question: {question}
Reason for escalation: {reason}"""