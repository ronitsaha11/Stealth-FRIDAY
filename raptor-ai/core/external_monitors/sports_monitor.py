"""
sports_monitor.py — Live Sports Event Detector
================================================
Periodically fetches live cricket/football scores from ESPN RSS
and detects significant events: wickets, goals, match completions,
and major score changes.

Uses the same free ESPN RSS feeds as the existing
get_cricket_scores() / get_football_scores() tools — no API key.
"""

from __future__ import annotations

import re
import ssl
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

# SSL context
_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE

# ── RSS Feeds ────────────────────────────────────────────────────────────

CRICKET_RSS = "https://www.espncricinfo.com/rss/livescores.xml"
FOOTBALL_RSS = "https://www.espn.com/espn/rss/soccer/news"

# ── Keywords for significant events ─────────────────────────────────────

CRICKET_MAJOR_KEYWORDS = [
    "wicket", "out", "all out", "won by", "lost by",
    "century", "50 runs", "hat-trick", "retired",
    "declared", "follow-on", "target",
]
FOOTBALL_MAJOR_KEYWORDS = [
    "goal", "scored", "penalty", "red card", "wins",
    "defeat", "equaliser", "equalizer", "hat-trick",
    "own goal", "extra time", "final score",
]


def _fetch_rss(url: str) -> list[str]:
    """Fetch RSS feed and return list of item titles."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "RAPTOR-Monitor/1.0"})
        with urllib.request.urlopen(req, timeout=10, context=_ssl_ctx) as resp:
            raw = resp.read()

        root = ET.fromstring(raw)
        channel = root.find("channel")
        items = channel.findall("item") if channel is not None else []

        titles = []
        for item in items[:10]:
            title_el = item.find("title")
            if title_el is not None and title_el.text:
                clean = re.sub(r"<[^>]+>", "", title_el.text).strip()
                titles.append(clean)
        return titles
    except Exception as e:
        print(f"[SPORTS_MONITOR] RSS fetch failed ({url}): {e}")
        return []


def fetch_cricket_headlines() -> list[str]:
    """Fetch current cricket score headlines."""
    return _fetch_rss(CRICKET_RSS)


def fetch_football_headlines() -> list[str]:
    """Fetch current football news headlines."""
    return _fetch_rss(FOOTBALL_RSS)


def detect_sports_events(
    current_headlines: list[str],
    previous_headlines: list[str] | None,
    sport: str = "cricket",
) -> list[dict]:
    """
    Compare current vs previous headlines and detect significant events.
    Pure function — testable without network calls.

    Args:
        current_headlines: List of current score/news headlines.
        previous_headlines: List from last check (None on first run).
        sport: "cricket" or "football" — determines keyword filter.
    """
    events: list[dict] = []

    if not current_headlines:
        return events

    # On first run, just record baseline — don't alert on everything
    if previous_headlines is None:
        return events

    # Find new headlines (not seen in previous check)
    prev_set = set(previous_headlines)
    new_headlines = [h for h in current_headlines if h not in prev_set]

    if not new_headlines:
        return events

    keywords = CRICKET_MAJOR_KEYWORDS if sport == "cricket" else FOOTBALL_MAJOR_KEYWORDS

    for headline in new_headlines:
        headline_lower = headline.lower()

        # Check if this headline contains a major event keyword
        is_major = any(kw in headline_lower for kw in keywords)

        if is_major:
            event_type = f"{sport}_major"
            events.append({
                "type": event_type,
                "message": f"{sport.capitalize()} update: {headline}",
                "suggestion": f"Want me to read the full {sport} scores?",
                "severity": "info",
            })

    # Cap at 2 events per check to avoid spam
    return events[:2]
