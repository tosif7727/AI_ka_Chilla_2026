# ── bot.py ─────────────────────────────────────────────────
# Core bot logic:
#   - retrieve()        → search ChromaDB for relevant docs
#   - eval_confidence() → keyword-based check (no extra LLM call)
#   - make_ticket()     → create a handoff ticket
#   - handoff_message() → generate escalation message
#   - SupportBot        → main class with chat() and stream_chat()
#
# Provider (OpenAI / Ollama) is read from config.LLM_PROVIDER
# which is set at runtime by main.py before this file is imported.
# ───────────────────────────────────────────────────────────

import uuid
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_chroma import Chroma
import config
from config import (
    TOP_K, SIM_THRESHOLD, CONF_THRESHOLD,
    UNCERTAINTY_PHRASES, SYSTEM_PROMPT, HANDOFF_PROMPT,
)


# ── LLM factory ──────────────────────────────────────────────

def get_llm(streaming: bool = False):
    """Return the correct LLM based on the selected provider."""
    if config.LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=config.OPENAI_CHAT_MODEL,
            api_key=config.OPENAI_API_KEY,
            temperature=0.1,
            streaming=streaming,
        )
    else:
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=config.OLLAMA_CHAT_MODEL,
            temperature=0.1,
            streaming=streaming,
        )


# ── Prompt template ───────────────────────────────────────────

rag_prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder("chat_history", optional=True),
    ("human", "{question}"),
])


# ── Retrieval ─────────────────────────────────────────────────

def retrieve(store: Chroma, query: str) -> tuple:
    """
    Search ChromaDB for the most relevant document chunks.
    Returns: (context_string, metadata_list, best_similarity_score)

    ChromaDB returns L2 distance (0 = identical, higher = less similar).
    We convert: similarity = 1 / (1 + distance) → range 0.0 to 1.0
    We use the BEST score across chunks to judge retrieval quality.
    """
    results = store.similarity_search_with_score(query, k=TOP_K)
    if not results:
        return "", [], 0.0

    parts = []
    meta  = []
    for doc, raw_score in results:
        similarity = round(1.0 / (1.0 + raw_score), 3)  # safe for any distance
        source = doc.metadata.get("source_file", "unknown")
        parts.append(f"[Source: {source}]\n{doc.page_content}")
        meta.append({"source": source, "score": similarity})

    context    = "\n\n---\n\n".join(parts)
    best_score = max(m["score"] for m in meta)  # best chunk = most relevant
    return context, meta, best_score

def eval_confidence(response: str, has_context: bool) -> dict:
    """
    Fast keyword-based confidence check — no extra LLM call needed.
    Returns a confidence dict with score and handoff recommendation.
    """
    uncertainty = any(phrase in response.lower() for phrase in UNCERTAINTY_PHRASES)
    score = 3 if uncertainty else 8

    return {
        "score": score,
        "uncertainty_detected": uncertainty,
        "handoff_recommended": uncertainty or not has_context,
    }


# ── Handoff helpers ───────────────────────────────────────────

def make_ticket(question: str, history: list, docs_meta: list, conf: dict) -> dict:
    """Create a structured support ticket dict for human agents."""
    return {
        "ticket_id":  f"TICKET-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}",
        "created_at": datetime.now().isoformat(),
        "question":   question,
        "history":    history[-5:],
        "sources":    docs_meta,
        "confidence": conf,
        "priority":   "high" if conf.get("score", 0) < 4 else "medium",
    }


def handoff_message(question: str, reason: str) -> str:
    """Generate a polite escalation message for the customer."""
    llm   = get_llm()
    chain = (
        ChatPromptTemplate.from_messages([("human", HANDOFF_PROMPT)])
        | llm
        | StrOutputParser()
    )
    return chain.invoke({"question": question, "reason": reason})


# ── SupportBot ────────────────────────────────────────────────

class SupportBot:
    """
    RAG-powered customer support bot.

    Flow for each question:
      1. Retrieve relevant docs from ChromaDB
      2. Generate an answer using the LLM + retrieved context
      3. Check confidence (keyword-based, fast)
      4. If confident  → return the answer
         If not sure   → create a ticket + return escalation message
    """

    def __init__(self, store: Chroma):
        self.store   = store
        self.history = []   # full conversation memory
        self.tickets = []   # all handoff tickets this session
        self.llm     = get_llm()
        self.chain   = rag_prompt | self.llm | StrOutputParser()

    def chat(self, question: str) -> dict:
        """
        Main method. Send a question, get a response dict back.

        Returns:
            response  (str)  — the bot's answer or escalation message
            status    (str)  — "answered" or "handoff"
            confidence(dict) — score, uncertainty_detected
            sources   (list) — filenames used to answer
            ticket    (dict) — filled only when status = "handoff"
            similarity(float)— raw similarity score (useful for debugging)
        """
        # 1. Retrieve relevant docs
        context, docs_meta, best_score = retrieve(self.store, question)

        # 2. Build chat history for the prompt (last 3 exchanges = 6 messages)
        chat_history = [
            HumanMessage(content=m["content"]) if m["role"] == "user"
            else AIMessage(content=m["content"])
            for m in self.history[-6:]
        ]

        # 3. Generate answer
        response = self.chain.invoke({
            "context":      context or "No relevant information found in the knowledge base.",
            "question":     question,
            "chat_history": chat_history,
        })

        # 4. Check confidence
        conf = eval_confidence(response, bool(docs_meta))

        # 5. Decide: answer or escalate
        #    best_score uses 1/(1+distance) so typical good matches = 0.3–0.6
        #    SIM_THRESHOLD = 0.15 means only truly irrelevant queries handoff
        needs_handoff = (
            not docs_meta                        # no docs retrieved at all
            or best_score < SIM_THRESHOLD        # best chunk is still a poor match
            or conf.get("uncertainty_detected")  # bot said "I don't know" etc.
        )

        # 6. Save to conversation history
        self.history += [
            {"role": "user",      "content": question},
            {"role": "assistant", "content": response},
        ]

        # 7. Build and return result
        base = {
            "confidence": conf,
            "sources":    [m["source"] for m in docs_meta],
            "similarity": best_score,
        }

        if needs_handoff:
            ticket = make_ticket(question, self.history, docs_meta, conf)
            self.tickets.append(ticket)
            return {
                **base,
                "response": handoff_message(question, "Bot was unable to answer confidently."),
                "status":   "handoff",
                "ticket":   ticket,
            }

        return {
            **base,
            "response": response,
            "status":   "answered",
            "ticket":   None,
        }

    def stream_chat(self, question: str):
        """
        Stream the response token by token.
        Yields {"type": "token",    "content": "..."}  — one per token
        Yields {"type": "metadata", ...}               — once at the end
        """
        context, docs_meta, best_score = retrieve(self.store, question)

        streaming_chain = rag_prompt | get_llm(streaming=True) | StrOutputParser()

        full = ""
        for token in streaming_chain.stream({
            "context":      context or "No relevant information found.",
            "question":     question,
            "chat_history": [],
        }):
            full += token
            yield {"type": "token", "content": token}

        # Post-stream confidence check
        conf = eval_confidence(full, bool(docs_meta))
        self.history += [
            {"role": "user",      "content": question},
            {"role": "assistant", "content": full},
        ]

        yield {
            "type":       "metadata",
            "status":     "handoff" if conf.get("handoff_recommended") else "answered",
            "score":      conf.get("score", 0),
            "similarity": best_score,
            "sources":    [m["source"] for m in docs_meta],
        }