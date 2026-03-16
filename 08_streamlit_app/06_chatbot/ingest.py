# ── ingest.py ──────────────────────────────────────────────
# Handles loading documents from ./docs, splitting them into
# chunks, embedding them, and saving to ChromaDB.
#
# Supports OpenAI or Ollama embeddings — controlled by
# LLM_PROVIDER in config.py (set at runtime by main.py).
# ───────────────────────────────────────────────────────────

import os
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import config
from config import CHROMA_DIR, DOCS_DIR


def get_embeddings():
    """
    Always use Ollama for embeddings — free and local.
    This applies even when LLM_PROVIDER = "openai" for chat.
    Make sure Ollama is running: ollama serve
    """
    from langchain_ollama import OllamaEmbeddings
    return OllamaEmbeddings(model=config.OLLAMA_EMBED_MODEL)


def ingest(docs_dir: str = DOCS_DIR) -> Chroma:
    """
    Full pipeline: load docs → split into chunks → embed → save to ChromaDB.
    Returns the ChromaDB vector store.
    """
    # Load documents (.txt and .pdf supported)
    loaders = {
        "**/*.txt": TextLoader,
        "**/*.pdf": PyPDFLoader,
    }
    docs = []
    for glob, loader_cls in loaders.items():
        try:
            loaded = DirectoryLoader(docs_dir, glob=glob, loader_cls=loader_cls).load()
            docs.extend(loaded)
        except Exception:
            pass

    if not docs:
        print("⚠️  No documents found in", docs_dir)
        return load_store()

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)

    # Add clean filename to metadata
    for chunk in chunks:
        chunk.metadata["source_file"] = os.path.basename(
            chunk.metadata.get("source", "unknown")
        )

    print(f"✅ Ingested {len(docs)} docs → {len(chunks)} chunks  [{config.LLM_PROVIDER} embeddings]")

    embeddings = get_embeddings()
    return Chroma.from_documents(
        chunks,
        embeddings,
        collection_name="support",
        persist_directory=CHROMA_DIR,
    )


def load_store() -> Chroma:
    """Load an existing ChromaDB vector store from disk."""
    embeddings = get_embeddings()
    return Chroma(
        collection_name="support",
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )