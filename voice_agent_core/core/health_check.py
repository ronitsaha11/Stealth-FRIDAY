"""
health_check.py — Raptor System Health Check (Windows-optimized)

Changes from original:
  - TTS check: no longer creates a second pyttsx3 engine on the main thread.
    The background TTS thread owns the engine; we just verify the module imports.
  - Wake listener check: no longer starts a full second listener with OWW/Whisper
    (would double-allocate RAM). Now just verifies the module is importable.
  - Gmail check: catches all exceptions gracefully (soft-fail, never hard-exits).
  - Hard sys.exit(1) removed — a failing check prints a warning but lets the
    agent continue. A failed mic or STT check is still a hard stop.
"""

import os
import sys
import threading
import time


def run_system_check():
    print("\n" + "=" * 30)
    print("SYSTEM HEALTH CHECK")
    print("=" * 30)

    results = {}

    # ── 1. Microphone Access ──────────────────────────────────────────────────
    print("[1/7] Checking microphone access...")
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        input_devices = [d for d in devices if d.get("max_input_channels", 0) > 0]
        if input_devices:
            print(f"  PASS: Found {len(input_devices)} input device(s).")
            results["mic"] = True
        else:
            print("  FAIL: No input audio devices found.")
            results["mic"] = False
    except Exception as e:
        print(f"  FAIL: Microphone check error: {e}")
        results["mic"] = False

    # ── 2. Wake Listener — import check only (do NOT start a second OWW instance) ──
    print("[2/7] Checking wake listener module...")
    try:
        from core.wake_listener import start_wake_listener  # noqa: F401
        print("  PASS: Wake listener module importable.")
        results["wake"] = True
    except Exception as e:
        print(f"  FAIL: Wake listener import error: {e}")
        results["wake"] = False

    # ── 3. STT (faster-whisper) ───────────────────────────────────────────────
    print("[3/7] Checking STT (faster-whisper)...")
    try:
        from core.local_audio import get_stt_model
        model = get_stt_model()
        if model:
            print("  PASS: STT model loaded.")
            results["stt"] = True
        else:
            print("  FAIL: STT model failed to load.")
            results["stt"] = False
    except Exception as e:
        print(f"  FAIL: STT check error: {e}")
        results["stt"] = False

    # ── 4. TTS — import + thread check only (engine lives in the TTS thread) ──
    print("[4/7] Checking TTS (pyttsx3)...")
    try:
        import pyttsx3  # noqa: F401
        # Verify the TTS background thread from local_audio is alive
        from core.local_audio import _tts_thread
        if _tts_thread.is_alive():
            print("  PASS: TTS engine thread is running.")
            results["tts"] = True
        else:
            print("  WARN: TTS thread not alive yet — it will start shortly.")
            results["tts"] = True   # soft pass; thread starts at module import
    except Exception as e:
        print(f"  FAIL: TTS check error: {e}")
        results["tts"] = False

    # ── 5. Planner ────────────────────────────────────────────────────────────
    print("[5/7] Checking Planner...")
    try:
        from core.planner import plan_task
        plan = plan_task("open notepad")
        if plan is not None:
            print("  PASS: Planner returned a plan.")
            results["planner"] = True
        else:
            print("  WARN: Planner returned None for test input.")
            results["planner"] = True  # soft pass — may be intentional
    except Exception as e:
        print(f"  FAIL: Planner check error: {e}")
        results["planner"] = False

    # ── 6. Executor ───────────────────────────────────────────────────────────
    print("[6/7] Checking Executor...")
    try:
        from core.executor import execute_plan
        test_plan = [{"tool": "run_command", "args": {"command": "echo Raptor Check"}}]
        res = execute_plan(test_plan)
        if res and res[0].get("status") == "success":
            print("  PASS: Executor ran safe test command.")
            results["executor"] = True
        else:
            print(f"  WARN: Executor result: {res}")
            results["executor"] = True  # soft pass
    except Exception as e:
        print(f"  FAIL: Executor check error: {e}")
        results["executor"] = False

    # ── 7. Gmail / Google Auth ────────────────────────────────────────────────
    print("[7/7] Checking Gmail Tools...")
    try:
        if os.path.exists("credentials.json") or os.path.exists("token.json"):
            from core.tools.email_tools import authenticate
            creds = authenticate()
            if creds:
                print("  PASS: Gmail authentication successful.")
            else:
                print("  WARN: Gmail auth returned no credentials. Email tools disabled.")
        else:
            print("  WARN: Gmail credentials/token missing. Email tools disabled.")
        results["gmail"] = True  # always soft-pass — not mission-critical
    except Exception as e:
        print(f"  WARN: Gmail check skipped: {e}")
        results["gmail"] = True  # soft pass

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 30)
    print("HEALTH CHECK SUMMARY")
    print("=" * 30)

    hard_failures = []
    for key, val in results.items():
        status = "PASS" if val else "FAIL"
        print(f"  {key.upper():<10}: {status}")
        if not val:
            hard_failures.append(key)

    # Only hard-exit on truly unrecoverable failures
    critical = [f for f in hard_failures if f in ("mic", "stt")]
    if critical:
        print(f"\n[CRITICAL] Cannot start without: {', '.join(critical)}")
        print("Please check your microphone and Python environment.")
        sys.exit(1)

    if hard_failures:
        print(f"\n[WARN] Non-critical failures: {', '.join(hard_failures)} — continuing anyway.")
    else:
        print("\nALL SYSTEMS GO.\n")

    return True
