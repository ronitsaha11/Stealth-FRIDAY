"""
intelligence.py — Raptor Decision Engine
=========================================
Sits between raw tool output and the agent's spoken response.
Provides:
  - select_tools()    : programmatic intent → tool mapping for automation-engine
  - analyze_results() : post-execution threshold analysis & recommendations
  - synthesize_response() : converts analyzed data → concise TTS-ready text
  - ContextMemory     : stores last system/network/browser states for delta comparison
  - execute_intelligent() : wraps execute_plan with analysis + memory + synthesis
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from core.executor import execute_plan


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  1. TOOL SELECTOR — Intent → Tool Mapping
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_INTENT_MAP: list[tuple[list[str], list[dict]]] = [
    # ── Multi-tool composites (MUST be checked FIRST — they contain
    #    substrings like "check system" that would match individual entries) ──
    (
        [
            "full diagnostics", "full system check", "complete diagnostics",
            "check everything", "system and network",
            "check system and network", "system and network status",
        ],
        [
            {"tool": "automation_system_info", "args": {}},
            {"tool": "automation_network_scan", "args": {}},
        ],
    ),
    # ── System optimization (analysis pass) ──
    (
        [
            "optimize system", "performance report", "system optimization",
            "improve performance", "speed up system", "system diagnostics",
        ],
        [{"tool": "automation_system_analyze", "args": {}}],
    ),
    # ── System diagnostics ──
    (
        [
            "system status", "system info", "system information",
            "cpu usage", "memory usage", "disk space", "disk usage",
            "check system", "how is my system", "system health",
            "device info", "hardware info", "battery status",
            "running processes", "top processes", "system report",
        ],
        [{"tool": "automation_system_info", "args": {}}],
    ),
    # ── Network scanning ──
    (
        [
            "scan network", "check network",
        ],
        [{"tool": "automation_network_scan", "args": {}}],
    ),
    # ── Browser / IP ──
    (
        ["my ip", "public ip", "what is my ip", "current ip", "check ip", "ip address"],
        [{"tool": "automation_get_ip", "args": {}}],
    ),
    (
        ["rotate session", "change ip", "new session", "rotate browser", "session rotation"],
        [{"tool": "automation_rotate_session", "args": {}}],
    ),
    (
        ["inject fingerprint", "randomize fingerprint", "spoof fingerprint", "change fingerprint"],
        [{"tool": "automation_inject_fingerprint", "args": {}}],
    ),
    # ── Browser Intelligence ──
    (
        [
            "what is this page", "what page is this", "current page",
            "what am i looking at", "describe this page", "current tab",
        ],
        [{"tool": "browser_get_page", "args": {}}],
    ),
    (
        [
            "summarize this page", "summarize this", "page summary",
            "summarize the page", "whats this page about",
        ],
        [{"tool": "browser_summarize", "args": {}}],
    ),
]


def select_tools(intent: str) -> list[dict] | None:
    """
    Given a natural-language intent string, return the matching
    automation-engine tool plan, or None if no match.
    """
    normalized = intent.lower().strip()
    normalized_clean = re.sub(r"[^\w\s]", "", normalized)

    for keywords, plan in _INTENT_MAP:
        if any(kw in normalized_clean for kw in keywords):
            # Deep-copy to avoid mutation of the template
            return [dict(step) for step in plan]

    # Check for targeted network scan with IP/range
    net_match = re.search(
        r"(?:scan|port\s+scan|network\s+scan)\s+"
        r"((?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?)",
        normalized,
    )
    if net_match:
        return [{"tool": "automation_network_scan", "args": {"target": net_match.group(1)}}]

    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  2. CONTEXT MEMORY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ContextMemory:
    """In-memory store for last-known states from automation tools."""

    def __init__(self):
        self._store: dict[str, dict[str, Any]] = {}
        self._timestamps: dict[str, datetime] = {}

    def update(self, domain: str, data: dict) -> None:
        """Store latest state for a domain (system | network | browser)."""
        self._store[domain] = data
        self._timestamps[domain] = datetime.now()

    def get_last(self, domain: str) -> dict | None:
        """Retrieve last stored state for a domain."""
        return self._store.get(domain)

    def get_timestamp(self, domain: str) -> datetime | None:
        """When was the last state recorded."""
        return self._timestamps.get(domain)

    def get_delta(self, domain: str, current: dict) -> dict:
        """
        Compare current metrics to last-stored metrics.
        Returns a dict of {metric_key: (old_value, new_value)} for changed fields.
        """
        previous = self._store.get(domain, {})
        delta = {}
        for key in set(list(previous.keys()) + list(current.keys())):
            old_val = previous.get(key)
            new_val = current.get(key)
            if old_val != new_val:
                delta[key] = (old_val, new_val)
        return delta

    def clear(self, domain: str | None = None) -> None:
        if domain:
            self._store.pop(domain, None)
            self._timestamps.pop(domain, None)
        else:
            self._store.clear()
            self._timestamps.clear()


# Singleton instance — shared across the agent's lifetime
context_memory = ContextMemory()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  3. RESULT ANALYSIS — Threshold Detection & Recommendations
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Thresholds
_CPU_WARN = 80.0
_MEM_WARN = 85.0
_DISK_WARN = 90.0


def _parse_system_metrics(raw_output: str) -> dict:
    """
    Extract numeric metrics from system_info.py's raw text output.
    Returns a dict with keys like cpu_percent, ram_percent, disk_percent, etc.
    """
    metrics: dict[str, Any] = {}

    # CPU overall usage
    cpu_match = re.search(r"CPU Usage Overall:\s*([\d.]+)%", raw_output)
    if cpu_match:
        metrics["cpu_percent"] = float(cpu_match.group(1))

    # Physical / logical cores
    phys = re.search(r"Physical Cores:\s*(\d+)", raw_output)
    if phys:
        metrics["physical_cores"] = int(phys.group(1))
    logical = re.search(r"Total Cores:\s*(\d+)", raw_output)
    if logical:
        metrics["total_cores"] = int(logical.group(1))

    # RAM
    ram_total = re.search(r"Total RAM:\s*([\d.]+)\s*GB", raw_output)
    ram_used = re.search(r"Used RAM:\s*([\d.]+)\s*GB", raw_output)
    ram_pct = re.search(r"RAM Usage:\s*([\d.]+)%", raw_output)
    if ram_total:
        metrics["ram_total_gb"] = float(ram_total.group(1))
    if ram_used:
        metrics["ram_used_gb"] = float(ram_used.group(1))
    if ram_pct:
        metrics["ram_percent"] = float(ram_pct.group(1))

    # Disk (first partition)
    disk_pct = re.search(r"Usage:\s*([\d.]+)%", raw_output)
    if disk_pct:
        metrics["disk_percent"] = float(disk_pct.group(1))
    disk_free = re.search(r"Free:\s*([\d.]+)\s*GB", raw_output)
    if disk_free:
        metrics["disk_free_gb"] = float(disk_free.group(1))

    # Battery
    batt = re.search(r"Battery Percentage:\s*([\d.]+)%", raw_output)
    if batt:
        metrics["battery_percent"] = float(batt.group(1))
    plugged = re.search(r"Power Plugged:\s*(Yes|No)", raw_output)
    if plugged:
        metrics["power_plugged"] = plugged.group(1) == "Yes"

    return metrics


def _parse_network_results(data: dict) -> dict:
    """Extract structured summary from network scan results."""
    summary: dict[str, Any] = {}

    host_disc = data.get("host_discovery", {})
    summary["live_hosts"] = host_disc.get("live_hosts", [])
    summary["host_count"] = host_disc.get("host_count", 0)

    port_scan = data.get("port_scan", {})
    summary["open_ports"] = port_scan.get("open_ports", [])
    summary["open_port_count"] = len(summary["open_ports"])
    summary["target"] = port_scan.get("target", "unknown")

    return summary


def analyze_results(tool_name: str, result: dict) -> dict:
    """
    Post-execution analysis. Returns an enriched dict with:
      - parsed metrics
      - warnings (list of strings)
      - recommendations (list of strings)
      - severity ("ok" | "warning" | "critical")
    """
    analysis: dict[str, Any] = {
        "tool": tool_name,
        "warnings": [],
        "recommendations": [],
        "severity": "ok",
        "metrics": {},
    }

    if result.get("status") != "success":
        analysis["severity"] = "error"
        analysis["warnings"].append(result.get("error_message", "Tool execution failed."))
        return analysis

    # ── System info analysis ──
    if tool_name in ("automation_system_info", "automation_system_analyze"):
        raw = result.get("raw_output", "")
        metrics = _parse_system_metrics(raw)
        analysis["metrics"] = metrics

        cpu = metrics.get("cpu_percent", 0)
        ram = metrics.get("ram_percent", 0)
        disk = metrics.get("disk_percent", 0)

        if cpu > _CPU_WARN:
            analysis["warnings"].append(f"CPU usage is critically high at {cpu}%.")
            analysis["recommendations"].append(
                "Consider closing resource-heavy applications or restarting."
            )
            analysis["severity"] = "critical" if cpu > 95 else "warning"

        if ram > _MEM_WARN:
            analysis["warnings"].append(f"Memory usage is high at {ram}%.")
            analysis["recommendations"].append(
                "Close unused applications to free up RAM."
            )
            if analysis["severity"] == "ok":
                analysis["severity"] = "warning"

        if disk > _DISK_WARN:
            analysis["warnings"].append(f"Disk usage is high at {disk}%.")
            analysis["recommendations"].append(
                "Clean up large or temporary files to reclaim disk space."
            )
            if analysis["severity"] == "ok":
                analysis["severity"] = "warning"

        batt = metrics.get("battery_percent")
        plugged = metrics.get("power_plugged")
        if batt is not None and batt < 20 and not plugged:
            analysis["warnings"].append(f"Battery is low at {batt}%. Not plugged in.")
            analysis["recommendations"].append("Plug in the charger soon.")

        # Store in context memory
        context_memory.update("system", metrics)

    # ── Network scan analysis ──
    elif tool_name == "automation_network_scan":
        scan_data = result.get("data", {})
        net_summary = _parse_network_results(scan_data)
        analysis["metrics"] = net_summary

        if net_summary["open_port_count"] > 10:
            analysis["warnings"].append(
                f"Found {net_summary['open_port_count']} open ports — review for unnecessary exposures."
            )
            analysis["severity"] = "warning"

        context_memory.update("network", net_summary)

    # ── Browser / IP analysis ──
    elif tool_name == "automation_get_ip":
        ip = result.get("ip", "unknown")
        analysis["metrics"] = {"public_ip": ip}
        context_memory.update("browser", {"ip": ip, "action": "ip_check"})

    elif tool_name == "automation_rotate_session":
        ip = result.get("current_ip", "unknown")
        analysis["metrics"] = {"current_ip": ip}
        context_memory.update("browser", {"ip": ip, "action": "session_rotation"})

    elif tool_name == "automation_inject_fingerprint":
        analysis["metrics"] = {"fingerprint_injected": True}
        context_memory.update("browser", {"action": "fingerprint_injection"})

    elif tool_name in ("browser_summarize", "browser_search"):
        # The summary text is in the original result's message
        summary = result.get("message", "")
        if summary:
            analysis["metrics"]["summary"] = summary

    return analysis


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  4. RESPONSE SYNTHESIS — Analyzed Data → Natural Language
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def synthesize_response(analyses: list[dict]) -> str:
    """
    Convert a list of analysis results into a single, concise,
    TTS-friendly natural-language response.
    """
    parts: list[str] = []

    for a in analyses:
        tool = a.get("tool", "")
        metrics = a.get("metrics", {})
        warnings = a.get("warnings", [])
        recommendations = a.get("recommendations", [])
        severity = a.get("severity", "ok")

        if severity == "error":
            parts.append(f"I couldn't complete the {_tool_display_name(tool)} check. {'; '.join(warnings)}")
            continue

        # ── System ──
        if tool in ("automation_system_info", "automation_system_analyze"):
            cpu = metrics.get("cpu_percent")
            ram = metrics.get("ram_percent")
            disk = metrics.get("disk_percent")
            batt = metrics.get("battery_percent")

            summary_bits = []
            if cpu is not None:
                summary_bits.append(f"CPU is at {cpu:.0f}%")
            if ram is not None:
                summary_bits.append(f"memory at {ram:.0f}%")
            if disk is not None:
                summary_bits.append(f"disk at {disk:.0f}%")
            if batt is not None:
                plugged = metrics.get("power_plugged", False)
                plug_text = "plugged in" if plugged else "on battery"
                summary_bits.append(f"battery at {batt:.0f}% {plug_text}")

            if summary_bits:
                parts.append("System status: " + ", ".join(summary_bits) + ".")

            if warnings:
                parts.append(" ".join(warnings))
            if recommendations:
                parts.append("Recommendation: " + " ".join(recommendations))

        # ── Network ──
        elif tool == "automation_network_scan":
            host_count = metrics.get("host_count", 0)
            port_count = metrics.get("open_port_count", 0)

            if host_count > 0:
                hosts = metrics.get("live_hosts", [])
                host_preview = ", ".join(hosts[:5])
                parts.append(
                    f"Network scan found {host_count} live host{'s' if host_count != 1 else ''}: {host_preview}."
                )
            else:
                parts.append("Network scan completed. No live hosts detected.")

            if port_count > 0:
                parts.append(f"Detected {port_count} open port{'s' if port_count != 1 else ''}.")

            if warnings:
                parts.append(" ".join(warnings))

        # ── IP ──
        elif tool == "automation_get_ip":
            ip = metrics.get("public_ip", "unknown")
            parts.append(f"Your current public IP address is {ip}.")

        elif tool == "automation_rotate_session":
            ip = metrics.get("current_ip", "unknown")
            parts.append(f"Session rotated. Your IP is now {ip}.")

        elif tool == "automation_inject_fingerprint":
            parts.append("Browser fingerprint has been randomized.")

        elif tool in ("browser_summarize", "browser_search"):
            summary = metrics.get("summary")
            if summary:
                parts.append(summary)

    if not parts:
        return "Task completed."

    return " ".join(parts)


def _tool_display_name(tool_name: str) -> str:
    """Human-readable name for a tool."""
    names = {
        "automation_system_info": "system",
        "automation_system_analyze": "system optimization",
        "automation_network_scan": "network",
        "automation_get_ip": "IP lookup",
        "automation_rotate_session": "session rotation",
        "automation_inject_fingerprint": "fingerprint injection",
    }
    return names.get(tool_name, tool_name)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  5. INTELLIGENT EXECUTION — Wraps execute_plan with analysis
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Tools that belong to the automation-engine (routed through intelligence layer)
AUTOMATION_TOOLS = {
    "automation_system_info",
    "automation_system_analyze",
    "automation_network_scan",
    "automation_get_ip",
    "automation_rotate_session",
    "automation_inject_fingerprint",
    "browser_get_page",
    "browser_click",
    "browser_type",
    "browser_summarize",
    "browser_search",
}


def is_automation_plan(plan: list[dict]) -> bool:
    """Check if any step in the plan uses an automation-engine tool."""
    return any(step.get("tool") in AUTOMATION_TOOLS for step in plan)


def execute_intelligent(plan: list[dict]) -> list[dict]:
    """
    Enhanced execution pipeline:
      1. Run tools via execute_plan()
      2. Analyze each result
      3. Store in ContextMemory
      4. Synthesize a natural-language response
      5. Return enriched results
    """
    raw_results = execute_plan(plan)

    analyses = []
    enriched_results = []

    for step, result in zip(plan, raw_results):
        tool_name = step.get("tool", "")

        if tool_name in AUTOMATION_TOOLS:
            # Pull the inner result dict for analysis
            inner = result.get("result", result)
            analysis = analyze_results(tool_name, inner)
            analyses.append(analysis)

            # Enrich the result with analysis metadata
            result["analysis"] = analysis
            result["severity"] = analysis["severity"]

        enriched_results.append(result)

    # Generate the synthesized natural-language response
    if analyses:
        natural_response = synthesize_response(analyses)
        # Attach to the last result so the agent can speak it
        if enriched_results:
            enriched_results[-1]["message"] = natural_response
            enriched_results[-1]["status"] = "success"

    return enriched_results
