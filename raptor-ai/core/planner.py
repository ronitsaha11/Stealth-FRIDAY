"""
planner.py — Intent to tool routing for Raptor.
Checked in priority order: real-time data, time, automation, email, OS tools.
"""

from __future__ import annotations

import re
import logging

logger = logging.getLogger("core-planner")

from core.tools.email import has_pending_email_read


def _normalize_file_request(file_token: str) -> tuple[str, str | None]:
    normalized = file_token.strip().lower()
    if normalized in {"resume", "cv"}:
        return "pdf", "resume"
    if normalized in {"photo", "image"}:
        return "jpg", normalized
    if normalized == "document":
        return "docx", None
    return normalized, None


def plan_task(user_input: str) -> list:
    plan = _plan_task_internal(user_input)
    logger.info(f"[DEBUG] Planner selected tools: {plan}")
    return plan

def _plan_task_internal(user_input: str) -> list:
    s = user_input.lower().strip()

    blocklist = ["rm", "sudo", "mkfs", "dd", "chmod", "chown", "shutdown", "reboot"]
    tokens = re.split(r"\s+", s)
    if any(blocked == token for blocked in blocklist for token in tokens):
        return []

    # Normalize: strip punctuation for reliable keyword matching
    s_clean = re.sub(r"[^\w\s]", "", s)

    # ── Weather (current or forecast) ──
    forecast_match = re.search(
        r"(?:weather\s+)?forecast\s+(?:in|for|at)?\s*([a-zA-Z\s]+?)(?:\s*$|\?)",
        s,
    )
    if not forecast_match:
        forecast_match = re.search(
            r"(?:this\s+week|next\s+\d+\s+days?|upcoming)\s+weather\s+(?:in|for|at)?\s*([a-zA-Z\s]+?)(?:\s*$|\?)",
            s,
        )
    if forecast_match:
        city = forecast_match.group(1).strip()
        if city:
            return [{"tool": "get_weather_forecast", "args": {"city": city}}]

    weather_match = re.search(r"weather\s+(?:in|for|at)?\s*([a-zA-Z\s]+?)(?:\s*$|\?)", s)
    if weather_match:
        city = weather_match.group(1).strip()
        if city:
            return [{"tool": "get_weather", "args": {"city": city}}]

    # ── Cricket Scores (PRIORITY — before generic sports/news) ──
    cricket_keywords = [
        "cricket score", "cricket scores", "live cricket",
        "ipl score", "ipl scores", "ipl update",
        "cricket match", "cricket update", "cricket result",
        "whos winning in cricket", "who is winning in cricket",
        "whats the cricket score", "what is the cricket score",
        "cricket live", "t20 score", "test match score",
    ]
    if any(keyword in s_clean for keyword in cricket_keywords):
        return [{"tool": "get_cricket_scores", "args": {}}]

    # ── Football Scores ──
    football_keywords = [
        "football score", "football scores", "soccer score", "soccer scores",
        "football update", "soccer update", "football result",
        "premier league", "la liga", "champions league",
        "whos winning in football", "who is winning in football",
        "live football", "live soccer",
    ]
    if any(keyword in s_clean for keyword in football_keywords):
        return [{"tool": "get_football_scores", "args": {}}]

    # ── Stock / Crypto Price ──
    stock_triggers = ["stock", "price", "share", "trading", "bitcoin", "crypto", "nifty", "sensex"]
    if any(kw in s for kw in stock_triggers):
        # Pattern 1: "price of X", "stock price of X", "what is X stock"
        stock_match = re.search(
            r"(?:price\s+of|stock\s+price\s+of|stock\s+price)\s+"
            r"([a-zA-Z0-9. ]+?)(?:\s*$|\?)",
            s,
        )
        # Pattern 2: "X stock price", "X share price", "X price"
        if not stock_match:
            stock_match = re.search(
                r"([a-zA-Z0-9. ]+?)\s+(?:stock|share|crypto)\s*(?:price|today|update)?(?:\s*$|\?)",
                s,
            )
        # Pattern 3: "how much is X", "what is X trading at"
        if not stock_match:
            stock_match = re.search(
                r"(?:how\s+much\s+is|whats|what\s+is|how\s+is)\s+"
                r"([a-zA-Z0-9. ]+?)\s*(?:stock|share|price|trading|today|doing|worth|at)\s*(?:$|\?)",
                s,
            )
        # Pattern 4: "price of bitcoin" / direct name match
        if not stock_match:
            stock_match = re.search(
                r"(?:price\s+of|check)\s+([a-zA-Z0-9. ]+?)(?:\s*$|\?)",
                s,
            )
        # Pattern 5: "X price" (e.g., "sensex price", "bitcoin price")
        if not stock_match:
            stock_match = re.search(
                r"([a-zA-Z0-9.]+)\s+price(?:\s*$|\?)",
                s,
            )
        if stock_match:
            symbol = stock_match.group(1).strip()
            if symbol and symbol not in {"the", "a", "my"}:
                return [{"tool": "get_stock_price", "args": {"symbol": symbol}}]

    # ── Music Playback ──
    music_match = re.search(r"play\s+(some\s+)?music(?:\s*$|\?)", s)
    if not music_match:
        music_match = re.search(r"play\s+(a\s+)?song(?:\s*$|\?)", s)
        
    if music_match:
        return [{"tool": "play_music", "args": {"query": ""}}]
        
    specific_song_match = re.search(r"play\s+(.+?)(?:\s+on\s+youtube)?(?:\s*$|\?)", s)
    if specific_song_match and "music" not in s and "song" not in s: # If they just said play the song, we catch it above
        song = specific_song_match.group(1).strip()
        if song:
            return [{"tool": "play_music", "args": {"query": song}}]

    # ── WORLD MONITOR (PRIORITY — must be checked BEFORE generic news) ──

    world_monitor_keywords = [
        "world monitor",
        "world news",
        "global situation",
        "global monitor",
        "whats going around the world",
        "what is going around the world",
        "whats going on around the world",
        "what is going on around the world",
        "whats happening around the world",
        "what is happening around the world",
        "show global situation",
        "show world monitor",
        "world situation",
    ]
    if any(keyword in s_clean for keyword in world_monitor_keywords):
        return [{"tool": "open_world_monitor", "args": {}}]

    # ── Generic news (lower priority) ──
    news_keywords = [
        "news",
        "headlines",
        "what's happening",
        "whats happening",
        "what is happening",
        "going on in the world",
        "latest updates",
    ]
    if any(keyword in s for keyword in news_keywords):
        return [{"tool": "get_news", "args": {}}]

    timer_match = (
        re.search(r"(?:set\s+)?timer\s+(?:for\s+)?(\d+)\s*(second|sec|minute|min|hour|hr)s?", s)
        or re.search(r"(?:remind\s+me|alert\s+me)\s+in\s+(\d+)\s*(second|sec|minute|min|hour|hr)s?", s)
    )
    if timer_match:
        amount = int(timer_match.group(1))
        unit = timer_match.group(2)
        if unit.startswith("min"):
            seconds = amount * 60
        elif unit.startswith("hour") or unit.startswith("hr"):
            seconds = amount * 3600
        else:
            seconds = amount
        return [{"tool": "set_timer", "args": {"seconds": seconds}}]

    alarm_match = (
        re.search(r"(?:set\s+)?alarm\s+(?:for\s+|at\s+)?(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)", s)
        or re.search(r"(?:wake\s+me(?:\s+up)?|remind\s+me)\s+at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)", s)
    )
    if alarm_match:
        return [{"tool": "set_alarm", "args": {"time_str": alarm_match.group(1).strip()}}]

    notification_keywords = [
        "read notifications",
        "check notifications",
        "any messages",
        "any mail notifications",
        "read my notifications",
    ]
    if any(keyword in s for keyword in notification_keywords):
        return [{"tool": "read_recent_notifications", "args": {"limit": 5}}]

    if s in {"yes", "yeah", "sure", "read them", "read those emails"} and has_pending_email_read():
        return [{"tool": "read_last_emails", "args": {"limit": 5}}]

    if "latest email" in s or "read latest email" in s:
        return [{"tool": "read_latest_email", "args": {}}]

    open_first_match = re.search(r"open\s+(?:the\s+)?(first|second|third|fourth|fifth|\d+)(?:st|nd|rd|th)?\s+email", s)
    if open_first_match:
        token = open_first_match.group(1).strip()
        index_map = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5}
        index = index_map[token] if token in index_map else int(token)
        return [{"tool": "open_email_in_browser", "args": {"index": index}}]

    open_sender_match = re.search(r"open\s+email\s+from\s+([a-zA-Z0-9 .&_-]+?)(?:\s*$|\?)", s)
    if open_sender_match:
        sender = open_sender_match.group(1).strip()
        return [{"tool": "open_email_in_browser", "args": {"sender": sender}}]

    if s in {"read that email", "read the email", "open that email"}:
        return [{"tool": "read_context_email", "args": {}}]

    if s in {"who sent that", "who sent that email", "who sent it"}:
        return [{"tool": "describe_context_email_sender", "args": {}}]

    if s in {"what is it about", "what is that email about", "what is that about"}:
        return [{"tool": "describe_context_email_topic", "args": {}}]

    if "summarize emails" in s or "what emails do i have" in s or "summarize my emails" in s:
        return [{"tool": "summarize_emails", "args": {"limit": 10}}]

    from_search_match = re.search(r"(?:find|search)\s+emails?\s+from\s+([a-zA-Z0-9 .&_-]+?)(?:\s*$|\?)", s)
    if from_search_match:
        sender = from_search_match.group(1).strip()
        return [{"tool": "search_emails", "args": {"query": f'from:{sender}', "limit": 5}}]

    read_sender_match = re.search(r"read\s+(?:my\s+)?emails?\s+from\s+([a-zA-Z0-9 .&_-]+?)(?:\s*$|\?)", s)
    if read_sender_match:
        sender = read_sender_match.group(1).strip()
        return [{"tool": "read_emails", "args": {"limit": 5, "sender": sender}}]

    if "unread emails" in s or "read unread emails" in s:
        return [{"tool": "read_emails", "args": {"limit": 5, "unread_only": True}}]

    if "important emails" in s or "read important emails" in s:
        return [{"tool": "read_emails", "args": {"limit": 5, "important_only": True}}]

    email_keywords = [
        "read email",
        "read emails",
        "emails",
        "check email",
        "check emails",
        "read my email",
        "read my emails",
        "check my email",
        "check my emails",
        "inbox",
        "any new email",
        "what emails",
        "read mail",
        "check mail",
    ]
    if any(keyword in s for keyword in email_keywords):
        return [{"tool": "read_emails", "args": {"limit": 5}}]

    if s in ("open whatsapp", "open whats app", "launch whatsapp"):
        return [{"tool": "open_whatsapp", "args": {}}]

    if s == "open gmail":
        return [{"tool": "open_url", "args": {"url": "https://mail.google.com"}}]

    if s == "open browser":
        return [{"tool": "open_url", "args": {"url": "about:blank"}}]

    url_match = re.search(r"open\s+((?:https?://)?(?:www\.)?[a-z0-9.-]+\.[a-z]{2,}(?:/[^\s]*)?)", s)
    if url_match:
        url = url_match.group(1).strip()
        if not url.startswith(("http://", "https://", "about:")):
            url = f"https://{url}"
        return [{"tool": "open_url", "args": {"url": url}}]

    message_match = re.search(r"send\s+(.+?)\s+to\s+([a-zA-Z\s]+?)(?:\s*$|\?)", s)
    alt_message_match = re.search(r"message\s+([a-zA-Z\s]+?)\s+saying\s+(.+)", s)
    if (message_match or alt_message_match) and any(keyword in s for keyword in ["send", "message", "whatsapp", "text"]):
        file_keywords = ["pdf", "doc", "docx", "resume", "file", "photo", "image", "jpg", "png", "cv"]
        if not any(keyword in s for keyword in file_keywords):
            if alt_message_match:
                contact = alt_message_match.group(1).strip()
                message = alt_message_match.group(2).strip()
            else:
                message = message_match.group(1).strip()
                contact = message_match.group(2).strip()
            if contact and message:
                return [{"tool": "send_whatsapp_message", "args": {"contact": contact, "message": message}}]

    file_send_match = re.search(
        r"send\s+(?:my\s+)?(?:latest\s+)?([\w.]+)\s+(?:file\s+)?to\s+([a-zA-Z\s]+?)(?:\s*$|\?)",
        s,
    )
    if file_send_match:
        raw_file_type = file_send_match.group(1).strip()
        contact = file_send_match.group(2).strip()
        file_type, name_hint = _normalize_file_request(raw_file_type)
        file_keywords = ["pdf", "doc", "docx", "resume", "file", "photo", "image", "jpg", "png", "cv"]
        if any(keyword in s for keyword in file_keywords):
            return [
                {"tool": "find_latest_file", "args": {"file_type": file_type, "name_hint": name_hint}},
                {"tool": "send_file_via_whatsapp", "args": {"contact": contact, "file_path": "$last_file_path"}},
            ]

    find_file_match = re.search(
        r"(?:find|locate|where\s+is)\s+(?:my\s+)?(?:latest|newest|recent)?\s*([\w.]+)\s+file",
        s,
    )
    if find_file_match:
        file_type, name_hint = _normalize_file_request(find_file_match.group(1).strip())
        return [{"tool": "find_latest_file", "args": {"file_type": file_type, "name_hint": name_hint}}]

    open_file_match = re.search(r"open\s+file\s+([\S]+)", s)
    if open_file_match:
        return [{"tool": "open_file", "args": {"path": open_file_match.group(1).strip()}}]

    # ── Browser Intelligence ──
    browser_page_keywords = [
        "what is this page", "what page is this", "what am i looking at",
        "whats on this page", "what is on this page", "describe this page",
        "what tab is this", "current page", "current tab",
        "read this page", "whats on screen",
    ]
    if any(kw in s_clean for kw in browser_page_keywords):
        return [{"tool": "browser_get_page", "args": {}}]

    browser_summarize_keywords = [
        "summarize this", "summarize this page", "summarize the page",
        "summarize page", "page summary", "summarize whats on screen",
        "tldr this page", "whats this page about",
    ]
    if any(kw in s_clean for kw in browser_summarize_keywords):
        return [{"tool": "browser_summarize", "args": {}}]

    # "click <button_text>" — browser click by visible text
    browser_click_match = re.search(
        r"(?:click|press|tap|hit)\s+(?:the\s+|on\s+)?(?:the\s+)?(.+?)\s*(?:button|link|tab)?\s*$",
        s,
    )
    if browser_click_match:
        target = browser_click_match.group(1).strip()
        # Avoid matching OS-level commands like "click open" → open_app
        os_overlap = ["open", "search", "create", "run", "send", "play", "set"]
        if target and target.lower() not in os_overlap and len(target) > 1:
            return [{"tool": "browser_click", "args": {"text": target}}]

    # "type <text> in <field>" / "fill <field> with <text>" — browser type
    browser_type_match = re.search(
        r"type\s+(.+?)\s+(?:in|into|in the|into the)\s+(.+?)(?:\s*$|\s+field|\s+box|\s+input)",
        s,
    )
    if not browser_type_match:
        browser_type_match = re.search(
            r"fill\s+(?:the\s+)?(.+?)\s+(?:with|as|to)\s+(.+?)(?:\s*$)",
            s,
        )
        if browser_type_match:
            # Swap groups: fill <field> with <text>
            field = browser_type_match.group(1).strip()
            text = browser_type_match.group(2).strip()
            if field and text:
                return [{"tool": "browser_type", "args": {"field": field, "text": text}}]
            browser_type_match = None  # Reset so we don't double-process

    if browser_type_match:
        text = browser_type_match.group(1).strip()
        field = browser_type_match.group(2).strip()
        if text and field:
            return [{"tool": "browser_type", "args": {"field": field, "text": text}}]

    # "search <query>" or "google <query>" — browser search
    browser_search_match = re.search(
        r"(?:search|google|look\s+up)\s+(?:for\s+)?(.+?)(?:\s+on\s+(?:the\s+)?(?:web|internet|google|browser|chrome))?(?:\s*$|\?)",
        s,
    )
    if browser_search_match:
        query = browser_search_match.group(1).strip()
        if query and not any(kw in s_clean for kw in ["search file", "search email", "search for file", "search for email"]):
            return [{"tool": "browser_search", "args": {"query": query}}]

    # "fill form" — generic, get page data first to see what fields exist
    if "fill form" in s or "fill the form" in s:
        return [{"tool": "browser_get_page", "args": {}}]

    # ── Automation Engine (system / network / browser) ──
    from core.intelligence import select_tools
    auto_plan = select_tools(s)
    if auto_plan:
        filtered_plan = []
        for step in auto_plan:
            if step.get("tool") == "automation_network_scan":
                if any(kw in s_clean for kw in ["scan network", "network scan", "check network"]):
                    filtered_plan.append(step)
            else:
                filtered_plan.append(step)
        if filtered_plan:
            return filtered_plan

    plan = []
    steps = re.split(r"\s+and\s+|\s+then\s+|,", s)
    steps = [step.strip() for step in steps if step.strip()]
    last_context = ""

    for step in steps:
        if "create folder" in step or "create a folder named" in step:
            name = re.split(r"folder", step)[-1].replace("named", "").strip()
            path = f"~/{name}"
            plan.append({"tool": "create_folder", "args": {"path": path}})
            last_context = path
        elif "open it in" in step:
            app = step.split("in")[-1].strip()
            plan.append({"tool": "open_app", "args": {"app_name": app}})
        elif "open it" in step and last_context:
            plan.append({"tool": "run_command", "args": {"command": f"open {last_context}"}})
        elif "open" in step and "folder" not in step and "file" not in step:
            app = step.split("open")[-1].strip()
            plan.append({"tool": "open_app", "args": {"app_name": app}})
        elif "search for" in step:
            query = step.split("search for")[-1].strip()
            plan.append({"tool": "search_files", "args": {"query": query}})
        elif "search" in step:
            query = step.split("search")[-1].strip()
            plan.append({"tool": "search_files", "args": {"query": query}})
        elif "run" in step or "execute" in step:
            command = step.split("run")[-1].strip() if "run" in step else step.split("execute")[-1].strip()
            plan.append({"tool": "run_command", "args": {"command": command}})

    return plan
