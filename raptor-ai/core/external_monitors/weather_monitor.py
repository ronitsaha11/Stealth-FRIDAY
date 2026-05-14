"""
weather_monitor.py — External Weather Event Detector
=====================================================
Periodically fetches weather data from wttr.in and detects
significant weather events: incoming rain, temperature extremes,
and severe conditions.

Uses the same free wttr.in JSON endpoint as the existing
get_weather_forecast() tool — no API key required.
"""

from __future__ import annotations

import json
import re
import ssl
import urllib.request
from typing import Any

# SSL context for wttr.in (macOS may lack system CA certs)
_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE

# ── Configurable thresholds ──────────────────────────────────────────────

TEMP_HIGH_THRESHOLD = 40.0   # °C — extreme heat
TEMP_LOW_THRESHOLD = 5.0     # °C — extreme cold
TEMP_SPIKE_DELTA = 8.0       # °C — sudden change from last check

# Weather descriptions that indicate rain/storm
RAIN_KEYWORDS = [
    "rain", "drizzle", "shower", "thunderstorm", "thunder",
    "sleet", "downpour", "precipitation", "storm",
]
SEVERE_KEYWORDS = [
    "thunderstorm", "heavy rain", "blizzard", "hurricane",
    "tornado", "hail", "severe", "cyclone",
]

# Default city (overridden by user config)
DEFAULT_CITY = "Bhubaneswar"


def fetch_weather_data(city: str = DEFAULT_CITY) -> dict | None:
    """
    Fetch current + forecast data from wttr.in JSON endpoint.
    Returns raw JSON dict or None on failure.
    """
    city_clean = city.strip().replace(" ", "+")
    url = f"https://wttr.in/{city_clean}?format=j1"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "RAPTOR-Monitor/1.0"})
        with urllib.request.urlopen(req, timeout=10, context=_ssl_ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[WEATHER_MONITOR] Fetch failed: {e}")
        return None


def detect_weather_events(
    data: dict,
    previous_temp: float | None = None,
    city: str = DEFAULT_CITY,
) -> list[dict]:
    """
    Analyze weather data and return detected events.
    Pure function — testable without network calls.
    """
    events: list[dict] = []

    if not data:
        return events

    # ── Current conditions ──
    current = data.get("current_condition", [{}])[0]
    temp_c_str = current.get("temp_C", "")
    desc = current.get("weatherDesc", [{}])[0].get("value", "").lower()
    feels_like_str = current.get("FeelsLikeC", "")

    try:
        temp_c = float(temp_c_str) if temp_c_str else None
    except ValueError:
        temp_c = None

    try:
        feels_like = float(feels_like_str) if feels_like_str else None
    except ValueError:
        feels_like = None

    # Rain / storm detection (current)
    if any(kw in desc for kw in RAIN_KEYWORDS):
        severity = "critical" if any(kw in desc for kw in SEVERE_KEYWORDS) else "warning"
        events.append({
            "type": "weather_rain",
            "message": f"Weather alert for {city}: {desc.capitalize()} reported right now.",
            "suggestion": "You might want to carry an umbrella if heading out.",
            "severity": severity,
        })

    # Extreme heat
    if temp_c is not None and temp_c > TEMP_HIGH_THRESHOLD:
        events.append({
            "type": "weather_heat",
            "message": f"Extreme heat in {city}: {temp_c:.0f}°C right now.",
            "suggestion": "Stay hydrated and avoid direct sun exposure.",
            "severity": "warning",
        })

    # Extreme cold
    if temp_c is not None and temp_c < TEMP_LOW_THRESHOLD:
        events.append({
            "type": "weather_cold",
            "message": f"Very cold in {city}: {temp_c:.0f}°C right now.",
            "suggestion": "Bundle up if you're going outside.",
            "severity": "warning",
        })

    # Temperature spike (compared to last check)
    if temp_c is not None and previous_temp is not None:
        delta = abs(temp_c - previous_temp)
        if delta >= TEMP_SPIKE_DELTA:
            direction = "risen" if temp_c > previous_temp else "dropped"
            events.append({
                "type": "weather_temp_spike",
                "message": f"Temperature in {city} has {direction} by {delta:.0f}°C to {temp_c:.0f}°C.",
                "suggestion": "",
                "severity": "warning",
            })

    # ── Forecast: check next few hours for incoming rain ──
    weather_days = data.get("weather", [])
    if weather_days:
        today = weather_days[0]
        hourly = today.get("hourly", [])
        for hour_data in hourly[:4]:  # next ~12 hours
            hour_desc = hour_data.get("weatherDesc", [{}])[0].get("value", "").lower()
            hour_time = hour_data.get("time", "")
            if any(kw in hour_desc for kw in RAIN_KEYWORDS):
                # Only alert once for upcoming rain
                if not any(e["type"] == "weather_rain" for e in events):
                    events.append({
                        "type": "weather_rain_forecast",
                        "message": f"Rain is expected later in {city}: {hour_desc.capitalize()}.",
                        "suggestion": "Consider carrying an umbrella.",
                        "severity": "info",
                    })
                break

    return events
