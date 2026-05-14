"""
learning_controls.py — Raptor Learning Explainability & User Control
=====================================================================
Provides user-facing functions to:

  1. explain_event()   — why an event was shown/suppressed
  2. describe_profile() — what Raptor knows about the user
  3. override_topic()  — force always/never notify for a topic
  4. reset_learning()  — clear interaction log + reset adjustments

All functions return TTS-ready strings for the agent to speak.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

# ── Paths ────────────────────────────────────────────────────────────────

_DIR = os.path.dirname(__file__)
_LOG_PATH = os.path.join(_DIR, "interaction_log.json")
_PROFILE_PATH = os.path.join(_DIR, "user_profile.json")

# ── Imports from sibling modules ─────────────────────────────────────────

from core.learning_engine import (
    get_stats, get_confidence, should_suppress_learned,
    PROTECTED_TYPES, PRIORITY_LADDER,
)
from core.priority_engine import (
    should_alert, load_profile, EVENT_INTEREST_MAP,
    SEVERITY_RANK,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  1. EXPLAIN DECISIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def explain_event(event_type: str) -> dict:
    """
    Explain why an event type would be shown or suppressed.

    Returns a dict with:
      - confidence: float ∈ [0.0, 1.0]
      - acceptance_rate: float
      - ignore_rate: float
      - total_interactions: int
      - suppressed: bool
      - suppression_reason: str
      - priority: str
      - interest_category: str
      - is_protected: bool
      - explanation: str (TTS-ready)
    """
    profile = load_profile(force=True)
    stats = get_stats(event_type=event_type)
    event_stats = stats.get(event_type, {})

    confidence = get_confidence(event_type)
    suppressed = should_suppress_learned(event_type)

    # Determine suppression reason
    suppression_reason = "none"
    if event_type in profile.get("ignore_list", []):
        suppression_reason = "on ignore list"
        suppressed = True
    elif suppressed:
        suppression_reason = f"low confidence ({confidence})"

    # Check interest match
    interest = EVENT_INTEREST_MAP.get(event_type, "unknown")
    interests = profile.get("interests", [])
    if interest not in interests and interest not in ("technology", "security"):
        suppression_reason = f"'{interest}' not in your interests"
        suppressed = True

    # Priority
    priority = profile.get("priority_levels", {}).get(event_type, "medium")

    # Build explanation
    explanation_parts = []
    total = event_stats.get("total", 0)

    if total > 0:
        accept_rate = event_stats.get("acceptance_rate", 0)
        ignore_rate = event_stats.get("ignore_rate", 0)
        explanation_parts.append(
            f"For {event_type}: you've seen it {total} times, "
            f"accepted {accept_rate:.0%} and ignored {ignore_rate:.0%} of the time."
        )
    else:
        explanation_parts.append(f"I haven't shown you any {event_type} alerts yet.")

    explanation_parts.append(f"Confidence score is {confidence}.")
    explanation_parts.append(f"Current priority is {priority}.")

    if event_type in PROTECTED_TYPES:
        explanation_parts.append("This is a protected system event, so it can never be fully suppressed.")

    if suppressed:
        explanation_parts.append(f"Currently suppressed because: {suppression_reason}.")
    else:
        explanation_parts.append("This event type is currently active and will trigger alerts.")

    return {
        "confidence": confidence,
        "acceptance_rate": event_stats.get("acceptance_rate", 0),
        "ignore_rate": event_stats.get("ignore_rate", 0),
        "total_interactions": total,
        "suppressed": suppressed,
        "suppression_reason": suppression_reason,
        "priority": priority,
        "interest_category": interest,
        "is_protected": event_type in PROTECTED_TYPES,
        "explanation": " ".join(explanation_parts),
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  2. PROFILE QUERY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def describe_profile() -> dict:
    """
    Return a structured summary of what Raptor knows about the user.

    Returns:
      - location: str
      - interests: list[str]
      - ignore_list: list[str]
      - severity_threshold: str
      - learned_priorities: dict
      - top_engaged_topics: list (by acceptance rate)
      - top_ignored_topics: list (by ignore rate)
      - summary: str (TTS-ready)
    """
    profile = load_profile(force=True)
    stats = get_stats()

    # Top engaged
    engaged = sorted(
        [(et, s["acceptance_rate"]) for et, s in stats.items() if s["total"] >= 3],
        key=lambda x: x[1], reverse=True,
    )[:3]

    # Top ignored
    ignored = sorted(
        [(et, s["ignore_rate"]) for et, s in stats.items() if s["total"] >= 3],
        key=lambda x: x[1], reverse=True,
    )[:3]

    # Build summary
    parts = []
    parts.append(f"Your location is set to {profile.get('location', 'unknown')}.")
    parts.append(f"Your interests are: {', '.join(profile.get('interests', []))}.")

    ignore_list = profile.get("ignore_list", [])
    if ignore_list:
        parts.append(f"You've asked me to ignore: {', '.join(ignore_list)}.")

    parts.append(f"Alert threshold is set to {profile.get('severity_threshold', 'medium')}.")

    if engaged:
        top = engaged[0]
        parts.append(f"You engage most with {top[0]} alerts, at {top[1]:.0%} acceptance.")

    if ignored:
        top = ignored[0]
        parts.append(f"You tend to ignore {top[0]} alerts, at {top[1]:.0%} ignore rate.")

    return {
        "location": profile.get("location", "unknown"),
        "interests": profile.get("interests", []),
        "ignore_list": ignore_list,
        "severity_threshold": profile.get("severity_threshold", "medium"),
        "learned_priorities": profile.get("priority_levels", {}),
        "top_engaged_topics": [{"type": et, "rate": r} for et, r in engaged],
        "top_ignored_topics": [{"type": et, "rate": r} for et, r in ignored],
        "summary": " ".join(parts),
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  3. MANUAL OVERRIDE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Topic aliases for natural language → event_type / interest
_TOPIC_ALIASES: dict[str, list[str]] = {
    "cricket": ["cricket_major"],
    "football": ["football_major"],
    "weather": ["weather_rain", "weather_rain_forecast", "weather_heat", "weather_cold", "weather_temp_spike"],
    "news": ["news_breaking"],
    "network": ["new_device", "network_change"],
    "cpu": ["cpu_spike"],
    "ram": ["ram_spike"],
    "battery": ["low_battery"],
    "disk": ["disk_full"],
}


def _resolve_topic(topic: str) -> list[str]:
    """Resolve a natural language topic to event type(s)."""
    topic_lower = topic.lower().strip()

    # Direct match
    if topic_lower in EVENT_INTEREST_MAP:
        return [topic_lower]

    # Alias match
    if topic_lower in _TOPIC_ALIASES:
        return _TOPIC_ALIASES[topic_lower]

    # Fuzzy: check if topic is a substring of any event type
    matches = [et for et in EVENT_INTEREST_MAP if topic_lower in et]
    if matches:
        return matches

    return []


def override_always_notify(topic: str) -> dict:
    """
    Force-enable notifications for a topic.
    - Removes from ignore list
    - Sets priority to 'high'
    - Adds interest if missing

    Returns dict with 'success', 'changes', 'message' (TTS-ready).
    """
    event_types = _resolve_topic(topic)
    if not event_types:
        return {
            "success": False,
            "changes": [],
            "message": f"I don't recognize the topic '{topic}'.",
        }

    try:
        with open(_PROFILE_PATH, "r") as f:
            profile = json.load(f)
    except (json.JSONDecodeError, OSError, FileNotFoundError):
        return {"success": False, "changes": [], "message": "Could not load your profile."}

    changes = []

    # Remove from ignore list
    ignore_list = profile.get("ignore_list", [])
    for et in event_types:
        if et in ignore_list:
            ignore_list.remove(et)
            changes.append(f"removed {et} from ignore list")
    profile["ignore_list"] = ignore_list

    # Set priority to high
    priority_levels = profile.get("priority_levels", {})
    for et in event_types:
        old = priority_levels.get(et, "medium")
        if old != "high" and old != "critical":
            priority_levels[et] = "high"
            changes.append(f"set {et} priority to high")
    profile["priority_levels"] = priority_levels

    # Add interest if missing
    interest = EVENT_INTEREST_MAP.get(event_types[0], "")
    interests = profile.get("interests", [])
    if interest and interest not in interests:
        interests.append(interest)
        profile["interests"] = interests
        changes.append(f"added '{interest}' to your interests")

    try:
        with open(_PROFILE_PATH, "w") as f:
            json.dump(profile, f, indent=4)
    except OSError:
        return {"success": False, "changes": [], "message": "Could not save your profile."}

    if changes:
        msg = f"Done. I'll always notify you about {topic}. Changes: {', '.join(changes)}."
    else:
        msg = f"You're already set to receive {topic} notifications."

    print(f"[LEARNING-CTRL] Always notify: {topic} → {changes}")
    return {"success": True, "changes": changes, "message": msg}


def override_never_notify(topic: str) -> dict:
    """
    Force-disable notifications for a topic.
    - Adds to ignore list
    - Protected types cannot be fully ignored (warns instead)

    Returns dict with 'success', 'changes', 'message' (TTS-ready).
    """
    event_types = _resolve_topic(topic)
    if not event_types:
        return {
            "success": False,
            "changes": [],
            "message": f"I don't recognize the topic '{topic}'.",
        }

    # Check for protected types
    protected_hits = [et for et in event_types if et in PROTECTED_TYPES]
    if protected_hits:
        return {
            "success": False,
            "changes": [],
            "message": f"I can't fully suppress {', '.join(protected_hits)} because they're safety-critical system events. "
                       f"I can lower their priority, but they'll still alert you in emergencies.",
        }

    try:
        with open(_PROFILE_PATH, "r") as f:
            profile = json.load(f)
    except (json.JSONDecodeError, OSError, FileNotFoundError):
        return {"success": False, "changes": [], "message": "Could not load your profile."}

    changes = []

    # Add to ignore list
    ignore_list = profile.get("ignore_list", [])
    for et in event_types:
        if et not in ignore_list:
            ignore_list.append(et)
            changes.append(f"added {et} to ignore list")
    profile["ignore_list"] = ignore_list

    try:
        with open(_PROFILE_PATH, "w") as f:
            json.dump(profile, f, indent=4)
    except OSError:
        return {"success": False, "changes": [], "message": "Could not save your profile."}

    if changes:
        msg = f"Done. I won't notify you about {topic} anymore."
    else:
        msg = f"{topic} notifications are already disabled."

    print(f"[LEARNING-CTRL] Never notify: {topic} → {changes}")
    return {"success": True, "changes": changes, "message": msg}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  4. RESET LEARNING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Original (default) priority levels to restore on reset
_DEFAULT_PRIORITIES = {
    "cpu_spike": "high",
    "ram_spike": "high",
    "disk_full": "medium",
    "low_battery": "critical",
    "new_device": "high",
    "network_change": "low",
    "weather_rain": "medium",
    "weather_rain_forecast": "low",
    "weather_heat": "medium",
    "weather_cold": "low",
    "weather_temp_spike": "medium",
    "cricket_major": "high",
    "football_major": "medium",
    "news_breaking": "high",
}


def reset_learning() -> dict:
    """
    Reset Raptor's learned behavior:
      1. Clear interaction_log.json
      2. Reset priority_levels in user_profile.json to defaults

    Preserves: location, interests, ignore_list, other settings.

    Returns dict with 'success', 'message' (TTS-ready).
    """
    # 1. Clear interaction log
    try:
        with open(_LOG_PATH, "w") as f:
            json.dump([], f)
        print("[LEARNING-CTRL] Interaction log cleared")
    except OSError as e:
        return {"success": False, "message": f"Could not clear interaction log: {e}"}

    # 2. Reset priorities
    try:
        with open(_PROFILE_PATH, "r") as f:
            profile = json.load(f)

        profile["priority_levels"] = dict(_DEFAULT_PRIORITIES)

        with open(_PROFILE_PATH, "w") as f:
            json.dump(profile, f, indent=4)
        print("[LEARNING-CTRL] Priority levels reset to defaults")
    except (json.JSONDecodeError, OSError, FileNotFoundError) as e:
        return {"success": False, "message": f"Could not reset profile: {e}"}

    return {
        "success": True,
        "message": "Learning has been reset. I've cleared my interaction history "
                   "and restored all alert priorities to their defaults.",
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  5. INTENT DETECTION — Parse user commands for learning controls
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def detect_learning_intent(user_input: str) -> dict | None:
    """
    Parse a natural language command and detect if it's a learning-control
    intent. Returns a dict with 'action' and 'args', or None.

    Supported patterns:
      - "what do you know about me" / "my profile" / "my preferences"
      - "always notify me about cricket"
      - "never notify me about weather" / "stop telling me about news"
      - "reset learning" / "forget what you learned"
      - "why did you alert me about X" / "explain cricket alerts"
    """
    text = user_input.lower().strip()

    # ── Profile query ──
    profile_patterns = [
        "what do you know about me",
        "my profile", "my preferences",
        "what are my interests",
        "show my settings", "tell me about my profile",
        "what have you learned about me",
    ]
    if any(p in text for p in profile_patterns):
        return {"action": "describe_profile", "args": {}}

    # ── Always notify ──
    always_match = re.search(
        r"always (?:notify|alert|tell|inform) (?:me )?(?:about |for )?([\w\s]+)",
        text,
    )
    if always_match:
        topic = always_match.group(1).strip()
        return {"action": "always_notify", "args": {"topic": topic}}

    # ── Never notify ──
    never_patterns = [
        r"never (?:notify|alert|tell|inform) (?:me )?(?:about |for )?([\w\s]+)",
        r"stop (?:telling|alerting|notifying) (?:me )?(?:about |for )?([\w\s]+)",
        r"don'?t (?:notify|alert|tell) (?:me )?(?:about |for )?([\w\s]+)",
        r"mute ([\w\s]+?) (?:alerts?|notifications?)",
        r"ignore ([\w\s]+?) (?:alerts?|notifications?)",
    ]
    for pattern in never_patterns:
        match = re.search(pattern, text)
        if match:
            topic = match.group(1).strip()
            return {"action": "never_notify", "args": {"topic": topic}}

    # ── Reset learning ──
    reset_patterns = [
        "reset learning", "reset your learning",
        "forget what you learned", "forget what you've learned",
        "clear learning data", "reset alert learning",
        "start fresh", "reset my preferences",
    ]
    if any(p in text for p in reset_patterns):
        return {"action": "reset_learning", "args": {}}

    # ── Explain ──
    explain_patterns = [
        r"(?:why|explain|tell me about) .*?([\w_]+) (?:alert|notification|event)",
        r"explain ([\w_]+) alerts?",
        r"why do you (?:show|alert|notify).*?([\w_]+)",
    ]
    for pattern in explain_patterns:
        match = re.search(pattern, text)
        if match:
            topic = match.group(1).strip()
            resolved = _resolve_topic(topic)
            event_type = resolved[0] if resolved else topic
            return {"action": "explain_event", "args": {"event_type": event_type}}

    return None


def execute_learning_command(intent: dict) -> str:
    """
    Execute a learning control command and return a TTS-ready response.

    Args:
        intent: dict from detect_learning_intent()
    """
    action = intent.get("action", "")
    args = intent.get("args", {})

    if action == "describe_profile":
        result = describe_profile()
        return result["summary"]

    elif action == "always_notify":
        result = override_always_notify(args.get("topic", ""))
        return result["message"]

    elif action == "never_notify":
        result = override_never_notify(args.get("topic", ""))
        return result["message"]

    elif action == "reset_learning":
        result = reset_learning()
        return result["message"]

    elif action == "explain_event":
        result = explain_event(args.get("event_type", ""))
        return result["explanation"]

    return "I'm not sure what you want me to do with your learning settings."
