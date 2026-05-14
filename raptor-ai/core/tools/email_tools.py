"""Backward-compatible imports for Gmail tools."""

from core.tools.email import (
    CREDS_FILE,
    SCOPES,
    TOKEN_FILE,
    authenticate,
    describe_context_email_sender,
    describe_context_email_topic,
    has_pending_email_read,
    last_emails,
    open_email_in_browser,
    read_emails,
    read_context_email,
    read_last_emails,
    read_latest_email,
    register,
    search_emails,
    summarize_emails,
)

__all__ = [
    "SCOPES",
    "CREDS_FILE",
    "TOKEN_FILE",
    "authenticate",
    "last_emails",
    "has_pending_email_read",
    "read_emails",
    "read_last_emails",
    "summarize_emails",
    "search_emails",
    "read_latest_email",
    "open_email_in_browser",
    "read_context_email",
    "describe_context_email_sender",
    "describe_context_email_topic",
    "register",
]
