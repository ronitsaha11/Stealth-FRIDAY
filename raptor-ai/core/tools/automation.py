"""macOS automation helpers for Raptor."""

from __future__ import annotations

import glob
import os
import subprocess
from typing import Any


SEARCH_DIRS = [
    os.path.expanduser("~/Desktop"),
    os.path.expanduser("~/Downloads"),
    os.path.expanduser("~/Documents"),
]

HEURISTIC_EXTENSIONS = {
    "resume": ["pdf", "doc", "docx"],
    "cv": ["pdf", "doc", "docx"],
    "document": ["pdf", "doc", "docx"],
    "photo": ["jpg", "jpeg", "png", "heic"],
    "image": ["jpg", "jpeg", "png", "heic"],
}

HEURISTIC_NAME_HINTS = {
    "resume": ["resume", "cv"],
    "cv": ["cv", "resume"],
}


def _run_osascript(script: str, env: dict[str, str] | None = None, timeout: int = 20) -> subprocess.CompletedProcess:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=merged_env,
    )


def _copy_to_clipboard(text: str) -> None:
    subprocess.run(["pbcopy"], input=text, text=True, check=True)


def _normalize_extensions(file_type: str, name_hint: str | None = None) -> list[str]:
    requested = file_type.strip().lower().lstrip(".")
    if requested in HEURISTIC_EXTENSIONS:
        return HEURISTIC_EXTENSIONS[requested]
    if name_hint and name_hint.strip().lower() in HEURISTIC_EXTENSIONS:
        return HEURISTIC_EXTENSIONS[name_hint.strip().lower()]
    return [requested]


def _collect_files(extensions: list[str]) -> list[str]:
    matches: list[str] = []
    for search_dir in SEARCH_DIRS:
        for extension in extensions:
            pattern = os.path.join(search_dir, f"**/*.{extension}")
            matches.extend(glob.glob(pattern, recursive=True))
    return [path for path in matches if os.path.isfile(path)]


def _rank_files(paths: list[str], hints: list[str]) -> list[str]:
    def score(path: str) -> tuple[int, float]:
        filename = os.path.basename(path).lower()
        hint_match = 1 if hints and any(hint in filename for hint in hints) else 0
        return (hint_match, os.path.getmtime(path))

    return sorted(paths, key=score, reverse=True)


def _activate_whatsapp_chat(contact: str) -> tuple[bool, str]:
    script = """
set targetContact to system attribute "RAPTOR_CONTACT"
tell application "WhatsApp" to activate
delay 1.2
tell application "System Events"
    tell process "WhatsApp"
        keystroke "f" using {command down}
        delay 0.5
        keystroke "a" using {command down}
        key code 51
        keystroke targetContact
        delay 1.0
        key code 36
        delay 0.8
    end tell
end tell
"""
    result = _run_osascript(script, env={"RAPTOR_CONTACT": contact}, timeout=15)
    if result.returncode != 0:
        return False, result.stderr.strip() or "WhatsApp automation failed."
    return True, ""


def open_whatsapp() -> str:
    """Open the WhatsApp desktop app."""
    try:
        subprocess.run(["open", "-a", "WhatsApp"], check=True, capture_output=True, text=True)
        return "WhatsApp is now open."
    except subprocess.CalledProcessError:
        open_url("https://web.whatsapp.com")
        return "WhatsApp desktop was not found. I opened WhatsApp Web instead."


def open_url(url: str, browser_app: str | None = None) -> str:
    """Open a URL in the default browser or a chosen browser app."""
    command = ["open"]
    if browser_app:
        command.extend(["-a", browser_app])
    command.append(url)
    subprocess.run(command, check=True)
    return f"Opened {url}."


def send_whatsapp_message(contact: str, message: str) -> dict[str, Any]:
    """Send a WhatsApp message using clipboard-safe UI automation."""
    print(f'[AUTOMATION] WhatsApp send requested for contact="{contact}".')
    try:
        open_whatsapp()
        ok, error = _activate_whatsapp_chat(contact)
        if not ok:
            print(f"[AUTOMATION] WhatsApp send failed: {error}")
            return {"status": "failed", "message": f"Could not open the WhatsApp chat for {contact}. {error}"}

        _copy_to_clipboard(message)
        script = """
tell application "System Events"
    tell process "WhatsApp"
        keystroke "v" using {command down}
        delay 0.3
        key code 36
    end tell
end tell
"""
        result = _run_osascript(script, timeout=10)
        if result.returncode != 0:
            error = result.stderr.strip() or "Message send automation failed."
            print(f"[AUTOMATION] WhatsApp send failed: {error}")
            return {"status": "failed", "message": f"Could not send the message to {contact}. {error}"}

        print(f'[AUTOMATION] WhatsApp send succeeded for contact="{contact}".')
        return {"status": "success", "message": f'Message sent to {contact} on WhatsApp.'}
    except Exception as exc:
        print(f"[AUTOMATION] WhatsApp send failed: {exc}")
        return {"status": "failed", "message": f"Could not send the message to {contact}. {exc}"}


def open_file(path: str) -> str:
    """Open a file with the default macOS app."""
    resolved_path = os.path.abspath(os.path.expanduser(path))
    if not os.path.exists(resolved_path):
        return f"File not found: {path}"
    subprocess.run(["open", resolved_path], check=True)
    return f"Opened {resolved_path}."


def find_latest_file(file_type: str, name_hint: str | None = None) -> dict[str, Any]:
    """Find the best matching recent file from common user folders."""
    normalized_hint = (name_hint or "").strip().lower()
    extensions = _normalize_extensions(file_type, normalized_hint)
    hint_terms = HEURISTIC_NAME_HINTS.get(normalized_hint, [normalized_hint] if normalized_hint else [])

    candidates = _collect_files(extensions)
    ranked_candidates = _rank_files(candidates, hint_terms)

    if not ranked_candidates:
        extension_summary = ", ".join(f".{ext}" for ext in extensions)
        message = f"No recent files matched {extension_summary} in Desktop, Downloads, or Documents."
        print(f"[AUTOMATION] File resolution failed: {message}")
        return {"status": "failed", "message": message, "items": []}

    best_match = ranked_candidates[0]
    items = ranked_candidates[:5]
    message = f"Found {os.path.basename(best_match)} in {os.path.dirname(best_match)}."
    print(f"[AUTOMATION] File resolution result: {best_match}")
    return {
        "status": "success",
        "message": message,
        "file_path": best_match,
        "items": items,
    }


def send_file_via_whatsapp(contact: str, file_path: str) -> dict[str, Any]:
    """Prepare a WhatsApp file send with a truthful fallback."""
    resolved_path = os.path.abspath(os.path.expanduser(file_path))
    if not os.path.exists(resolved_path):
        return {"status": "failed", "message": f"File not found: {file_path}"}

    print(f'[AUTOMATION] WhatsApp file send requested for contact="{contact}", file="{resolved_path}".')
    try:
        open_whatsapp()
        ok, error = _activate_whatsapp_chat(contact)
        if not ok:
            print(f"[AUTOMATION] WhatsApp file send failed: {error}")
            return {"status": "failed", "message": f"Could not open the WhatsApp chat for {contact}. {error}"}

        _copy_to_clipboard(resolved_path)
        script = """
tell application "System Events"
    tell process "WhatsApp"
        keystroke "u" using {command down}
        delay 1.0
        keystroke "g" using {command down, shift down}
        delay 0.5
        keystroke "v" using {command down}
        delay 0.3
        key code 36
        delay 0.8
        key code 36
        delay 1.0
        key code 36
    end tell
end tell
"""
        result = _run_osascript(script, timeout=20)
        if result.returncode == 0:
            print(f"[AUTOMATION] WhatsApp file attach flow completed for {resolved_path}.")
            return {
                "status": "success",
                "message": f"Prepared {os.path.basename(resolved_path)} for WhatsApp send to {contact}. Please confirm the attachment in WhatsApp.",
                "file_path": resolved_path,
            }

        open_file(resolved_path)
        error = result.stderr.strip() or "Direct WhatsApp attachment was not available."
        print(f"[AUTOMATION] WhatsApp file send fell back to manual handoff: {error}")
        return {
            "status": "success",
            "message": (
                f"I opened the WhatsApp chat and the file {os.path.basename(resolved_path)}. "
                "Direct attachment was not reliable on this macOS setup, so please confirm the final send manually."
            ),
            "file_path": resolved_path,
        }
    except Exception as exc:
        print(f"[AUTOMATION] WhatsApp file send failed: {exc}")
        return {"status": "failed", "message": f"Could not prepare the WhatsApp file send. {exc}"}


def read_recent_mail(limit: int = 5) -> dict[str, Any]:
    """Read recent unread Mail.app messages."""
    script = """
set maxItems to (system attribute "RAPTOR_LIMIT") as integer
tell application "Mail"
    set unreadMessages to (every message of inbox whose read status is false)
    set messageCount to count of unreadMessages
    if messageCount is 0 then
        return ""
    end if
    set outputLines to {}
    repeat with indexValue from 1 to (min of {maxItems, messageCount})
        set currentMessage to item indexValue of unreadMessages
        set senderName to sender of currentMessage as string
        set subjectLine to subject of currentMessage as string
        copy (senderName & "||" & subjectLine) to end of outputLines
    end repeat
    set AppleScript's text item delimiters to linefeed
    set joinedOutput to outputLines as string
    set AppleScript's text item delimiters to ""
    return joinedOutput
end tell
"""
    try:
        result = _run_osascript(script, env={"RAPTOR_LIMIT": str(limit)}, timeout=15)
        if result.returncode != 0:
            error = result.stderr.strip() or "Mail automation is unavailable."
            return {"status": "failed", "message": f"Could not read Mail.app messages. {error}", "items": []}

        rows = [row.strip() for row in result.stdout.splitlines() if row.strip()]
        items = []
        for row in rows[:limit]:
            sender, _, subject = row.partition("||")
            if sender or subject:
                items.append(f"From {sender or 'Unknown Sender'}: {subject or '(No Subject)'}")

        message = "No unread messages were found in Mail." if not items else "Mail notifications: " + ". ".join(items)
        print(f"[AUTOMATION] Notification source read: Mail ({len(items)} items).")
        return {"status": "success", "message": message, "items": items}
    except subprocess.TimeoutExpired:
        return {
            "status": "failed",
            "message": "Could not read Mail.app messages because Mail did not respond in time.",
            "items": [],
        }
    except Exception as exc:
        return {"status": "failed", "message": f"Could not read Mail.app messages. {exc}", "items": []}


def read_recent_messages(limit: int = 5) -> dict[str, Any]:
    """Read recent Messages.app chats."""
    script = """
set maxItems to (system attribute "RAPTOR_LIMIT") as integer
tell application "Messages"
    set targetChats to chats
    set chatCount to count of targetChats
    if chatCount is 0 then
        return ""
    end if
    set outputLines to {}
    repeat with indexValue from 1 to (min of {maxItems, chatCount})
        set currentChat to item indexValue of targetChats
        set chatName to ""
        try
            set chatName to name of currentChat as string
        end try
        if chatName is "" then
            try
                set chatName to id of currentChat as string
            end try
        end if
        copy chatName to end of outputLines
    end repeat
    set AppleScript's text item delimiters to linefeed
    set joinedOutput to outputLines as string
    set AppleScript's text item delimiters to ""
    return joinedOutput
end tell
"""
    try:
        result = _run_osascript(script, env={"RAPTOR_LIMIT": str(limit)}, timeout=15)
        if result.returncode != 0:
            error = result.stderr.strip() or "Messages automation is unavailable."
            return {"status": "failed", "message": f"Could not read Messages.app chats. {error}", "items": []}

        items = [item.strip() for item in result.stdout.splitlines() if item.strip()]
        message = "No recent chats were found in Messages." if not items else "Messages notifications: " + ". ".join(items[:limit])
        print(f"[AUTOMATION] Notification source read: Messages ({len(items[:limit])} items).")
        return {"status": "success", "message": message, "items": items[:limit]}
    except subprocess.TimeoutExpired:
        return {
            "status": "failed",
            "message": "Could not read Messages.app chats because Messages did not respond in time.",
            "items": [],
        }
    except Exception as exc:
        return {"status": "failed", "message": f"Could not read Messages.app chats. {exc}", "items": []}


def read_recent_notifications(limit: int = 5) -> dict[str, Any]:
    """Aggregate simple notification summaries from Mail and Messages."""
    mail_result = read_recent_mail(limit=limit)
    messages_result = read_recent_messages(limit=limit)

    sections = []
    items: list[str] = []

    if mail_result.get("status") == "success":
        sections.append(mail_result["message"])
        items.extend(mail_result.get("items", []))
    else:
        sections.append(mail_result["message"])

    if messages_result.get("status") == "success":
        sections.append(messages_result["message"])
        items.extend(messages_result.get("items", []))
    else:
        sections.append(messages_result["message"])

    print("[AUTOMATION] Notification sources read: Mail, Messages.")
    return {
        "status": "success",
        "message": " ".join(section for section in sections if section).strip(),
        "items": items[:limit],
    }


def register(mcp):
    @mcp.tool(name="open_whatsapp")
    def open_whatsapp_tool() -> str:
        """Open WhatsApp on macOS."""
        return open_whatsapp()

    @mcp.tool(name="send_whatsapp_message")
    def send_whatsapp_message_tool(contact: str, message: str) -> dict[str, Any]:
        """Send a WhatsApp message to a contact."""
        return send_whatsapp_message(contact, message)

    @mcp.tool(name="open_file")
    def open_file_tool(path: str) -> str:
        """Open a file path with the default app."""
        return open_file(path)

    @mcp.tool(name="find_latest_file")
    def find_latest_file_tool(file_type: str, name_hint: str | None = None) -> dict[str, Any]:
        """Find the latest matching file in common folders."""
        return find_latest_file(file_type=file_type, name_hint=name_hint)

    @mcp.tool(name="send_file_via_whatsapp")
    def send_file_via_whatsapp_tool(contact: str, file_path: str) -> dict[str, Any]:
        """Prepare a file send to a WhatsApp contact."""
        return send_file_via_whatsapp(contact, file_path)

    @mcp.tool(name="open_url")
    def open_url_tool(url: str, browser_app: str | None = None) -> str:
        """Open a URL in the browser."""
        return open_url(url, browser_app=browser_app)

    @mcp.tool(name="read_recent_mail")
    def read_recent_mail_tool(limit: int = 5) -> dict[str, Any]:
        """Read recent Mail.app summaries."""
        return read_recent_mail(limit=limit)

    @mcp.tool(name="read_recent_messages")
    def read_recent_messages_tool(limit: int = 5) -> dict[str, Any]:
        """Read recent Messages.app summaries."""
        return read_recent_messages(limit=limit)

    @mcp.tool(name="read_recent_notifications")
    def read_recent_notifications_tool(limit: int = 5) -> dict[str, Any]:
        """Read recent notifications from Mail and Messages."""
        return read_recent_notifications(limit=limit)
