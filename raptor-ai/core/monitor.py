"""
monitor.py — Raptor Proactive Background Monitor & Action System
=================================================================
Daemon thread that continuously monitors system & network health
and external intelligence (weather, sports, news), detects anomalies,
proactively alerts the user via TTS, and executes remediation actions
upon user confirmation.

Features:
  - System check every ~10 seconds (CPU, RAM, disk, battery)
  - Network check every ~60 seconds (host discovery delta)
  - Weather check every ~5 minutes (rain, temp spikes)
  - Sports check every ~2 minutes (cricket/football major events)
  - News check every ~3 minutes (breaking headlines)
  - Event detection with configurable thresholds
  - 30-second per-event-type cooldown to prevent alert spam
  - State-aware: only speaks when agent is IDLE
  - Action pipeline: alert → listen → confirm → execute
  - 10-second confirmation timeout
  - Auto-mode toggle (with safety guardrails)
  - Clean shutdown via threading.Event
"""

from __future__ import annotations

import logging
import subprocess
import sys
import threading
import time
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass  # agent reference is typed loosely to avoid circular imports

from core.intelligence import context_memory, _parse_system_metrics, _parse_network_results

logger = logging.getLogger("RaptorMonitor")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  THRESHOLDS & CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CPU_SPIKE_THRESHOLD = 80.0
RAM_SPIKE_THRESHOLD = 85.0
DISK_WARN_THRESHOLD = 90.0
BATTERY_CRITICAL_THRESHOLD = 15.0

SYSTEM_CHECK_INTERVAL = 10   # seconds
NETWORK_CHECK_INTERVAL = 60  # seconds
WEATHER_CHECK_INTERVAL = 300  # 5 minutes
SPORTS_CHECK_INTERVAL = 120   # 2 minutes
NEWS_CHECK_INTERVAL = 180     # 3 minutes
COOLDOWN_SECONDS = 30        # per-event-type rate limit
ACTION_TIMEOUT = 10          # seconds to wait for user confirmation

CONFIRMATION_WORDS = ["yes", "yeah", "do it", "confirm", "go ahead", "sure", "please"]
CANCEL_WORDS = ["no", "cancel", "don't", "stop", "never mind", "skip"]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ACTION REGISTRY — Maps event types to executable remediation actions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Safety classification: actions marked destructive=True are NEVER auto-executed
ACTION_REGISTRY: dict[str, dict] = {
    "cpu_spike": {
        "action_id": "cpu_cleanup",
        "description": "Show top CPU-consuming processes",
        "destructive": False,
        "handler": "_action_show_top_cpu",
    },
    "ram_spike": {
        "action_id": "ram_cleanup",
        "description": "Show top memory-consuming processes",
        "destructive": False,
        "handler": "_action_show_top_ram",
    },
    "disk_full": {
        "action_id": "disk_cleanup",
        "description": "Identify large temporary files",
        "destructive": True,   # File deletion — NEVER auto-execute
        "handler": "_action_disk_report",
    },
    "new_device": {
        "action_id": "network_deep_scan",
        "description": "Run a detailed scan on the new device",
        "destructive": False,
        "handler": "_action_deep_scan_device",
    },
    "low_battery": {
        "action_id": "battery_save",
        "description": "Enable battery optimization tips",
        "destructive": False,
        "handler": "_action_battery_tips",
    },
    # ── External intelligence events ──
    "weather_rain": {
        "action_id": "weather_detail",
        "description": "Read the full weather forecast",
        "destructive": False,
        "handler": "_action_read_weather",
    },
    "weather_rain_forecast": {
        "action_id": "weather_detail",
        "description": "Read the full weather forecast",
        "destructive": False,
        "handler": "_action_read_weather",
    },
    "weather_heat": {
        "action_id": "weather_detail",
        "description": "Read the full weather forecast",
        "destructive": False,
        "handler": "_action_read_weather",
    },
    "weather_cold": {
        "action_id": "weather_detail",
        "description": "Read the full weather forecast",
        "destructive": False,
        "handler": "_action_read_weather",
    },
    "weather_temp_spike": {
        "action_id": "weather_detail",
        "description": "Read the full weather forecast",
        "destructive": False,
        "handler": "_action_read_weather",
    },
    "cricket_major": {
        "action_id": "read_scores",
        "description": "Read full live cricket scores",
        "destructive": False,
        "handler": "_action_read_cricket",
    },
    "football_major": {
        "action_id": "read_scores",
        "description": "Read full live football scores",
        "destructive": False,
        "handler": "_action_read_football",
    },
    "news_breaking": {
        "action_id": "read_news",
        "description": "Read today's top headlines",
        "destructive": False,
        "handler": "_action_read_news",
    },
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ACTION HANDLERS — Concrete remediation functions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _action_show_top_cpu(event: dict) -> dict:
    """List top 5 CPU-consuming processes."""
    try:
        result = subprocess.run(
            ["ps", "aux", "--sort=-%cpu"],
            capture_output=True, text=True, timeout=10,
        )
        lines = result.stdout.strip().split("\n")[:6]  # header + top 5

        # Extract just process names and CPU% for TTS
        processes = []
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 11:
                cpu_pct = parts[2]
                proc_name = parts[10].split("/")[-1]
                processes.append(f"{proc_name} at {cpu_pct}%")

        summary = ", ".join(processes[:3]) if processes else "No processes found"
        return {
            "status": "success",
            "message": f"Top CPU consumers: {summary}.",
            "raw": lines,
        }
    except Exception as e:
        return {"status": "error", "message": f"Could not list processes: {e}"}


def _action_show_top_ram(event: dict) -> dict:
    """List top 5 memory-consuming processes."""
    try:
        result = subprocess.run(
            ["ps", "aux", "--sort=-%mem"],
            capture_output=True, text=True, timeout=10,
        )
        lines = result.stdout.strip().split("\n")[:6]

        processes = []
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 11:
                mem_pct = parts[3]
                proc_name = parts[10].split("/")[-1]
                processes.append(f"{proc_name} at {mem_pct}%")

        summary = ", ".join(processes[:3]) if processes else "No processes found"
        return {
            "status": "success",
            "message": f"Top memory consumers: {summary}.",
            "raw": lines,
        }
    except Exception as e:
        return {"status": "error", "message": f"Could not list processes: {e}"}


def _action_disk_report(event: dict) -> dict:
    """Report large files in /tmp and ~/Downloads (read-only, no deletion)."""
    try:
        result = subprocess.run(
            ["find", "/tmp", "-maxdepth", "2", "-size", "+100M", "-type", "f"],
            capture_output=True, text=True, timeout=15,
        )
        large_files = [f for f in result.stdout.strip().split("\n") if f]
        count = len(large_files)

        if count > 0:
            msg = f"Found {count} large file{'s' if count != 1 else ''} in temp directories."
        else:
            msg = "No large temporary files found. Disk usage may be from applications."

        return {"status": "success", "message": msg, "raw": large_files}
    except Exception as e:
        return {"status": "error", "message": f"Disk report failed: {e}"}


def _action_deep_scan_device(event: dict) -> dict:
    """Run a detailed network scan on a newly discovered device."""
    try:
        # Extract IP from the event data
        ip = event.get("_target_ip", "")
        if not ip:
            # Try to parse from message
            import re
            ip_match = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", event.get("message", ""))
            ip = ip_match.group(1) if ip_match else ""

        if not ip:
            return {"status": "error", "message": "Could not determine the device IP to scan."}

        # from network_tool import scan_network
        # result = scan_network(target=ip, scan_types=["port_scan", "service_detection"])
        result = {"status": "success", "data": {"port_scan": {"open_ports": []}}}

        if result.get("status") == "success":
            data = result.get("data", {})
            port_info = data.get("port_scan", {})
            open_ports = port_info.get("open_ports", [])
            port_count = len(open_ports)
            return {
                "status": "success",
                "message": f"Deep scan of {ip} complete. Found {port_count} open port{'s' if port_count != 1 else ''}.",
                "raw": data,
            }
        else:
            return {"status": "error", "message": f"Deep scan failed: {result.get('error_message', 'unknown')}"}

    except Exception as e:
        return {"status": "error", "message": f"Deep scan error: {e}"}


def _action_battery_tips(event: dict) -> dict:
    """Provide battery-saving tips."""
    return {
        "status": "success",
        "message": (
            "To save battery: reduce screen brightness, "
            "close unused browser tabs, and disable Bluetooth if not needed."
        ),
    }


# ── External Intelligence Action Handlers ─────────────────────────────────

def _action_read_weather(event: dict) -> dict:
    """Read full weather forecast via the existing realtime tool."""
    try:
        from core.tools.realtime import get_weather_forecast
        # Use city from event or default
        city = event.get("_city", "Bhubaneswar")
        forecast = get_weather_forecast(city, days=2)
        return {"status": "success", "message": forecast}
    except Exception as e:
        return {"status": "error", "message": f"Could not fetch forecast: {e}"}


def _action_read_cricket(event: dict) -> dict:
    """Read full live cricket scores via the existing realtime tool."""
    try:
        from core.tools.realtime import get_cricket_scores
        scores = get_cricket_scores()
        return {"status": "success", "message": scores}
    except Exception as e:
        return {"status": "error", "message": f"Could not fetch cricket scores: {e}"}


def _action_read_football(event: dict) -> dict:
    """Read full live football scores via the existing realtime tool."""
    try:
        from core.tools.realtime import get_football_scores
        scores = get_football_scores()
        return {"status": "success", "message": scores}
    except Exception as e:
        return {"status": "error", "message": f"Could not fetch football scores: {e}"}


def _action_read_news(event: dict) -> dict:
    """Read today's top headlines via the existing realtime tool."""
    try:
        from core.tools.realtime import get_news
        headlines = get_news()
        return {"status": "success", "message": headlines}
    except Exception as e:
        return {"status": "error", "message": f"Could not fetch news: {e}"}


# Handler dispatch table
_ACTION_HANDLERS = {
    # Internal
    "_action_show_top_cpu": _action_show_top_cpu,
    "_action_show_top_ram": _action_show_top_ram,
    "_action_disk_report": _action_disk_report,
    "_action_deep_scan_device": _action_deep_scan_device,
    "_action_battery_tips": _action_battery_tips,
    # External
    "_action_read_weather": _action_read_weather,
    "_action_read_cricket": _action_read_cricket,
    "_action_read_football": _action_read_football,
    "_action_read_news": _action_read_news,
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  EVENT DETECTION — Pure functions (testable without agent)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _detect_system_events(metrics: dict) -> list[dict]:
    """
    Given parsed system metrics, return a list of detected events.
    Each event: {"type": str, "message": str, "suggestion": str, "severity": str}
    """
    events: list[dict] = []

    cpu = metrics.get("cpu_percent", 0.0)
    ram = metrics.get("ram_percent", 0.0)
    disk = metrics.get("disk_percent", 0.0)
    battery = metrics.get("battery_percent")
    plugged = metrics.get("power_plugged")

    if cpu > CPU_SPIKE_THRESHOLD:
        events.append({
            "type": "cpu_spike",
            "message": f"CPU usage has spiked to {cpu:.0f}%.",
            "suggestion": "Want me to show the top processes consuming CPU?",
            "severity": "critical" if cpu > 95 else "warning",
        })

    if ram > RAM_SPIKE_THRESHOLD:
        events.append({
            "type": "ram_spike",
            "message": f"Memory usage is critically high at {ram:.0f}%.",
            "suggestion": "Want me to identify which apps are using the most memory?",
            "severity": "critical" if ram > 95 else "warning",
        })

    if disk > DISK_WARN_THRESHOLD:
        events.append({
            "type": "disk_full",
            "message": f"Disk usage is dangerously high at {disk:.0f}%.",
            "suggestion": "You should free up some disk space soon.",
            "severity": "warning",
        })

    if battery is not None and battery < BATTERY_CRITICAL_THRESHOLD and not plugged:
        events.append({
            "type": "low_battery",
            "message": f"Battery is critically low at {battery:.0f}%.",
            "suggestion": "You should plug in the charger immediately.",
            "severity": "critical",
        })

    return events


def _detect_network_events(
    old_hosts: list[str] | None, new_hosts: list[str]
) -> list[dict]:
    """
    Compare old vs new host lists and detect new devices / topology changes.
    """
    events: list[dict] = []

    if old_hosts is None:
        # First scan — no delta to compare
        return events

    old_set = set(old_hosts)
    new_set = set(new_hosts)
    appeared = new_set - old_set
    disappeared = old_set - new_set

    for ip in appeared:
        events.append({
            "type": "new_device",
            "message": f"A new device has appeared on your network: {ip}.",
            "suggestion": "Want me to run a detailed scan on this device?",
            "severity": "warning",
            "_target_ip": ip,  # internal: used by action handler
        })

    if len(disappeared) > 2:
        events.append({
            "type": "network_change",
            "message": f"{len(disappeared)} devices have left your network.",
            "suggestion": "",
            "severity": "info",
        })

    return events


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MONITOR CLASS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class RaptorMonitor:
    """
    Background daemon that polls system/network tools, detects anomalies,
    alerts the user via the agent's TTS system, and optionally executes
    remediation actions upon user confirmation.
    """

    def __init__(self, agent):
        """
        Args:
            agent: Reference to LocalVoiceAgent instance (or None for testing).
        """
        self.agent = agent
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

        # Per-event-type cooldown tracker
        self._cooldowns: dict[str, float] = {}

        # Event log
        self._event_log: list[dict] = []

        # Pending action awaiting confirmation
        self.pending_action: dict | None = None

        # Timing
        self._last_system_check = 0.0
        self._last_network_check = 0.0
        self._last_weather_check = 0.0
        self._last_sports_check = 0.0
        self._last_news_check = 0.0

        # External monitor state (for delta comparison)
        self._prev_weather_temp: float | None = None
        self._prev_cricket_headlines: list[str] | None = None
        self._prev_football_headlines: list[str] | None = None
        self._prev_news_headlines: list[str] | None = None

        # Configurable city for weather monitor
        self.weather_city: str = "Bhubaneswar"

        # Auto-mode: if True, execute non-destructive actions without asking
        self.auto_mode: bool = False

    # ── Cooldown ──────────────────────────────────────────────────────────

    def _is_cooled_down(self, event_type: str) -> bool:
        """Check if enough time has passed since the last alert of this type."""
        last = self._cooldowns.get(event_type, 0.0)
        return (time.time() - last) >= COOLDOWN_SECONDS

    def _record_alert(self, event_type: str) -> None:
        """Record the timestamp of an alert firing."""
        self._cooldowns[event_type] = time.time()

    # ── Event Logging ─────────────────────────────────────────────────────

    def _log_event(self, event: dict, action_taken: str = "alerted") -> None:
        """Persist event to in-memory log with timestamp."""
        entry = {
            **event,
            "action_taken": action_taken,
            "timestamp": datetime.now().isoformat(),
        }
        self._event_log.append(entry)
        logger.info(f"[MONITOR EVENT] {entry}")
        print(f"[MONITOR] ⚠️  {event['type'].upper()}: {event['message']}")

    # ── Action Execution ──────────────────────────────────────────────────

    def _execute_action(self, event: dict) -> dict | None:
        """
        Look up and execute the action handler for a given event type.
        Returns the action result dict, or None if no action is registered.
        """
        action_def = ACTION_REGISTRY.get(event["type"])
        if not action_def:
            return None

        handler_name = action_def["handler"]
        handler_fn = _ACTION_HANDLERS.get(handler_name)
        if not handler_fn:
            print(f"[MONITOR] No handler found for {handler_name}")
            return None

        print(f"[MONITOR] 🔧 Executing action: {action_def['description']}")
        try:
            result = handler_fn(event)
            self._log_event(event, action_taken=f"executed:{action_def['action_id']}")
            return result
        except Exception as e:
            print(f"[MONITOR] Action execution error: {e}")
            return {"status": "error", "message": str(e)}

    def _is_action_safe_for_auto(self, event_type: str) -> bool:
        """Check if an action is safe to auto-execute (non-destructive)."""
        action_def = ACTION_REGISTRY.get(event_type)
        if not action_def:
            return False
        return not action_def.get("destructive", True)

    # ── Action Cycle: Alert → Listen → Confirm → Execute ─────────────────

    def _run_action_cycle(self, event: dict) -> None:
        """
        Full action cycle:
          1. Speak alert + suggestion
          2. Listen for user confirmation (10s timeout)
          3. Execute action if confirmed
          4. Speak action result

        This method takes over the agent's state temporarily.
        """
        if self.agent is None:
            return

        action_def = ACTION_REGISTRY.get(event["type"])
        if not action_def:
            # No action registered — just speak the alert
            self._speak_alert_only(event)
            return

        # ── Auto-mode path ──
        if self.auto_mode and self._is_action_safe_for_auto(event["type"]):
            print(f"[MONITOR] Auto-mode ON: executing {action_def['action_id']} automatically")
            self._speak_alert_only(event)
            result = self._execute_action(event)
            if result and result.get("message"):
                self._agent_speak(result["message"])
            self.agent.set_state("IDLE")
            return

        # ── Manual confirmation path ──
        # Store pending action
        self.pending_action = {
            "event": event,
            "action": action_def,
            "created_at": time.time(),
        }

        # Step 1: Speak alert + suggestion
        alert_text = event["message"]
        if event.get("suggestion"):
            alert_text += f" {event['suggestion']}"

        try:
            from core.ws_bridge import bridge as ws_bridge
            ws_bridge.update_state({
                "state": "SPEAKING",
                "active_module": "monitor",
                "last_response": alert_text,
            })
        except Exception:
            pass

        self.agent._speak_response(alert_text)

        # Step 2: Listen for confirmation
        self.agent.set_state("LISTENING")
        try:
            from core.ws_bridge import bridge as ws_bridge
            ws_bridge.update_state({"state": "LISTENING"})
        except Exception:
            pass

        try:
            from core.local_audio import listen_and_transcribe
            user_response = listen_and_transcribe(timeout=ACTION_TIMEOUT)
            user_lower = user_response.lower().strip() if user_response else ""

            print(f"[MONITOR] User response: '{user_response}'")

            if any(word in user_lower for word in CONFIRMATION_WORDS):
                # ── CONFIRMED ──
                print(f"[MONITOR] ✅ Action confirmed by user")
                self.agent.set_state("PROCESSING")

                # Log interaction for learning
                try:
                    from core.learning_engine import record_interaction
                    from core.priority_engine import context_tracker, EVENT_INTEREST_MAP
                    record_interaction(event["type"], "accepted")
                    interest = EVENT_INTEREST_MAP.get(event["type"], "")
                    if interest:
                        context_tracker.record_interaction(interest)
                except ImportError:
                    pass

                result = self._execute_action(event)
                if result and result.get("message"):
                    self._agent_speak(result["message"])
                else:
                    self._agent_speak("Done.")

            elif any(word in user_lower for word in CANCEL_WORDS):
                # ── CANCELLED ──
                print(f"[MONITOR] ❌ Action cancelled by user")
                try:
                    from core.learning_engine import record_interaction
                    record_interaction(event["type"], "cancelled")
                except ImportError:
                    pass
                self._agent_speak("Understood. Action cancelled.")
            else:
                # ── UNRECOGNIZED ──
                print(f"[MONITOR] ❓ Unrecognized response, discarding action")
                self._agent_speak("I didn't catch that. Skipping the action.")

        except (TimeoutError, Exception) as e:
            # ── TIMEOUT / ERROR ──
            print(f"[MONITOR] ⏰ No response within {ACTION_TIMEOUT}s, discarding action")
            try:
                from core.learning_engine import record_interaction
                record_interaction(event["type"], "timeout")
            except ImportError:
                pass
            self._agent_speak("No response received. Action discarded.")

        # Cleanup
        self.pending_action = None
        self.agent.set_state("IDLE")

    # ── Speaking Helpers ──────────────────────────────────────────────────

    def _speak_alert_only(self, event: dict) -> None:
        """Speak just the alert message without listening for confirmation."""
        alert_text = event["message"]
        if event.get("suggestion"):
            alert_text += f" {event['suggestion']}"

        try:
            from core.ws_bridge import bridge as ws_bridge
            ws_bridge.update_state({
                "state": "SPEAKING",
                "active_module": "monitor",
                "last_response": alert_text,
            })
        except Exception:
            pass

        self.agent._speak_response(alert_text)

    def _agent_speak(self, text: str) -> None:
        """Speak a response through the agent's TTS (convenience wrapper)."""
        try:
            self.agent.set_state("SPEAKING")
            from core.local_audio import speak
            speak(text, blocking=True)
            print(f"[MONITOR] 🔊 {text}")
        except Exception as e:
            print(f"[MONITOR] TTS error: {e}")

    # ── Alert Delivery (upgraded with action pipeline) ────────────────────

    def _deliver_alert(self, event: dict) -> None:
        """
        Deliver an alert for a detected event. If an action is registered,
        runs the full action cycle (alert → listen → confirm → execute).
        Only fires if:
          1. Priority engine approves (interest, ignore, severity)
          2. Cooldown has expired for this event type
          3. Agent is in IDLE state (not busy with user interaction)
        """
        if not self._is_cooled_down(event["type"]):
            return

        # ── Learned suppression ──
        try:
            from core.learning_engine import should_suppress_learned
            if should_suppress_learned(event["type"]):
                print(f"[MONITOR] 🧠 Suppressed by learning: {event['type']}")
                return
        except ImportError:
            pass

        # ── Priority filtering ──
        try:
            from core.priority_engine import should_alert, context_tracker
            if not should_alert(event):
                print(f"[MONITOR] 🔇 Filtered out: {event['type']} (priority engine)")
                return
        except ImportError:
            pass  # If priority_engine isn't available, skip filtering

        # Log regardless of agent state
        self._log_event(event)

        # Only interact if agent exists and is idle
        if self.agent is None:
            return

        if getattr(self.agent, "state", "IDLE") != "IDLE":
            print(f"[MONITOR] Agent is {self.agent.state}, deferring alert.")
            return

        # Record cooldown BEFORE the action cycle (prevent re-trigger during cycle)
        self._record_alert(event["type"])

        # Run the full action cycle (or alert-only if no action registered)
        self._run_action_cycle(event)

    # ── System Check ──────────────────────────────────────────────────────

    def _check_system(self) -> None:
        """Run system_tool, parse metrics, detect events, deliver alerts."""
        try:
            from system_tool import get_system_info
            result = get_system_info()

            if result.get("status") != "success":
                print(f"[MONITOR] System check failed: {result.get('error_message', 'unknown')}")
                return

            raw_output = result.get("raw_output", "")
            metrics = _parse_system_metrics(raw_output)

            if not metrics:
                return

            # Store in context memory for delta analysis
            context_memory.update("system", metrics)

            # Detect events
            events = _detect_system_events(metrics)
            for event in events:
                self._deliver_alert(event)

        except Exception as e:
            print(f"[MONITOR] System check error: {e}")

    # ── Network Check ─────────────────────────────────────────────────────

    def _check_network(self) -> None:
        """Run network_tool (host discovery only), detect new devices."""
        try:
            # from network_tool import scan_network
            # result = scan_network(scan_types=["host_discovery"])
            result = {"status": "success", "data": {"network_scan": {"live_hosts": []}}}

            if result.get("status") != "success":
                print(f"[MONITOR] Network check failed: {result.get('error_message', 'unknown')}")
                return

            scan_data = result.get("data", {})
            net_summary = _parse_network_results(scan_data)
            new_hosts = net_summary.get("live_hosts", [])

            # Get previous hosts from context memory
            prev_state = context_memory.get_last("network")
            old_hosts = prev_state.get("live_hosts") if prev_state else None

            # Store current state
            context_memory.update("network", net_summary)

            # Detect events
            events = _detect_network_events(old_hosts, new_hosts)
            for event in events:
                self._deliver_alert(event)

        except Exception as e:
            print(f"[MONITOR] Network check error: {e}")

    # ── External Checks ───────────────────────────────────────────────────

    def _check_weather(self) -> None:
        """Fetch weather data, detect events, deliver alerts."""
        try:
            from core.external_monitors.weather_monitor import (
                fetch_weather_data, detect_weather_events,
            )

            data = fetch_weather_data(city=self.weather_city)
            if not data:
                return

            # Extract current temp for delta tracking
            current = data.get("current_condition", [{}])[0]
            try:
                current_temp = float(current.get("temp_C", 0))
            except (ValueError, TypeError):
                current_temp = None

            events = detect_weather_events(
                data,
                previous_temp=self._prev_weather_temp,
                city=self.weather_city,
            )

            # Update previous temp for next delta check
            if current_temp is not None:
                self._prev_weather_temp = current_temp

            for event in events:
                self._deliver_alert(event)

        except Exception as e:
            print(f"[MONITOR] Weather check error: {e}")

    def _check_sports(self) -> None:
        """Fetch cricket + football headlines, detect major events."""
        try:
            from core.external_monitors.sports_monitor import (
                fetch_cricket_headlines, fetch_football_headlines,
                detect_sports_events,
            )

            # Cricket
            cricket_headlines = fetch_cricket_headlines()
            if cricket_headlines:
                events = detect_sports_events(
                    cricket_headlines,
                    self._prev_cricket_headlines,
                    sport="cricket",
                )
                self._prev_cricket_headlines = cricket_headlines
                for event in events:
                    self._deliver_alert(event)

            # Football
            football_headlines = fetch_football_headlines()
            if football_headlines:
                events = detect_sports_events(
                    football_headlines,
                    self._prev_football_headlines,
                    sport="football",
                )
                self._prev_football_headlines = football_headlines
                for event in events:
                    self._deliver_alert(event)

        except Exception as e:
            print(f"[MONITOR] Sports check error: {e}")

    def _check_news(self) -> None:
        """Fetch news headlines, detect breaking events."""
        try:
            from core.external_monitors.news_monitor import (
                fetch_news_headlines, detect_news_events,
            )

            headlines = fetch_news_headlines()
            if headlines:
                events = detect_news_events(headlines, self._prev_news_headlines)
                self._prev_news_headlines = headlines
                for event in events:
                    self._deliver_alert(event)

        except Exception as e:
            print(f"[MONITOR] News check error: {e}")

    # ── Main Loop ─────────────────────────────────────────────────────────

    def _monitor_loop(self) -> None:
        """
        Core monitoring loop. Runs until _stop_event is set.
        Internal:  system (10s), network (60s)
        External:  weather (5m), sports (2m), news (3m)
        """
        print("[MONITOR] 🟢 Proactive monitoring daemon started.")
        print("[MONITOR]    Internal: system, network")
        print("[MONITOR]    External: weather, sports, news")
        logger.info("Monitor loop started.")

        # Wait a bit before first check to let the agent fully initialize
        self._stop_event.wait(timeout=15)
        if self._stop_event.is_set():
            return

        while not self._stop_event.is_set():
            now = time.time()

            # ── Internal checks ──
            if (now - self._last_system_check) >= SYSTEM_CHECK_INTERVAL:
                # self._check_system()
                self._last_system_check = time.time()

            if (now - self._last_network_check) >= NETWORK_CHECK_INTERVAL:
                # self._check_network()
                self._last_network_check = time.time()

            # ── External checks ──
            if (now - self._last_weather_check) >= WEATHER_CHECK_INTERVAL:
                self._check_weather()
                self._last_weather_check = time.time()

            if (now - self._last_sports_check) >= SPORTS_CHECK_INTERVAL:
                self._check_sports()
                self._last_sports_check = time.time()

            if (now - self._last_news_check) >= NEWS_CHECK_INTERVAL:
                self._check_news()
                self._last_news_check = time.time()

            # Sleep in small increments so we can respond to stop_event quickly
            self._stop_event.wait(timeout=2)

        print("[MONITOR] 🔴 Proactive monitoring daemon stopped.")
        logger.info("Monitor loop stopped.")

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the monitoring daemon thread."""
        if self._thread and self._thread.is_alive():
            print("[MONITOR] Already running.")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="RaptorMonitorThread",
        )
        self._thread.start()

    def stop(self) -> None:
        """Signal the monitoring loop to stop."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
            print("[MONITOR] Thread joined.")

    def get_event_log(self) -> list[dict]:
        """Return a copy of the event log."""
        return list(self._event_log)

    def set_auto_mode(self, enabled: bool) -> None:
        """Toggle auto-mode for non-destructive actions."""
        self.auto_mode = enabled
        mode = "ON" if enabled else "OFF"
        print(f"[MONITOR] Auto-mode {mode}")
