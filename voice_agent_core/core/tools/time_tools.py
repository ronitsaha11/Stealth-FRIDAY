"""Alarm and timer helpers for Raptor."""

from __future__ import annotations

import datetime
import threading
import time


def _get_speak():
    """Import TTS lazily to avoid circular imports."""
    from core.local_audio import speak

    return speak


def _parse_alarm_time(time_str: str) -> datetime.datetime | None:
    normalized = " ".join(time_str.strip().upper().split())
    for fmt in ("%H:%M", "%I:%M %p", "%I:%M%p", "%I %p", "%I%p"):
        try:
            return datetime.datetime.strptime(normalized, fmt)
        except ValueError:
            continue
    return None


def set_timer(seconds: int) -> str:
    """Start a background timer and speak when it finishes."""
    if seconds <= 0:
        return "Timer duration must be greater than zero seconds."

    print(f"[TIME] Timer scheduled for {seconds} seconds.")

    def _run():
        time.sleep(seconds)
        speak = _get_speak()
        speak("Time is up")

    threading.Thread(target=_run, daemon=True).start()
    return f"Timer started for {seconds} seconds."


def set_alarm(time_str: str) -> str:
    """Schedule an alarm for today or tomorrow."""
    parsed_time = _parse_alarm_time(time_str)
    if parsed_time is None:
        return (
            f"Could not parse alarm time '{time_str}'. "
            "Try formats like '07:30', '7:30 AM', or '7 AM'."
        )

    now = datetime.datetime.now()
    alarm_at = now.replace(
        hour=parsed_time.hour,
        minute=parsed_time.minute,
        second=0,
        microsecond=0,
    )
    if alarm_at <= now:
        alarm_at += datetime.timedelta(days=1)

    wait_seconds = max((alarm_at - now).total_seconds(), 0)
    friendly_time = alarm_at.strftime("%I:%M %p")
    print(f"[TIME] Alarm scheduled for {friendly_time}.")

    def _run():
        time.sleep(wait_seconds)
        speak = _get_speak()
        speak(f"Alarm. It is {friendly_time}.")

    threading.Thread(target=_run, daemon=True).start()
    return f"Alarm set for {friendly_time}."


def register(mcp):
    @mcp.tool(name="set_timer")
    def timer_tool(seconds: int) -> str:
        """Start a timer in seconds."""
        return set_timer(seconds)

    @mcp.tool(name="set_alarm")
    def alarm_tool(time_str: str) -> str:
        """Set an alarm for a clock time."""
        return set_alarm(time_str)
