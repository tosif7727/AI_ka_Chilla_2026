# 🔩 Steel Pro — AI Customer Support Bot

A RAG-powered support bot that answers questions from your own documents.
Supports **OpenAI** and **Ollama**, with a Streamlit web UI and terminal interface.

---

## 🧱 Project Structure

```
steel-pro-support-bot/
├── app.py            ← Streamlit web UI
├── main.py           ← Terminal interface
├── bot.py            ← Core logic (retrieval, confidence, handoff)
├── ingest.py         ← Load docs → embed → save to ChromaDB
├── config.py         ← All settings (edit here to customise)
├── requirements.txt  ← Dependencies
└── docs/             ← ⚠️ YOU must create this with your files
```

> `chroma_db/` is created automatically on first run — do not edit it.

---

## ⚠️ Before Anything — Create Your Docs Folder

The bot **will not start** without this step.

```bash
mkdir docs
```

Add your `.txt` or `.pdf` support documents inside:

```
docs/
├── product_catalog.txt
├── services_pricing.txt
└── faq_store_info.txt
```

> After adding or editing docs, always delete `chroma_db/` and restart to rebuild.

---

## 🛠️ Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install Ollama from https://ollama.com then pull models
ollama pull nomic-embed-text   # required — used for embeddings always
ollama pull llama3.2           # required only if using Ollama for chat
ollama serve                   # keep running in background
```

**OpenAI users** — set your API key:
```bash
export OPENAI_API_KEY=sk-...   # Mac/Linux
set OPENAI_API_KEY=sk-...      # Windows
```

---

## ▶️ Running

```bash
# Web UI (recommended)
streamlit run app.py

# Terminal
python main.py
```

On startup, pick your provider:

| | OpenAI | Ollama |
|---|---|---|
| Speed | ~1–2 sec | Depends on hardware |
| Cost | Paid | Free |
| Privacy | Cloud | 100% local |
| Requires | API key | `ollama serve` |

> Ollama **always** handles embeddings regardless of which chat provider you pick.

---

## 📊 Understanding the Response

```
🤖 Bot: Plasma cutting starts at $8.00 per cut. [Source: services_pricing.txt]
   ✓ Answered  ⚡ 8/10  ◎ 0.41  📄 services_pricing.txt
```

| Field | Meaning |
|---|---|
| `✓ Answered` / `⚠ Escalated` | Confident answer or escalated to human |
| `⚡ 8/10` | Confidence score |
| `◎ 0.41` | Doc similarity — above 0.25 is a good match |
| `📄 file.txt` | Source document used |

---

## ⚙️ Configuration (`config.py`)

```python
OPENAI_CHAT_MODEL  = "gpt-4o-mini"      # swap to "gpt-4o" for higher quality
OLLAMA_CHAT_MODEL  = "llama3.2"         # swap to "llama3.2:1b" for faster local
OLLAMA_EMBED_MODEL = "nomic-embed-text" # embeddings — always Ollama

SIM_THRESHOLD  = 0.15   # similarity below this → escalate to human
TOP_K          = 4      # number of doc chunks retrieved per question
```

---

## ❗ Common Issues

| Problem | Fix |
|---|---|
| `./docs folder not found` | Run `mkdir docs` and add your files |
| `./docs folder is empty` | Add `.txt` or `.pdf` files to `./docs/` |
| `Connection refused` | Run `ollama serve` |
| `model not found` | Run `ollama pull nomic-embed-text` |
| Invalid API key | Key must start with `sk-` |
| Too many handoffs | Lower `SIM_THRESHOLD` to `0.10` in `config.py` |
| Wrong/outdated answers | Delete `chroma_db/` and restart |
| Ollama very slow | Switch to `llama3.2:1b` in `config.py` |
| `streamlit: command not found` | Run `pip install streamlit` |

---

## 👨‍💻 Created By

**Touseef Afridi**

[![GitHub](https://img.shields.io/badge/GitHub-@Touseef--Afridi-181717?style=flat-square&logo=github)](https://github.com/tosif7727)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Touseef%20Afridi-0A66C2?style=flat-square&logo=linkedin)](https://linkedin.com/in/touseef-afridi)

---

## 🎓 Credits

This project was built under the guidance of:

**Dr. Muhammad Aammar Tufail**
Instructor & AI Expert

[![GitHub](https://img.shields.io/badge/GitHub-Dr.%20Aammar-181717?style=flat-square&logo=github)](https://github.com/AammarTufail/)
[![YouTube](https://img.shields.io/badge/YouTube-Codanics-FF0000?style=flat-square&logo=youtube)](https://www.youtube.com/Codanics)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Dr.%20Aammar-0A66C2?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/aammar-tufail/)

---

<div align="center">

**Codanics** — AI & Data Science Training Platform

[![Codanics](https://img.shields.io/badge/Codanics-Visit%20Platform-brightgreen?style=flat-square)](https://codanics.com)
[![YouTube](https://img.shields.io/badge/YouTube-Codanics-FF0000?style=flat-square&logo=youtube)](https://www.youtube.com/@Codanics)

*Learn AI · Build Projects · Get Hired*

</div>