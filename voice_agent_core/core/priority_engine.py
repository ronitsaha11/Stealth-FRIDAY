"""
priority_engine.py — Raptor Alert Prioritization & Filtering
=============================================================
Sits between event detection and alert delivery. Decides which
events reach the user by applying:

  1. Ignore list — hard-block certain event types
  2. Interest matching — only pass events related to user interests
  3. Severity gating — only pass events ≥ user's threshold
  4. Context boosting — promote events the user recently interacted with
  5. Alert grouping — batch multiple events within a time window

All decisions are driven by user_profile.json — no code changes
needed to adjust preferences.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

# ── Severity Levels (numeric for comparison) ─────────────────────────────

SEVERITY_RANK: dict[str, int] = {
    "low": 1,
    "info": 1,
    "medium": 2,
    "warning": 2,
    "high": 3,
    "critical": 4,
}

# ── Event-to-interest mapping ────────────────────────────────────────────
# Maps event type prefixes/names to the interest category they belong to.

EVENT_INTEREST_MAP: dict[str, str] = {
    "cpu_spike": "technology",
    "ram_spike": "technology",
    "disk_full": "technology",
    "low_battery": "technology",
    "new_device": "security",
    "network_change": "security",
    "weather_rain": "weather",
    "weather_rain_forecast": "weather",
    "weather_heat": "weather",
    "weather_cold": "weather",
    "weather_temp_spike": "weather",
    "cricket_major": "cricket",
    "football_major": "football",
    "news_breaking": "news",
}

# ── Profile Loading ──────────────────────────────────────────────────────

_PROFILE_PATH = os.path.join(
    os.path.dirname(__file__), "user_profile.json"
)

_cached_profile: dict | None = None
_profile_mtime: float = 0.0


def load_profile(force: bool = False) -> dict:
    """
    Load user_profile.json with file-modification caching.
    Re-reads only when the file changes on disk.
    Returns default profile if file is missing/corrupt.
    """
    global _cached_profile, _profile_mtime

    if not os.path.exists(_PROFILE_PATH):
        return _default_profile()

    try:
        current_mtime = os.path.getmtime(_PROFILE_PATH)
    except OSError:
        return _cached_profile or _default_profile()

    if not force and _cached_profile and current_mtime <= _profile_mtime:
        return _cached_profile

    try:
        with open(_PROFILE_PATH, "r") as f:
            _cached_profile = json.load(f)
            _profile_mtime = current_mtime
            return _cached_profile
    except (json.JSONDecodeError, OSError) as e:
        print(f"[PRIORITY] Profile load error: {e}")
        return _cached_profile or _default_profile()


def _default_profile() -> dict:
    """Fallback profile if user_profile.json is missing."""
    return {
        "location": "Bhubaneswar",
        "interests": ["cricket", "football", "technology", "weather", "security", "news"],
        "ignore_list": [],
        "severity_threshold": "low",
        "priority_levels": {},
        "context_boost_enabled": True,
        "grouping_window_seconds": 15,
    }


# ── Context Tracker ──────────────────────────────────────────────────────

class ContextTracker:
    """
    Tracks topics the user recently interacted with.
    When the user confirms or asks about a topic, that topic gets
    a temporary priority boost (decays over time).
    """

    def __init__(self, decay_seconds: float = 300.0):
        """
        Args:
            decay_seconds: How long a boost lasts (default 5 minutes).
        """
        self._interactions: dict[str, float] = {}
        self._decay = decay_seconds

    def record_interaction(self, topic: str) -> None:
        """Record that the user interacted with a topic."""
        self._interactions[topic] = time.time()

    def get_boost(self, event_type: str) -> int:
        """
        Return a priority boost (0 or 1) if the user recently
        interacted with the topic mapped to this event type.
        """
        interest = EVENT_INTEREST_MAP.get(event_type, "")
        if not interest:
            return 0

        last = self._interactions.get(interest, 0.0)
        if (time.time() - last) < self._decay:
            return 1
        return 0

    def get_active_topics(self) -> list[str]:
        """Return list of currently boosted topics."""
        now = time.time()
        return [
            topic for topic, ts in self._interactions.items()
            if (now - ts) < self._decay
        ]


# Singleton
context_tracker = ContextTracker()


# ── Priority Filter ──────────────────────────────────────────────────────

def should_alert(event: dict, profile: dict | None = None) -> bool:
    """
    Determine whether an event should reach the user.

    Checks in order:
      1. Is the event type on the ignore list? → block
      2. Does the event match a user interest? → pass (or block)
      3. Is the effective severity ≥ threshold? → pass (or block)

    Returns True if the event should be delivered.
    """
    if profile is None:
        profile = load_profile()

    event_type = event.get("type", "")

    # ── 1. Hard ignore ──
    ignore_list = profile.get("ignore_list", [])
    if event_type in ignore_list:
        return False

    # ── 2. Interest check ──
    interests = profile.get("interests", [])
    mapped_interest = EVENT_INTEREST_MAP.get(event_type, "")

    # System/security events always pass (they're safety-related)
    is_system = mapped_interest in ("technology", "security")

    if not is_system and mapped_interest and mapped_interest not in interests:
        return False

    # ── 3. Severity gating ──
    threshold_str = profile.get("severity_threshold", "low")
    threshold_rank = SEVERITY_RANK.get(threshold_str, 1)

    # Event's base severity
    event_severity_str = event.get("severity", "info")
    event_rank = SEVERITY_RANK.get(event_severity_str, 1)

    # Priority level from profile (overrides event severity)
    priority_levels = profile.get("priority_levels", {})
    if event_type in priority_levels:
        override_str = priority_levels[event_type]
        event_rank = SEVERITY_RANK.get(override_str, event_rank)

    # Context boost
    if profile.get("context_boost_enabled", True):
        boost = context_tracker.get_boost(event_type)
        event_rank += boost

    if event_rank < threshold_rank:
        return False

    return True


def effective_severity(event: dict, profile: dict | None = None) -> str:
    """
    Compute the effective severity label for an event, taking into
    account profile overrides and context boost.
    """
    if profile is None:
        profile = load_profile()

    event_type = event.get("type", "")
    base = event.get("severity", "info")
    rank = SEVERITY_RANK.get(base, 1)

    # Profile override
    priority_levels = profile.get("priority_levels", {})
    if event_type in priority_levels:
        rank = SEVERITY_RANK.get(priority_levels[event_type], rank)

    # Context boost
    if profile.get("context_boost_enabled", True):
        rank += context_tracker.get_boost(event_type)

    # Clamp
    rank = min(rank, 4)

    # Reverse map
    for label, r in sorted(SEVERITY_RANK.items(), key=lambda x: x[1], reverse=True):
        if r <= rank:
            return label
    return "info"


# ── Alert Grouping ───────────────────────────────────────────────────────

class AlertGrouper:
    """
    Batches events that arrive within a time window into a single
    grouped alert, reducing TTS interruptions.
    """

    def __init__(self, window: float = 15.0):
        """
        Args:
            window: Grouping window in seconds.
        """
        self._window = window
        self._buffer: list[dict] = []
        self._first_event_time: float = 0.0

    def add(self, event: dict) -> None:
        """Add an event to the current group buffer."""
        now = time.time()
        if not self._buffer:
            self._first_event_time = now
        self._buffer.append(event)

    def is_window_expired(self) -> bool:
        """Check if the grouping window has elapsed since the first event."""
        if not self._buffer:
            return False
        return (time.time() - self._first_event_time) >= self._window

    def flush(self) -> list[dict]:
        """Return and clear all buffered events."""
        events = list(self._buffer)
        self._buffer.clear()
        self._first_event_time = 0.0
        return events

    def has_events(self) -> bool:
        """Check if there are buffered events."""
        return len(self._buffer) > 0

    @property
    def count(self) -> int:
        return len(self._buffer)


def group_events_to_alert(events: list[dict]) -> dict:
    """
    Merge multiple events into a single grouped alert dict.
    Picks the highest severity from the group.
    """
    if not events:
        return {}

    if len(events) == 1:
        return events[0]

    # Combine messages
    messages = [e["message"] for e in events]
    combined_msg = "Multiple alerts: " + " Also, ".join(messages)

    # Pick highest severity
    best_severity = "info"
    best_rank = 0
    for e in events:
        r = SEVERITY_RANK.get(e.get("severity", "info"), 1)
        if r > best_rank:
            best_rank = r
            best_severity = e.get("severity", "info")

    # Pick first suggestion that exists
    suggestion = ""
    for e in events:
        if e.get("suggestion"):
            suggestion = e["suggestion"]
            break

    return {
        "type": "grouped_alert",
        "message": combined_msg,
        "suggestion": suggestion,
        "severity": best_severity,
        "_grouped_events": events,
        "_group_count": len(events),
    }
