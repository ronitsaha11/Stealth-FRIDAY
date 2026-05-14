"""
news_monitor.py — Breaking News Event Detector
================================================
Periodically fetches top headlines from NYT RSS and detects
breaking or major news events by comparing against previous
headlines and filtering for significance keywords.

Uses the same free NYT RSS feed as the existing get_news() tool —
no API key required.
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

# ── RSS Feed ─────────────────────────────────────────────────────────────

NEWS_RSS = "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"

# ── Keywords that indicate a breaking / major event ──────────────────────

BREAKING_KEYWORDS = [
    "breaking", "urgent", "just in", "developing",
    "emergency", "crisis", "killed", "explosion",
    "earthquake", "tsunami", "attack", "war",
    "assassination", "crashed", "shooting",
    "declared", "elected", "resigned", "impeach",
    "pandemic", "outbreak",
]

# Keywords that indicate lower-significance stories (skip these)
NOISE_KEYWORDS = [
    "opinion", "review", "recipe", "style",
    "crossword", "podcast", "newsletter",
]


def fetch_news_headlines() -> list[str]:
    """Fetch top 10 headlines from NYT RSS."""
    try:
        req = urllib.request.Request(NEWS_RSS, headers={"User-Agent": "RAPTOR-Monitor/1.0"})
        with urllib.request.urlopen(req, timeout=10, context=_ssl_ctx) as resp:
            raw = resp.read()

        root = ET.fromstring(raw)
        channel = root.find("channel")
        items = channel.findall("item") if channel is not None else []

        headlines = []
        for item in items[:10]:
            title_el = item.find("title")
            if title_el is not None and title_el.text:
                clean = re.sub(r"<[^>]+>", "", title_el.text).strip()
                headlines.append(clean)
        return headlines
    except Exception as e:
        print(f"[NEWS_MONITOR] Fetch failed: {e}")
        return []


def detect_news_events(
    current_headlines: list[str],
    previous_headlines: list[str] | None,
) -> list[dict]:
    """
    Compare current vs previous headlines and detect breaking news.
    Pure function — testable without network calls.

    Args:
        current_headlines: List of current top headlines.
        previous_headlines: List from last check (None on first run).
    """
    events: list[dict] = []

    if not current_headlines:
        return events

    # On first run, just record baseline
    if previous_headlines is None:
        return events

    # Find new headlines
    prev_set = set(previous_headlines)
    new_headlines = [h for h in current_headlines if h not in prev_set]

    if not new_headlines:
        return events

    for headline in new_headlines:
        headline_lower = headline.lower()

        # Skip noise
        if any(kw in headline_lower for kw in NOISE_KEYWORDS):
            continue

        # Check for breaking/major keywords
        is_breaking = any(kw in headline_lower for kw in BREAKING_KEYWORDS)

        if is_breaking:
            events.append({
                "type": "news_breaking",
                "message": f"Breaking news: {headline}",
                "suggestion": "Want me to read more headlines?",
                "severity": "warning",
            })

    # Cap at 1 breaking news alert per check
    return events[:1]
