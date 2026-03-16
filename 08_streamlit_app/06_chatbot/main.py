# ── main.py ────────────────────────────────────────────────
# Entry point for the Customer Support Bot.
#
# On startup:
#   1. Shows a provider selection menu (OpenAI or Ollama)
#   2. If OpenAI is chosen, prompts for the API key
#   3. Loads (or builds) the ChromaDB knowledge base
#   4. Starts an interactive chat loop
#
# The bot only responds when the user types a question.
# Type 'quit', 'exit', or 'bye' to stop.
# ───────────────────────────────────────────────────────────

import os
import sys
import shutil
import config
from config import CHROMA_DIR, DOCS_DIR


# ── Provider selection ────────────────────────────────────────

def pick_provider() -> str:
    """Show a menu and return the chosen provider string."""
    print()
    print("┌──────────────────────────────────────────┐")
    print("│           Select AI Provider             │")
    print("├──────────────────────────────────────────┤")
    print("│  1. OpenAI  (fast, requires API key)     │")
    print("│  2. Ollama  (free, runs locally)         │")
    print("└──────────────────────────────────────────┘")

    while True:
        choice = input("\nEnter 1 or 2: ").strip()
        if choice == "1":
            return "openai"
        elif choice == "2":
            return "ollama"
        print("  ❌ Please enter 1 or 2.")


def get_openai_key() -> str:
    """
    Get the OpenAI API key.
    Checks environment variable first, then prompts the user.
    """
    # Check if already set in environment
    env_key = os.getenv("OPENAI_API_KEY", "")
    if env_key.startswith("sk-") and len(env_key) > 20:
        print("  ✅ API key loaded from environment variable.")
        return env_key

    # Prompt the user
    print()
    print("  🔑 Enter your OpenAI API key:")
    print("     (Get one at https://platform.openai.com/api-keys)")
    while True:
        key = input("\n  API Key: ").strip()
        if key.startswith("sk-") and len(key) > 20:
            return key
        print("  ❌ Invalid key. It should start with 'sk-'. Try again.")


def apply_provider(provider: str):
    """
    Set the provider in config at runtime.
    bot.py and ingest.py are imported AFTER this runs,
    so they will always see the correct provider.
    """
    config.LLM_PROVIDER = provider

    if provider == "openai":
        key = get_openai_key()
        config.OPENAI_API_KEY = key
        os.environ["OPENAI_API_KEY"] = key   # ensure LangChain picks it up
        print(f"\n  ✅ Provider : OpenAI ({config.OPENAI_CHAT_MODEL})")
        print(f"  ✅ Embedding: {config.OPENAI_EMBED_MODEL}")
    else:
        print(f"\n  ✅ Provider : Ollama ({config.OLLAMA_CHAT_MODEL})")
        print(f"  ✅ Embedding: {config.OLLAMA_EMBED_MODEL}")
        print("     Make sure Ollama is running → ollama serve")


# ── Knowledge base setup ──────────────────────────────────────

def validate_docs() -> bool:
    """
    Check that ./docs exists and contains at least one .txt or .pdf file.
    Print a clear error and return False if not.
    """
    if not os.path.exists(DOCS_DIR):
        print()
        print("  ❌ ERROR: ./docs folder not found.")
        print()
        print("  Please create a ./docs folder and add your support")
        print("  documents (.txt or .pdf) before running the bot.")
        print()
        print("  Example:")
        print("    docs/")
        print("    ├── product_catalog.txt")
        print("    ├── services_pricing.txt")
        print("    └── faq_store_info.txt")
        print()
        print("  See README.md for full setup instructions.")
        return False

    valid_files = [
        f for f in os.listdir(DOCS_DIR)
        if f.endswith(".txt") or f.endswith(".pdf")
    ]

    if not valid_files:
        print()
        print("  ❌ ERROR: ./docs folder is empty.")
        print()
        print(f"  Found folder: {DOCS_DIR}/")
        print("  But no .txt or .pdf files were found inside it.")
        print()
        print("  Add your support documents and restart the bot.")
        print("  See README.md for full setup instructions.")
        return False

    print(f"  📂 Found {len(valid_files)} document(s) in {DOCS_DIR}/")
    return True


def setup_knowledge_base():
    """
    Validate docs folder, then load or build the ChromaDB vector store.
    Exits cleanly with a helpful message if docs are missing.
    """
    from ingest import ingest, load_store

    # Validate before doing anything
    if not validate_docs():
        sys.exit(1)

    # Load existing store or build a new one
    if os.path.exists(CHROMA_DIR) and os.listdir(CHROMA_DIR):
        print("  📦 Loading existing knowledge base...")
        return load_store()
    else:
        print("  🔧 Building knowledge base from docs (first time only)...")
        return ingest(DOCS_DIR)



# ── Output formatting ─────────────────────────────────────────

def print_result(result: dict):
    """Print the bot response with status, score, similarity, and sources."""
    print(f"\n🤖 Bot: {result['response']}")
    print(f"   ├─ Status     : {result['status'].upper()}")
    print(f"   ├─ Confidence : {result['confidence'].get('score', '?')}/10")
    print(f"   ├─ Similarity : {result.get('similarity', 0):.2f}")
    print(f"   └─ Sources    : {', '.join(result['sources']) if result['sources'] else 'none'}")

    if result.get("ticket"):
        t = result["ticket"]
        print(f"\n   📋 Ticket {t['ticket_id']} created  (priority: {t['priority']})")


# ── Main ──────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print("    Steel Pro Customer Support Bot")
    print("=" * 50)

    # Step 1: Pick provider and configure
    provider = pick_provider()
    apply_provider(provider)

    # Step 2: Import bot AFTER config is set
    # (bot.py reads config.LLM_PROVIDER at import time)
    from bot import SupportBot

    # Step 3: Setup knowledge base
    print()
    store = setup_knowledge_base()

    # Step 4: Start the bot
    bot = SupportBot(store)
    print(f"\n{'=' * 50}")
    print("  ✅ Ready! Type your question below.")
    print("  Type 'quit' to exit.")
    print(f"{'=' * 50}\n")

    # Step 5: Chat loop — bot only speaks when user asks
    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye!")
            break

        if not question:
            continue   # ignore empty Enter presses

        if question.lower() in ("quit", "exit", "bye"):
            print("Goodbye!")
            break

        result = bot.chat(question)
        print_result(result)
        print()


if __name__ == "__main__":
    main()