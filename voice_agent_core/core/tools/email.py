"""Gmail tools for Raptor."""

from __future__ import annotations

import os
import subprocess
from collections import Counter
from typing import Any


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CREDS_FILE = os.path.join(ROOT_DIR, "credentials.json")
TOKEN_FILE = os.path.join(ROOT_DIR, "token.json")

last_emails: list[dict[str, str]] = []
last_selected_email: dict[str, str] | None = None
pending_read_aloud: bool = False


def authenticate():
    """Return valid Gmail OAuth credentials, creating token.json if needed."""
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
    except ImportError as exc:
        raise RuntimeError("Missing Gmail authentication dependencies.") from exc

    if not os.path.exists(CREDS_FILE):
        raise RuntimeError("Missing credentials.json for Gmail authentication.")

    try:
        creds = None
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())

        if not creds or not creds.valid:
            raise RuntimeError("Gmail authentication did not return valid credentials.")
        return creds
    except Exception as exc:
        print(f"[EMAIL] Authentication failed: {type(exc).__name__}: {exc}")
        raise


def _build_service():
    try:
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError("Missing Gmail API client dependencies.") from exc

    creds = authenticate()
    return build("gmail", "v1", credentials=creds)


def _normalize_sender(sender: str) -> str:
    clean_sender = sender.strip()
    if "<" in clean_sender:
        clean_sender = clean_sender.split("<", 1)[0].strip()
    return clean_sender.strip('"') or "Unknown Sender"


def _truncate(text: str, limit: int = 160) -> str:
    compact = " ".join((text or "").split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def _gmail_message_url(message_id: str) -> str:
    return f"https://mail.google.com/mail/u/0/#all/{message_id}"


def _store_email_context(items: list[dict[str, str]], select_index: int | None = None, mark_pending_read: bool = False) -> None:
    global last_emails, last_selected_email, pending_read_aloud
    last_emails = [dict(item) for item in items]
    pending_read_aloud = mark_pending_read
    if select_index is not None and 0 <= select_index < len(last_emails):
        last_selected_email = dict(last_emails[select_index])
    elif not items:
        last_selected_email = None


def has_pending_email_read() -> bool:
    return pending_read_aloud and bool(last_emails)


def _clear_pending_read() -> None:
    global pending_read_aloud
    pending_read_aloud = False


def _build_query(unread_only: bool = False, important_only: bool = False, sender: str | None = None) -> str:
    query_parts = []
    if unread_only:
        query_parts.append("is:unread")
    if important_only:
        query_parts.append("is:important")
    if sender:
        query_parts.append(f'from:("{sender}")')
    return " ".join(query_parts)


def _fetch_messages(
    *,
    limit: int = 5,
    query: str | None = None,
    label_ids: list[str] | None = None,
    include_snippet: bool = False,
) -> tuple[list[dict[str, str]], int]:
    service = _build_service()
    response = service.users().messages().list(
        userId="me",
        labelIds=label_ids or ["INBOX"],
        q=query or None,
        maxResults=limit,
    ).execute()
    message_refs = response.get("messages", [])
    total_count = int(response.get("resultSizeEstimate", len(message_refs)) or 0)
    items: list[dict[str, str]] = []

    for message_ref in message_refs:
        message_data = service.users().messages().get(
            userId="me",
            id=message_ref["id"],
            format="metadata",
            metadataHeaders=["Subject", "From"],
        ).execute()
        headers = {header["name"]: header["value"] for header in message_data.get("payload", {}).get("headers", [])}
        item = {
            "id": message_ref["id"],
            "sender": _normalize_sender(headers.get("From", "Unknown Sender")),
            "subject": headers.get("Subject", "(No Subject)"),
            "url": _gmail_message_url(message_ref["id"]),
        }
        if include_snippet:
            item["snippet"] = _truncate(message_data.get("snippet", ""))
        items.append(item)

    return items, total_count


def _email_intro(unread_only: bool, important_only: bool, sender: str | None) -> str:
    if sender:
        return f"Here are your latest emails from {sender}:"
    if unread_only and important_only:
        return "Here are your latest unread important emails:"
    if unread_only:
        return "Here are your latest unread emails:"
    if important_only:
        return "Here are your latest important emails:"
    return "Here are your latest emails:"


def _voice_friendly_item(index: int, item: dict[str, str]) -> str:
    return f"{index}. Email from {item['sender']}. Subject: {item['subject']}."


def _format_summary(items: list[dict[str, str]], total_count: int) -> str:
    sender_counts = Counter(item["sender"] for item in items)
    top_groups = sender_counts.most_common(2)
    summary_parts = [f"{count} from {name}" for name, count in top_groups]
    remaining = total_count - sum(count for _, count in top_groups)
    if remaining > 0:
        summary_parts.append(f"{remaining} others")
    return f"You have {total_count} emails: " + ". ".join(summary_parts) + ". Do you want me to read them?"


def _get_email_from_context(index: int | None = None) -> dict[str, str] | None:
    if index is not None:
        zero_index = index - 1
        if 0 <= zero_index < len(last_emails):
            return dict(last_emails[zero_index])
        return None
    if last_selected_email:
        return dict(last_selected_email)
    if last_emails:
        return dict(last_emails[0])
    return None


def read_emails(
    limit: int = 5,
    unread_only: bool = False,
    important_only: bool = False,
    sender: str | None = None,
) -> dict[str, Any]:
    """Read recent inbox subjects with optional filters."""
    try:
        fetch_limit = max(limit, 10)
        items, total_count = _fetch_messages(
            limit=fetch_limit,
            query=_build_query(unread_only, important_only, sender),
            include_snippet=True,
        )
        if not items:
            _store_email_context([], select_index=None, mark_pending_read=False)
            return {"status": "success", "message": "I could not find matching emails.", "items": []}

        if total_count > 5:
            _store_email_context(items, select_index=0, mark_pending_read=True)
            summary_message = _format_summary(items[:10], total_count)
            print("[EMAIL] Gmail read summarized because more than five emails matched.")
            return {
                "status": "success",
                "message": summary_message,
                "items": [_voice_friendly_item(index, item) for index, item in enumerate(items[:10], start=1)],
            }

        display_items = items[:limit]
        _store_email_context(display_items, select_index=0, mark_pending_read=False)
        spoken_items = [_voice_friendly_item(index, item) for index, item in enumerate(display_items, start=1)]
        print("[EMAIL] Gmail read succeeded.")
        return {
            "status": "success",
            "message": _email_intro(unread_only, important_only, sender) + " " + " ".join(spoken_items),
            "items": spoken_items,
        }
    except Exception as exc:
        print(f"[EMAIL] Gmail read failed: {type(exc).__name__}: {exc}")
        return {
            "status": "failed",
            "message": "I couldn't access your emails right now.",
            "items": [],
        }


def read_last_emails(limit: int = 5) -> dict[str, Any]:
    """Read back the last remembered email results."""
    if not last_emails:
        return {"status": "failed", "message": "I don't have any recent email results to read yet.", "items": []}

    _clear_pending_read()
    display_items = last_emails[:limit]
    spoken_items = [_voice_friendly_item(index, item) for index, item in enumerate(display_items, start=1)]
    return {
        "status": "success",
        "message": "Here are the emails I just found: " + " ".join(spoken_items),
        "items": spoken_items,
    }


def summarize_emails(
    limit: int = 10,
    unread_only: bool = False,
    important_only: bool = False,
    sender: str | None = None,
) -> dict[str, Any]:
    """Summarize recent emails by sender."""
    try:
        items, total_count = _fetch_messages(
            limit=max(limit, 10),
            query=_build_query(unread_only, important_only, sender),
            include_snippet=True,
        )
        if not items:
            _store_email_context([], select_index=None, mark_pending_read=False)
            return {"status": "success", "message": "You do not have matching emails right now.", "items": []}

        _store_email_context(items, select_index=0, mark_pending_read=True)
        return {
            "status": "success",
            "message": _format_summary(items[:10], total_count),
            "items": [f"{item['sender']}: {item['subject']}" for item in items[:10]],
        }
    except Exception as exc:
        print(f"[EMAIL] Gmail summary failed: {type(exc).__name__}: {exc}")
        return {
            "status": "failed",
            "message": "I couldn't access your emails right now.",
            "items": [],
        }


def search_emails(query: str, limit: int = 5) -> dict[str, Any]:
    """Search Gmail using the native Gmail query syntax."""
    try:
        items, total_count = _fetch_messages(limit=max(limit, 10), query=query, include_snippet=True)
        if not items:
            _store_email_context([], select_index=None, mark_pending_read=False)
            return {"status": "success", "message": f'I could not find any emails for "{query}".', "items": []}

        _store_email_context(items, select_index=0, mark_pending_read=total_count > 5)
        if total_count > 5:
            return {
                "status": "success",
                "message": _format_summary(items[:10], total_count),
                "items": [_voice_friendly_item(index, item) for index, item in enumerate(items[:10], start=1)],
            }

        spoken_items = [_voice_friendly_item(index, item) for index, item in enumerate(items[:limit], start=1)]
        return {
            "status": "success",
            "message": f'Here are the top email matches for "{query}": ' + " ".join(spoken_items),
            "items": spoken_items,
        }
    except Exception as exc:
        print(f"[EMAIL] Gmail search failed: {type(exc).__name__}: {exc}")
        return {
            "status": "failed",
            "message": "I couldn't access your emails right now.",
            "items": [],
        }


def read_latest_email() -> dict[str, Any]:
    """Read the sender, subject, and snippet of the latest inbox email."""
    try:
        items, _ = _fetch_messages(limit=1, include_snippet=True)
        if not items:
            _store_email_context([], select_index=None, mark_pending_read=False)
            return {"status": "success", "message": "Your inbox is empty.", "items": []}

        latest = items[0]
        _store_email_context(items, select_index=0, mark_pending_read=False)
        message = (
            f'Email from {latest["sender"]}. '
            f'Subject: {latest["subject"]}. '
            f'It is about: {latest.get("snippet", "(No preview available)")}.'
        )
        return {
            "status": "success",
            "message": message,
            "items": [latest["sender"], latest["subject"], latest.get("snippet", "")],
        }
    except Exception as exc:
        print(f"[EMAIL] Latest email read failed: {type(exc).__name__}: {exc}")
        return {
            "status": "failed",
            "message": "I couldn't access your emails right now.",
            "items": [],
        }


def open_email_in_browser(index: int = 1, sender: str | None = None) -> dict[str, Any]:
    """Open a remembered email in Gmail."""
    try:
        target_email = None
        if sender:
            if last_emails:
                target_email = next((item for item in last_emails if sender.lower() in item["sender"].lower()), None)
            if target_email is None:
                items, _ = _fetch_messages(limit=5, query=f'from:("{sender}")', include_snippet=True)
                if items:
                    _store_email_context(items, select_index=0, mark_pending_read=False)
                    target_email = items[0]
        else:
            target_email = _get_email_from_context(index=index)

        if target_email is None:
            return {"status": "failed", "message": "I don't have that email in context yet.", "items": []}

        subprocess.run(["open", target_email["url"]], check=True)
        _store_email_context(last_emails or [target_email], select_index=0, mark_pending_read=False)
        global last_selected_email
        last_selected_email = dict(target_email)
        return {
            "status": "success",
            "message": f'Opened the email from {target_email["sender"]}. Subject: {target_email["subject"]}.',
            "items": [target_email["url"]],
        }
    except Exception as exc:
        print(f"[EMAIL] Open email failed: {type(exc).__name__}: {exc}")
        return {
            "status": "failed",
            "message": "I couldn't access your emails right now.",
            "items": [],
        }


def read_context_email(index: int | None = None) -> dict[str, Any]:
    """Read the selected or remembered email from context."""
    target_email = _get_email_from_context(index=index)
    if target_email is None:
        return {"status": "failed", "message": "I don't have that email in context yet.", "items": []}

    global last_selected_email
    last_selected_email = dict(target_email)
    _clear_pending_read()
    return {
        "status": "success",
        "message": (
            f'Email from {target_email["sender"]}. '
            f'Subject: {target_email["subject"]}. '
            f'It is about: {target_email.get("snippet", "(No preview available)")}.'
        ),
        "items": [target_email["sender"], target_email["subject"], target_email.get("snippet", "")],
    }


def describe_context_email_sender() -> dict[str, Any]:
    """Return the sender of the current email context."""
    target_email = _get_email_from_context()
    if target_email is None:
        return {"status": "failed", "message": "I don't have that email in context yet.", "items": []}
    return {
        "status": "success",
        "message": f'That email is from {target_email["sender"]}.',
        "items": [target_email["sender"]],
    }


def describe_context_email_topic() -> dict[str, Any]:
    """Return the subject and summary of the current email context."""
    target_email = _get_email_from_context()
    if target_email is None:
        return {"status": "failed", "message": "I don't have that email in context yet.", "items": []}
    return {
        "status": "success",
        "message": (
            f'That email is about {target_email["subject"]}. '
            f'Preview: {target_email.get("snippet", "(No preview available)")}.'
        ),
        "items": [target_email["subject"], target_email.get("snippet", "")],
    }


def register(mcp):
    @mcp.tool(name="read_emails")
    def read_emails_tool(
        limit: int = 5,
        unread_only: bool = False,
        important_only: bool = False,
        sender: str | None = None,
    ) -> dict[str, Any]:
        """Read recent email subjects with optional filters."""
        return read_emails(limit=limit, unread_only=unread_only, important_only=important_only, sender=sender)

    @mcp.tool(name="read_last_emails")
    def read_last_emails_tool(limit: int = 5) -> dict[str, Any]:
        """Read back the last remembered email results."""
        return read_last_emails(limit=limit)

    @mcp.tool(name="summarize_emails")
    def summarize_emails_tool(
        limit: int = 10,
        unread_only: bool = False,
        important_only: bool = False,
        sender: str | None = None,
    ) -> dict[str, Any]:
        """Summarize recent emails by sender."""
        return summarize_emails(limit=limit, unread_only=unread_only, important_only=important_only, sender=sender)

    @mcp.tool(name="search_emails")
    def search_emails_tool(query: str, limit: int = 5) -> dict[str, Any]:
        """Search Gmail with a Gmail query string."""
        return search_emails(query=query, limit=limit)

    @mcp.tool(name="read_latest_email")
    def read_latest_email_tool() -> dict[str, Any]:
        """Read the latest email subject, sender, and snippet."""
        return read_latest_email()

    @mcp.tool(name="open_email_in_browser")
    def open_email_in_browser_tool(index: int = 1, sender: str | None = None) -> dict[str, Any]:
        """Open a remembered email in Gmail."""
        return open_email_in_browser(index=index, sender=sender)

    @mcp.tool(name="read_context_email")
    def read_context_email_tool(index: int | None = None) -> dict[str, Any]:
        """Read an email from remembered context."""
        return read_context_email(index=index)

    @mcp.tool(name="describe_context_email_sender")
    def describe_context_email_sender_tool() -> dict[str, Any]:
        """Return the sender of the current email context."""
        return describe_context_email_sender()

    @mcp.tool(name="describe_context_email_topic")
    def describe_context_email_topic_tool() -> dict[str, Any]:
        """Return the topic of the current email context."""
        return describe_context_email_topic()
