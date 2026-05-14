#!/usr/bin/env python3
"""
Raptor Watchdog Launcher
========================
Monitors the Raptor Agent and relaunches it in Terminal if it dies.

Fixes applied:
  1. Watchdog singleton lock — prevents duplicate launcher instances
  2. Terminal tab reuse — reuses existing Raptor tab instead of opening new ones
  3. Post-launch grace period — waits after spawning before re-checking
"""

import os
import sys
import subprocess
import time
import logging
import fcntl

# Configuration
PROJECT_DIR = "/Users/soumyadebtripathy/Stealth F.R.I.D.A.Y/voice_agent_core"
AGENT_SCRIPT = "agent.py"
PYTHON_BIN = "./.venv/bin/python"
CHECK_INTERVAL = 30          # seconds between health checks
POST_LAUNCH_GRACE = 45       # seconds to wait after launching before re-checking
LOCK_FILE_AGENT = "/tmp/raptor_agent.lock"
LOCK_FILE_LAUNCHER = "/tmp/raptor_launcher.lock"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [LAUNCHER] %(levelname)s: %(message)s',
    filename=os.path.join(PROJECT_DIR, "raptor_launcher.log")
)


def acquire_launcher_lock():
    """Ensure only one watchdog launcher instance runs at a time."""
    lock_fd = open(LOCK_FILE_LAUNCHER, 'w')
    try:
        fcntl.lockf(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_fd.write(str(os.getpid()))
        lock_fd.flush()
        logging.info(f"Watchdog lock acquired (PID {os.getpid()}).")
        return lock_fd  # Must keep reference alive to hold the lock
    except IOError:
        logging.error("Another Raptor Launcher is already running. Exiting.")
        sys.exit(1)


def is_agent_running():
    """Check if agent.py holds its lock file (reliable cross-process check)."""
    if not os.path.exists(LOCK_FILE_AGENT):
        return False

    try:
        with open(LOCK_FILE_AGENT, 'a') as f:
            try:
                fcntl.lockf(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                # We got the lock → agent does NOT hold it
                fcntl.lockf(f, fcntl.LOCK_UN)
                return False
            except IOError:
                # Lock is held by the agent
                return True
    except Exception as e:
        logging.error(f"Lock file check failed: {e}")
        # Fallback: check process table
        try:
            subprocess.check_output(["pgrep", "-f", AGENT_SCRIPT])
            return True
        except Exception:
            return False


def _has_raptor_terminal_tab():
    """Check if a Terminal tab running the Raptor agent already exists."""
    check_script = '''
tell application "System Events"
    if not (exists process "Terminal") then return "NO_TERMINAL"
end tell
tell application "Terminal"
    repeat with w in windows
        repeat with t in tabs of w
            set tabProcs to processes of t
            if tabProcs contains "Python" then
                -- Check if any custom title or history contains our agent
                set tabHistory to history of t
                if tabHistory contains "agent.py" then
                    return "FOUND"
                end if
            end if
        end repeat
    end repeat
end tell
return "NOT_FOUND"
'''
    try:
        result = subprocess.run(
            ["osascript", "-e", check_script],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout.strip()
        return output == "FOUND"
    except Exception as e:
        logging.warning(f"Terminal tab check failed: {e}")
        return False


def launch_agent_in_terminal():
    """Launch the agent in Terminal, reusing an existing Raptor tab if possible."""
    logging.info("Triggering Terminal launch for Raptor Agent...")

    cmd = f'cd "{PROJECT_DIR}" && PYTHONUNBUFFERED=1 {PYTHON_BIN} {AGENT_SCRIPT} | tee raptor_agent.log'
    escaped_cmd = cmd.replace('"', '\\"')

    # AppleScript that reuses the frontmost Terminal window instead of creating new ones.
    # Uses `do script ... in front window` so it goes into the EXISTING window/tab.
    applescript = f'''
tell application "Terminal"
    activate
    if (count of windows) > 0 then
        -- Reuse the front window by creating a tab in it
        tell application "System Events" to tell process "Terminal" to keystroke "t" using command down
        delay 0.3
        do script "{escaped_cmd}" in front window
    else
        -- No windows open, create a fresh one
        do script "{escaped_cmd}"
    end if
end tell
'''

    try:
        result = subprocess.run(
            ["osascript", "-e", applescript],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            logging.info("Terminal launch succeeded.")
        else:
            logging.error(f"AppleScript error: {result.stderr.strip()}")
    except subprocess.TimeoutExpired:
        logging.error("AppleScript timed out.")
    except subprocess.CalledProcessError as e:
        logging.error(f"AppleScript failed: {e}")


def main():
    # ── Singleton: only one launcher at a time ──
    _lock = acquire_launcher_lock()  # noqa: F841 — must keep reference

    logging.info("Raptor Watchdog Launcher started.")

    while True:
        try:
            if is_agent_running():
                logging.debug("Raptor Agent is active.")
                time.sleep(CHECK_INTERVAL)
                continue

            # Agent is NOT running — but is there already a Terminal tab for it?
            if _has_raptor_terminal_tab():
                logging.info(
                    "Agent lock not held but a Raptor Terminal tab exists. "
                    "Waiting for it to initialize..."
                )
                time.sleep(CHECK_INTERVAL)
                continue

            logging.warning("Raptor Agent is not running. Initiating launch...")
            launch_agent_in_terminal()

            # Grace period: give the agent time to boot and acquire its lock
            logging.info(f"Post-launch grace period: {POST_LAUNCH_GRACE}s")
            time.sleep(POST_LAUNCH_GRACE)

        except Exception as e:
            logging.error(f"Main loop error: {e}")
            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
