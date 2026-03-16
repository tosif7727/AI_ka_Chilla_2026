"""
email_sender.py — LangGraph Email Delivery Workflow
=====================================================

Architecture:
                                                    ┌──────────────┐
START → parse_email_content → select_provider ──►  │  send_gmail  │ ──► delivery_confirmed → END
                                    │               └──────────────┘          ▲
                                    │          fail  ┌──────────────┐         │
                                    └──────────────► │ send_outlook │ ──►─────┤
                                                     └──────────────┘    fail │
                                                     ┌──────────────┐         │
                                                     │  send_yahoo  │ ──►─────┘
                                                     └──────────────┘
                                                           │ fail
                                                     delivery_failed → END

The SEND nodes are the critical path — everything else supports delivery.
Retry logic: each provider node retries up to 3× before handing off.
"""

import smtplib
import re
import uuid
import logging
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Literal, Optional, Any

from pydantic import BaseModel, field_validator
from langgraph.graph import StateGraph, END

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# CUSTOM EXCEPTION
# ──────────────────────────────────────────────

class DeliveryError(Exception):
    """Raised when email could not be delivered after all retries/fallbacks."""
    pass


# ──────────────────────────────────────────────
# PYDANTIC STATE MODEL
# ──────────────────────────────────────────────

class EmailWorkflowState(BaseModel):
    """Tracks every stage of the email delivery transaction."""

    # INPUT (immutable after init)
    recipient_email: str                                  # WHERE the email will be sent
    generated_content: dict = {}                          # subject, body, sender from generator
    provider_choice: Literal["gmail", "outlook", "yahoo", "auto"] = "auto"
    sender_credentials: dict = {}                         # {"email": ..., "password": ...}

    # RUNTIME STATE
    delivery_status: Literal["pending", "sent", "failed"] = "pending"
    provider_attempts: list = []                          # chain of providers tried
    current_provider: Optional[str] = None
    retry_count: int = 0

    # OUTPUT
    message_id: Optional[str] = None
    final_result: Optional[str] = None
    error_detail: Optional[str] = None

    @field_validator("recipient_email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        pattern = r"^[a-zA-Z0-9_.+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-.]+$"
        if not re.match(pattern, v):
            raise ValueError(f"Invalid email address: {v}")
        return v.strip().lower()

    class Config:
        arbitrary_types_allowed = True


# ──────────────────────────────────────────────
# PROVIDER SMTP / IMAP CONFIG
# ──────────────────────────────────────────────

PROVIDER_CONFIG = {
    "gmail": {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "display": "Gmail",
    },
    "outlook": {
        "smtp_host": "smtp-mail.outlook.com",
        "smtp_port": 587,
        "display": "Outlook",
    },
    "yahoo": {
        "smtp_host": "smtp.mail.yahoo.com",
        "smtp_port": 587,
        "display": "Yahoo Mail",
    },
}

FALLBACK_CHAIN = ["gmail", "outlook", "yahoo"]


# ──────────────────────────────────────────────
# HELPER: BUILD MIME MESSAGE
# ──────────────────────────────────────────────

def _build_mime_message(
    sender_email: str,
    recipient_email: str,
    subject: str,
    body: str,
) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Message-ID"] = f"<{uuid.uuid4()}@emailwriter>"
    msg.attach(MIMEText(body, "plain"))
    return msg


# ──────────────────────────────────────────────
# HELPER: SEND VIA SMTP (shared logic)
# ──────────────────────────────────────────────

def _smtp_send(
    provider_key: str,
    state: EmailWorkflowState,
    max_retries: int = 3,
) -> dict:
    """
    Core SMTP transmission. Retries up to max_retries times.
    Returns state-update dict on success, raises DeliveryError on failure.
    """
    config = PROVIDER_CONFIG[provider_key]
    creds = state.sender_credentials
    sender_email = creds.get("email", "")
    password = creds.get("password", "")

    content = state.generated_content
    subject = content.get("subject", "(No Subject)")
    body = content.get("body", "")

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                f"[{config['display']}] Attempt {attempt}/{max_retries} → {state.recipient_email}"
            )

            msg = _build_mime_message(
                sender_email, state.recipient_email, subject, body
            )
            raw_msg_id = msg["Message-ID"]

            with smtplib.SMTP(config["smtp_host"], config["smtp_port"], timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.login(sender_email, password)
                server.sendmail(sender_email, [state.recipient_email], msg.as_string())

            ts = datetime.now(timezone.utc).isoformat()
            final_result = (
                f"Message delivered to {state.recipient_email} "
                f"via {config['display']} at {ts}"
            )
            logger.info(f"✅ {final_result}")

            return {
                "delivery_status": "sent",
                "message_id": raw_msg_id,
                "current_provider": provider_key,
                "provider_attempts": state.provider_attempts + [provider_key],
                "final_result": final_result,
                "retry_count": 0,
                "error_detail": None,
            }

        except smtplib.SMTPAuthenticationError as e:
            last_error = f"Auth failed for {config['display']}: {e}"
            logger.warning(last_error)
            break  # Auth errors won't be fixed by retrying

        except Exception as e:
            last_error = f"{config['display']} attempt {attempt} failed: {e}"
            logger.warning(last_error)

    raise DeliveryError(last_error or f"{config['display']} delivery failed")


# ──────────────────────────────────────────────
# NODE: PARSE GENERATED EMAIL CONTENT
# ──────────────────────────────────────────────

def parse_email_content_node(state: EmailWorkflowState) -> dict:
    """
    Validates that generated_content has the required fields
    before any transmission attempt.
    """
    content = state.generated_content
    subject = content.get("subject", "").strip()
    body = content.get("body", "").strip()

    if not subject:
        content["subject"] = "No Subject"
    if not body:
        raise ValueError("Email body is empty — cannot send.")

    # Determine first provider to try
    if state.provider_choice == "auto":
        first_provider = FALLBACK_CHAIN[0]
    else:
        first_provider = state.provider_choice

    return {
        "generated_content": content,
        "current_provider": first_provider,
        "delivery_status": "pending",
    }


# ──────────────────────────────────────────────
# NODE: SELECT PROVIDER
# ──────────────────────────────────────────────

def select_provider_node(state: EmailWorkflowState) -> dict:
    """Routes to the correct provider based on state.current_provider."""
    return {}  # Routing is handled by conditional edges


# ──────────────────────────────────────────────
# SEND NODES
# ──────────────────────────────────────────────

def send_via_gmail_node(state: EmailWorkflowState) -> EmailWorkflowState:
    """
    Transmit generated email to state.recipient_email via Gmail SMTP.

    Args:
        state: Contains recipient_email (validated) and generated_content.
               sender_credentials must have {"email": "...", "password": "app-password"}

    Returns:
        Updated EmailWorkflowState object.

    Raises:
        DeliveryError: If SMTP returns error after 3 retries.
    """
    try:
        updated_state = _smtp_send("gmail", state)
        # Merge the returned dictionary with the existing state
        return state.copy(update=updated_state)
    except DeliveryError as e:
        return state.copy(
            update={
                "delivery_status": "pending",
                "provider_attempts": state.provider_attempts + ["gmail"],
                "error_detail": str(e),
                "current_provider": "outlook",
            }
        )

def send_via_outlook_node(state: EmailWorkflowState) -> EmailWorkflowState:
    """
    Transmit generated email to state.recipient_email via Outlook SMTP.

    Args:
        state: Contains recipient_email (validated) and generated_content.
               sender_credentials must have {"email": "...", "password": "..."}

    Returns:
        Updated EmailWorkflowState object.

    Raises:
        DeliveryError: If SMTP returns error after 3 retries.
    """
    try:
        updated_state = _smtp_send("outlook", state)
        # Merge the returned dictionary with the existing state
        return state.copy(update=updated_state)
    except DeliveryError as e:
        return state.copy(
            update={
                "delivery_status": "pending",
                "provider_attempts": state.provider_attempts + ["outlook"],
                "error_detail": str(e),
                "current_provider": "yahoo",
            }
        )

def send_via_yahoo_node(state: EmailWorkflowState) -> EmailWorkflowState:
    """
    Transmit generated email to state.recipient_email via Yahoo SMTP.

    Args:
        state: Contains recipient_email (validated) and generated_content.
               sender_credentials must have {"email": "...", "password": "app-password"}

    Returns:
        Updated EmailWorkflowState object.

    Raises:
        DeliveryError: If SMTP returns error after 3 retries.
    """
    try:
        updated_state = _smtp_send("yahoo", state)
        # Merge the returned dictionary with the existing state
        return state.copy(update=updated_state)
    except DeliveryError as e:
        return state.copy(
            update={
                "delivery_status": "pending",
                "provider_attempts": state.provider_attempts + ["yahoo"],
                "error_detail": str(e),
                "current_provider": None,
            }
        )


# ──────────────────────────────────────────────
# TERMINAL NODES
# ──────────────────────────────────────────────

def delivery_confirmed_node(state: EmailWorkflowState) -> dict:
    """
    Final state: Email successfully transmitted to recipient.

    Returns:
        Complete state with delivery_status="sent",
        final_result string for user display,
        message_id for tracking.
    """
    logger.info(f"🎉 DELIVERY CONFIRMED: {state.final_result}")
    return {
        "delivery_status": "sent",
        "final_result": state.final_result,
    }


def delivery_failed_node(state: EmailWorkflowState) -> dict:
    """
    Final state: All providers exhausted, email NOT delivered.

    Returns:
        State with delivery_status="failed",
        error details,
        UNDELIVERED EMAIL CONTENT for manual recovery.
    """
    tried = ", ".join(state.provider_attempts) if state.provider_attempts else "none"
    final_result = (
        f"❌ DELIVERY FAILED — Could not reach {state.recipient_email}. "
        f"Providers tried: {tried}. "
        f"Last error: {state.error_detail or 'unknown'}. "
        f"Undelivered subject: '{state.generated_content.get('subject', '')}'"
    )
    logger.error(final_result)
    return {
        "delivery_status": "failed",
        "final_result": final_result,
    }


# ──────────────────────────────────────────────
# CONDITIONAL ROUTING
# ──────────────────────────────────────────────

def route_to_provider(state: EmailWorkflowState) -> str:
    """Route from select_provider to the correct send node."""
    provider = state.current_provider or "gmail"
    mapping = {
        "gmail": "send_gmail",
        "outlook": "send_outlook",
        "yahoo": "send_yahoo",
    }
    return mapping.get(provider, "send_gmail")


def route_after_send(state: EmailWorkflowState) -> str:
    """
    After any send attempt:
    - "sent"    → confirmed
    - "pending" → next provider (tracked in current_provider)
    - "failed"  → failed terminal
    """
    if state.delivery_status == "sent":
        return "confirmed"

    if state.delivery_status == "failed":
        return "failed"

    # Still pending → route to whichever provider is next
    next_p = state.current_provider
    if next_p == "outlook":
        return "send_outlook"
    if next_p == "yahoo":
        return "send_yahoo"

    return "failed"


# ──────────────────────────────────────────────
# GRAPH CONSTRUCTION
# ──────────────────────────────────────────────

def _build_graph() -> Any:
    """Build and compile the LangGraph delivery workflow."""

    workflow = StateGraph(EmailWorkflowState)

    # Nodes
    workflow.add_node("parse_content",   parse_email_content_node)
    workflow.add_node("select_provider", select_provider_node)
    workflow.add_node("send_gmail",      send_via_gmail_node)
    workflow.add_node("send_outlook",    send_via_outlook_node)
    workflow.add_node("send_yahoo",      send_via_yahoo_node)
    workflow.add_node("confirmed",       delivery_confirmed_node)
    workflow.add_node("failed",          delivery_failed_node)

    # Entry point
    workflow.set_entry_point("parse_content")

    # Linear edges
    workflow.add_edge("parse_content",   "select_provider")
    workflow.add_edge("confirmed",       END)
    workflow.add_edge("failed",          END)

    # Conditional routing: select_provider → correct send node
    workflow.add_conditional_edges(
        "select_provider",
        route_to_provider,
        {
            "send_gmail":   "send_gmail",
            "send_outlook": "send_outlook",
            "send_yahoo":   "send_yahoo",
        },
    )

    # Conditional routing: after each send attempt
    for send_node in ("send_gmail", "send_outlook", "send_yahoo"):
        workflow.add_conditional_edges(
            send_node,
            route_after_send,
            {
                "confirmed":    "confirmed",
                "failed":       "failed",
                "send_outlook": "send_outlook",
                "send_yahoo":   "send_yahoo",
            },
        )

    return workflow.compile()


# Compile once at import time
_graph = _build_graph()


# ──────────────────────────────────────────────
# PUBLIC API
# ──────────────────────────────────────────────

def send_email(
    generated_content: dict,
    recipient_email: str,
    sender_email: str,
    sender_password: str,
    provider: Literal["gmail", "outlook", "yahoo", "auto"] = "auto",
) -> dict:
    """
    Deliver an email to the specified address using LangGraph workflow.

    This is the primary entry point. When this function returns successfully,
    the email exists in the recipient's inbox.

    Args:
        generated_content : Dict with keys "subject" and "body" from email_generator.py
        recipient_email   : WHERE THE EMAIL WILL BE SENT (validated)
        sender_email      : Your sending email address
        sender_password   : App password (Gmail/Yahoo) or account password (Outlook)
        provider          : "gmail" | "outlook" | "yahoo" | "auto" (tries all in order)

    Returns:
        {
            "success": True,
            "message": "Message delivered to alice@company.com via Gmail at ...",
            "message_id": "<uuid@emailwriter>",
            "provider_used": "gmail",
            "recipient": "alice@company.com"
        }

    Raises:
        DeliveryError: If email could not be delivered after all retries/fallbacks.

    Example:
        >>> result = send_email(
        ...     generated_content={"subject": "Q3 Update", "body": "Hi Alice, ..."},
        ...     recipient_email="alice@company.com",
        ...     sender_email="me@gmail.com",
        ...     sender_password="xxxx xxxx xxxx xxxx",
        ...     provider="gmail",
        ... )
        >>> print(result["message"])
        "Message delivered to alice@company.com via Gmail at 2024-01-15T09:30:00Z"
    """
    initial_state = EmailWorkflowState(
        recipient_email=recipient_email,
        generated_content=generated_content,
        provider_choice=provider,
        sender_credentials={"email": sender_email, "password": sender_password},
    )

    raw_result = _graph.invoke(initial_state)

    # LangGraph returns a dict, not the Pydantic model — access via keys
    if isinstance(raw_result, dict):
        status       = raw_result.get("delivery_status")
        final_result = raw_result.get("final_result")
        message_id   = raw_result.get("message_id")
        provider     = raw_result.get("current_provider")
        recipient    = raw_result.get("recipient_email", recipient_email)
    else:
        # Fallback: Pydantic object (future-proofing)
        status       = raw_result.delivery_status
        final_result = raw_result.final_result
        message_id   = raw_result.message_id
        provider     = raw_result.current_provider
        recipient    = raw_result.recipient_email

    if status == "sent":
        return {
            "success": True,
            "message": final_result,
            "message_id": message_id,
            "provider_used": provider,
            "recipient": recipient,
        }
    else:
        raise DeliveryError(
            final_result
            or f"Delivery failed to {recipient_email}. "
               f"Undelivered content: {generated_content}"
        )