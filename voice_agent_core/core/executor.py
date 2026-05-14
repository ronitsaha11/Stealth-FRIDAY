from __future__ import annotations

import os
import sys

# ── Add project-root automation_engine to import path ──
_voice_agent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_project_root = os.path.dirname(_voice_agent_dir)
_automation_engine_dir = os.path.join(_project_root, "core", "tools", "automation_engine")
if _automation_engine_dir not in sys.path:
    sys.path.insert(0, _automation_engine_dir)

from core.tools.automation import (
    find_latest_file,
    open_file,
    open_url,
    open_whatsapp,
    read_recent_mail,
    read_recent_messages,
    read_recent_notifications,
    send_file_via_whatsapp,
    send_whatsapp_message,
)
from core.tools.email import (
    describe_context_email_sender,
    describe_context_email_topic,
    open_email_in_browser,
    read_context_email,
    read_emails,
    read_last_emails,
    read_latest_email,
    search_emails,
    summarize_emails,
)
from core.tools.os import _create_folder, _open_app, _run_command, _search_files
from core.tools.realtime import (
    get_cricket_scores,
    get_football_scores,
    get_news,
    get_stock_price,
    get_weather,
    get_weather_forecast,
    open_world_monitor,
    play_music,
)
from core.tools.time_tools import set_alarm, set_timer
from core.tools.browser import (
    browser_click,
    browser_get_page,
    browser_summarize,
    browser_type,
    browser_search,
)

# ── Automation Engine Imports ──
from system_tool import get_system_info as _auto_system_info
from network_tool import scan_network as _auto_network_scan
from browser_tool import (
    get_public_ip as _auto_get_ip,
    rotate_browser_session as _auto_rotate_session,
    inject_fingerprint as _auto_inject_fingerprint,
)


TOOL_REGISTRY = {
    "open_app": _open_app,
    "search_files": _search_files,
    "create_folder": _create_folder,
    "run_command": _run_command,
    "get_weather": get_weather,
    "get_weather_forecast": get_weather_forecast,
    "get_news": get_news,
    "get_cricket_scores": get_cricket_scores,
    "get_football_scores": get_football_scores,
    "get_stock_price": get_stock_price,
    "play_music": play_music,
    "open_world_monitor": open_world_monitor,
    "set_timer": set_timer,
    "set_alarm": set_alarm,
    "open_whatsapp": open_whatsapp,
    "send_whatsapp_message": send_whatsapp_message,
    "open_file": open_file,
    "find_latest_file": find_latest_file,
    "send_file_via_whatsapp": send_file_via_whatsapp,
    "open_url": open_url,
    "read_recent_mail": read_recent_mail,
    "read_recent_messages": read_recent_messages,
    "read_recent_notifications": read_recent_notifications,
    "read_emails": read_emails,
    "read_last_emails": read_last_emails,
    "summarize_emails": summarize_emails,
    "search_emails": search_emails,
    "read_latest_email": read_latest_email,
    "open_email_in_browser": open_email_in_browser,
    "read_context_email": read_context_email,
    "describe_context_email_sender": describe_context_email_sender,
    "describe_context_email_topic": describe_context_email_topic,
    # ── Automation Engine Tools ──
    "automation_system_info": _auto_system_info,
    "automation_system_analyze": _auto_system_info,   # same data, intelligence layer adds analysis
    "automation_network_scan": _auto_network_scan,
    "automation_get_ip": _auto_get_ip,
    "automation_rotate_session": _auto_rotate_session,
    "automation_inject_fingerprint": _auto_inject_fingerprint,
    # ── Browser Intelligence Tools ──
    "browser_get_page": browser_get_page,
    "browser_click": browser_click,
    "browser_type": browser_type,
    "browser_summarize": browser_summarize,
    "browser_search": browser_search,
}


def _resolve_args(args: dict, context: dict) -> dict:
    resolved_args = {}
    for key, value in args.items():
        if isinstance(value, str) and value.startswith("$"):
            resolved_args[key] = context.get(value[1:], "")
        else:
            resolved_args[key] = value
    return resolved_args


def _normalize_result(tool_name: str, raw_result):
    if isinstance(raw_result, dict):
        status = raw_result.get("status", "success")
        message = raw_result.get("message", "")
        return {
            "tool": tool_name,
            "status": status,
            "result": raw_result,
            "message": message,
        }

    text_result = str(raw_result)
    lowered = text_result.lower()
    status = "failed" if any(token in lowered for token in ["failed", "blocked", "error"]) else "success"
    return {
        "tool": tool_name,
        "status": status,
        "result": raw_result,
        "message": text_result,
    }


def execute_plan(plan: list) -> list:
    """Execute an ordered tool plan with simple shared context."""
    results = []
    context = {}

    for step in plan:
        tool_name = step.get("tool")
        print(f"[DEBUG] Executing tool: {tool_name}")
        args = _resolve_args(step.get("args", {}), context)

        if tool_name not in TOOL_REGISTRY:
            results.append(
                {
                    "tool": tool_name,
                    "status": "failed",
                    "error": f"Unknown tool: {tool_name}",
                    "message": f"Unknown tool: {tool_name}",
                }
            )
            break

        try:
            raw_result = TOOL_REGISTRY[tool_name](**args)
            normalized = _normalize_result(tool_name, raw_result)

            if isinstance(raw_result, dict):
                file_path = raw_result.get("file_path")
                if file_path:
                    context["last_file_path"] = file_path
                items = raw_result.get("items")
                if items is not None:
                    context["last_items"] = items

            results.append(normalized)
            if normalized["status"] != "success":
                break
        except Exception as exc:
            results.append(
                {
                    "tool": tool_name,
                    "status": "failed",
                    "error": str(exc),
                    "message": str(exc),
                }
            )
            break

    return results
