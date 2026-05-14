"""
learning_engine.py — Raptor Adaptive Learning System
=====================================================
Tracks user interactions with alerts over time and automatically
adjusts alert priorities to match observed behavior.

Pipeline:
  1. Log every interaction (accepted / ignored / cancelled / timeout)
  2. Compute acceptance & ignore rates per event type
  3. Build confidence scores ∈ [0.0, 1.0]
  4. Auto-adjust user_profile.json priority_levels
  5. Apply time-of-day modifiers

Safety:
  - System events (CPU, RAM, battery, disk) are NEVER auto-suppressed
  - Security events (new_device) are NEVER auto-suppressed
  - Changes are gradual (one level at a time)
  - Minimum sample size before adjustments kick in
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from typing import Any

# ── Constants ────────────────────────────────────────────────────────────

_DIR = os.path.dirname(__file__)
_LOG_PATH = os.path.join(_DIR, "interaction_log.json")
_PROFILE_PATH = os.path.join(_DIR, "user_profile.json")

# Minimum interactions before learning kicks in
MIN_SAMPLES = 5

# Thresholds for auto-adjustment
PROMOTE_THRESHOLD = 0.75   # acceptance rate ≥ 75% → increase priority
SUPPRESS_THRESHOLD = 0.70  # ignore rate ≥ 70% → decrease priority

# Priority ladder (ordered low → high)
PRIORITY_LADDER = ["low", "medium", "high", "critical"]

# Protected event types — NEVER auto-suppressed
PROTECTED_TYPES = frozenset({
    "cpu_spike", "ram_spike", "disk_full", "low_battery",
    "new_device",
})

# Time-of-day periods
TIME_PERIODS = {
    "night":   (0, 6),    # 00:00 - 05:59
    "morning": (6, 12),   # 06:00 - 11:59
    "afternoon": (12, 18), # 12:00 - 17:59
    "evening": (18, 24),  # 18:00 - 23:59
}


# ── Interaction Log ──────────────────────────────────────────────────────

def _load_log() -> list[dict]:
    """Load the interaction log from disk."""
    if not os.path.exists(_LOG_PATH):
        return []
    try:
        with open(_LOG_PATH, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_log(entries: list[dict]) -> None:
    """Save the interaction log to disk. Keeps last 500 entries."""
    entries = entries[-500:]  # cap to avoid unbounded growth
    try:
        with open(_LOG_PATH, "w") as f:
            json.dump(entries, f, indent=2)
    except OSError as e:
        print(f"[LEARNING] Log save error: {e}")


def record_interaction(event_type: str, response: str) -> None:
    """
    Record a user interaction with an alert.

    Args:
        event_type: The event type (e.g., 'cricket_major')
        response: One of 'accepted', 'cancelled', 'ignored', 'timeout'
    """
    entries = _load_log()
    now = datetime.now()

    entries.append({
        "event_type": event_type,
        "response": response,
        "timestamp": now.isoformat(),
        "hour": now.hour,
        "period": _get_period(now.hour),
    })

    _save_log(entries)
    print(f"[LEARNING] 📝 Logged: {event_type} → {response}")


def _get_period(hour: int) -> str:
    """Map an hour (0-23) to a time period name."""
    for period, (start, end) in TIME_PERIODS.items():
        if start <= hour < end:
            return period
    return "night"


# ── Statistics ───────────────────────────────────────────────────────────

def get_stats(event_type: str | None = None,
              entries: list[dict] | None = None) -> dict[str, dict]:
    """
    Compute acceptance/ignore rates per event type.

    Returns:
        {
            "cricket_major": {
                "total": 12,
                "accepted": 9,
                "ignored": 2,
                "cancelled": 1,
                "timeout": 0,
                "acceptance_rate": 0.75,
                "ignore_rate": 0.167,
            },
            ...
        }
    """
    if entries is None:
        entries = _load_log()

    stats: dict[str, dict] = {}

    for entry in entries:
        et = entry.get("event_type", "")
        if event_type and et != event_type:
            continue

        if et not in stats:
            stats[et] = {
                "total": 0,
                "accepted": 0,
                "ignored": 0,
                "cancelled": 0,
                "timeout": 0,
            }

        stats[et]["total"] += 1
        resp = entry.get("response", "ignored")
        if resp in stats[et]:
            stats[et][resp] += 1

    # Compute rates
    for et, s in stats.items():
        total = s["total"]
        if total > 0:
            s["acceptance_rate"] = round(s["accepted"] / total, 3)
            s["ignore_rate"] = round(
                (s["ignored"] + s["timeout"]) / total, 3
            )
        else:
            s["acceptance_rate"] = 0.0
            s["ignore_rate"] = 0.0

    return stats


def get_time_stats(entries: list[dict] | None = None) -> dict[str, dict]:
    """
    Compute per-period acceptance rates.

    Returns:
        {
            "morning": {"total": 5, "accepted": 4, "acceptance_rate": 0.8},
            "evening": {"total": 3, "accepted": 1, "acceptance_rate": 0.333},
            ...
        }
    """
    if entries is None:
        entries = _load_log()

    period_stats: dict[str, dict] = {}

    for entry in entries:
        period = entry.get("period", "unknown")
        if period not in period_stats:
            period_stats[period] = {"total": 0, "accepted": 0}
        period_stats[period]["total"] += 1
        if entry.get("response") == "accepted":
            period_stats[period]["accepted"] += 1

    for p, s in period_stats.items():
        s["acceptance_rate"] = round(
            s["accepted"] / s["total"], 3
        ) if s["total"] > 0 else 0.0

    return period_stats


# ── Confidence Score ─────────────────────────────────────────────────────

def get_confidence(event_type: str,
                   entries: list[dict] | None = None) -> float:
    """
    Compute a confidence score ∈ [0.0, 1.0] for an event type.

    Confidence = weighted acceptance rate, where recent interactions
    matter more than older ones.

    Returns 0.5 (neutral) if insufficient data.
    """
    if entries is None:
        entries = _load_log()

    relevant = [e for e in entries if e.get("event_type") == event_type]

    if len(relevant) < MIN_SAMPLES:
        return 0.5  # neutral — not enough data

    # Weight recent interactions more heavily (exponential decay)
    total_weight = 0.0
    weighted_accept = 0.0

    for i, entry in enumerate(relevant):
        # More recent entries have higher weight
        weight = 1.0 + (i / len(relevant))  # [1.0 → 2.0]
        total_weight += weight
        if entry.get("response") == "accepted":
            weighted_accept += weight

    if total_weight == 0:
        return 0.5

    return round(weighted_accept / total_weight, 3)


# ── Auto-Adjust Profile ─────────────────────────────────────────────────

def auto_adjust_profile() -> list[str]:
    """
    Analyze interaction history and adjust user_profile.json priorities.

    Rules:
      - acceptance_rate ≥ 75% + enough samples → promote (one level up)
      - ignore_rate ≥ 70% + enough samples → demote (one level down)
      - Protected types are NEVER demoted below 'medium'
      - Only one level change per adjustment cycle

    Returns:
        List of human-readable change descriptions.
    """
    entries = _load_log()
    stats = get_stats(entries=entries)

    # Load current profile
    try:
        with open(_PROFILE_PATH, "r") as f:
            profile = json.load(f)
    except (json.JSONDecodeError, OSError, FileNotFoundError):
        print("[LEARNING] Cannot load profile for auto-adjust")
        return []

    priority_levels = profile.get("priority_levels", {})
    changes: list[str] = []

    for event_type, s in stats.items():
        if s["total"] < MIN_SAMPLES:
            print(f"[LEARNING-DBG] {event_type}: skip — only {s['total']} samples (need {MIN_SAMPLES})")
            continue  # Not enough data

        current_priority = priority_levels.get(event_type, "medium")
        current_idx = PRIORITY_LADDER.index(current_priority) \
            if current_priority in PRIORITY_LADDER else 1

        new_idx = current_idx

        print(f"[LEARNING-DBG] {event_type}: accept={s['acceptance_rate']:.0%} "
              f"ignore={s['ignore_rate']:.0%} current={current_priority}")

        # ── High acceptance → promote ──
        if s["acceptance_rate"] >= PROMOTE_THRESHOLD:
            new_idx = min(current_idx + 1, len(PRIORITY_LADDER) - 1)
            print(f"[LEARNING-DBG] {event_type}: → PROMOTE (accept≥{PROMOTE_THRESHOLD})")

        # ── High ignore → demote ──
        elif s["ignore_rate"] >= SUPPRESS_THRESHOLD:
            new_idx = max(current_idx - 1, 0)
            print(f"[LEARNING-DBG] {event_type}: → DEMOTE (ignore≥{SUPPRESS_THRESHOLD})")

            # Safety: protected types never go below medium
            if event_type in PROTECTED_TYPES:
                new_idx = max(new_idx, 1)  # 1 = "medium"
                print(f"[LEARNING-DBG] {event_type}: PROTECTED floor applied (≥medium)")

        if new_idx != current_idx:
            new_priority = PRIORITY_LADDER[new_idx]
            priority_levels[event_type] = new_priority

            direction = "⬆️ promoted" if new_idx > current_idx else "⬇️ demoted"
            desc = f"{event_type}: {current_priority} → {new_priority} ({direction})"
            changes.append(desc)
            print(f"[LEARNING] {desc}")
        else:
            print(f"[LEARNING-DBG] {event_type}: no change needed")

    if changes:
        profile["priority_levels"] = priority_levels
        try:
            with open(_PROFILE_PATH, "w") as f:
                json.dump(profile, f, indent=4)
            print(f"[LEARNING] Profile updated with {len(changes)} change(s)")
        except OSError as e:
            print(f"[LEARNING] Profile save error: {e}")

    return changes


# ── Time-Based Severity Modifier ─────────────────────────────────────────

def get_time_modifier() -> int:
    """
    Return a severity modifier based on time of day.

    - Night (00-06): -1 (less intrusive — user likely sleeping)
    - Morning (06-12): 0 (neutral)
    - Afternoon (12-18): 0 (neutral)
    - Evening (18-24): 0 (neutral)

    Can be expanded with learned per-period engagement data.
    """
    hour = datetime.now().hour
    period = _get_period(hour)

    # Check learned data for low-engagement periods
    entries = _load_log()
    if len(entries) >= MIN_SAMPLES * 2:
        time_stats = get_time_stats(entries)
        period_data = time_stats.get(period, {})

        if period_data.get("total", 0) >= MIN_SAMPLES:
            rate = period_data.get("acceptance_rate", 0.5)
            if rate < 0.25:
                return -1  # very low engagement → suppress

    # Default rules
    if 0 <= hour < 6:
        return -1  # nighttime suppression
    return 0


# ── Integration Helper ───────────────────────────────────────────────────

def should_suppress_learned(event_type: str) -> bool:
    """
    Quick check: should this event type be suppressed based on
    learned behavior? Uses confidence score.

    Protected types are never suppressed.
    """
    if event_type in PROTECTED_TYPES:
        print(f"[LEARNING-DBG] {event_type}: PROTECTED — suppression bypassed")
        return False

    confidence = get_confidence(event_type)

    # Very low confidence (< 0.2) = user consistently ignores
    if confidence < 0.2:
        print(f"[LEARNING-DBG] {event_type}: SUPPRESSED — confidence={confidence} < 0.2")
        return True

    print(f"[LEARNING-DBG] {event_type}: PASS — confidence={confidence} ≥ 0.2")
    return False
