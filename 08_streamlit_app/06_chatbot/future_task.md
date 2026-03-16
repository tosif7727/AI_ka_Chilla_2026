# 🚀 Future Improvements — Steel Pro Support Bot

A tracked list of planned improvements. Check off items as they are completed.

---

## 🧠 Better Answers

- [ ] **Query rewriting**
  Before searching ChromaDB, rephrase the user's short input into a full search query.
  Example: `"round bar"` → `"What sizes and prices are available for mild steel round bar?"`

- [ ] **Hybrid search**
  Combine keyword search (BM25) + vector search together.
  Currently only vector search is used, so exact terms like product codes or prices can be missed.

- [ ] **Reranking**
  After retrieving chunks, use a reranker model to re-order them by true relevance
  before passing to the LLM. Better context = better answers.

---

## 💬 Better Conversation

- [ ] **Conversation summarisation**
  After 10+ messages, summarise older messages into one paragraph to keep the
  prompt small and fast instead of growing indefinitely.

- [ ] **Follow-up awareness**
  If the user asks `"how much does it cost?"` after asking about round bar,
  the bot should understand `"it"` refers to round bar using smarter history handling.

---

## 🛡️ Better Reliability

- [ ] **Guardrails**
  Detect off-topic questions (weather, sports, politics) before hitting the LLM
  and instantly return a polite redirect without wasting API calls.

- [ ] **Input validation**
  Reject very short inputs (under 3 characters), gibberish, or special character
  spam before processing.

- [ ] **Fallback model**
  If OpenAI fails (rate limit or outage), automatically retry with Ollama
  instead of crashing.

---

## 📊 Better Visibility

- [ ] **Logging**
  Save every question, answer, similarity score, and status to a `.log` or `.csv`
  file. Useful for spotting what the bot gets wrong over time.

- [ ] **Ticket dashboard**
  Export all handoff tickets to a JSON or CSV file at the end of each session
  so human agents can review them easily.

---

## ⚡ Better Speed

- [ ] **Answer caching**
  Cache answers to frequently asked questions. If the same question is asked
  twice, return the stored answer instantly without hitting the LLM.

- [ ] **Async processing**
  Run retrieval and LLM generation concurrently where possible to reduce
  response time.

---

## 📁 Better Knowledge Base

- [ ] **Auto re-ingest**
  Watch the `./docs` folder for changes. If a file is added or modified,
  automatically rebuild ChromaDB without restarting the bot.

- [ ] **Source deduplication**
  Currently the same filename can appear multiple times in Sources.
  Deduplicate so each source file only shows once per response.

- [ ] **Metadata filtering**
  Tag documents by category (products, services, faq) and filter retrieval
  by category based on the question type before searching ChromaDB.

---

## ✅ Completed

- [x] Basic RAG pipeline (retrieve → answer)
- [x] OpenAI + Ollama provider support with startup menu
- [x] Ollama embeddings always used (free, no API cost)
- [x] Keyword-based confidence check (no extra LLM call)
- [x] Human handoff with support ticket creation
- [x] Fixed similarity score formula (`1 / (1 + distance)`)
- [x] Fixed handoff using best chunk score instead of worst
- [x] Lowered `SIM_THRESHOLD` to `0.15` to reduce false escalations
- [x] Interactive chat loop (bot only replies when user asks)
- [x] Split into clean separate files (`config`, `ingest`, `bot`, `main`)
- [x] Steel hardware shop sample documents created