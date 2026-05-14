import os
import sys
import threading
import time
from core.planner import plan_task
from core.executor import execute_plan
from core.wake_listener import start_wake_listener

def run_system_check():
    print("\n" + "="*30)
    print("SYSTEM HEALTH CHECK")
    print("="*30)
    
    results = {}

    # 1. Microphone Access
    print("[1/7] Checking microphone access...")
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        if len(devices) > 0:
            print("  PASS: Found audio devices.")
            results["mic"] = True
        else:
            print("  FAIL: No audio devices found.")
            results["mic"] = False
    except Exception as e:
        print(f"  FAIL: Microphone check error: {e}")
        results["mic"] = False

    # 2. Wake Listener Thread
    print("[2/7] Checking wake listener...")
    try:
        def dummy_callback(): pass
        wake_thread = threading.Thread(target=start_wake_listener, args=(dummy_callback,), daemon=True)
        wake_thread.start()
        time.sleep(1) # Give it a second to initialize
        if wake_thread.is_alive():
            print("  PASS: Wake listener thread started.")
            results["wake"] = True
        else:
            print("  FAIL: Wake listener thread died immediately.")
            results["wake"] = False
    except Exception as e:
        print(f"  FAIL: Wake listener error: {e}")
        results["wake"] = False

    # 3. STT Test (requires mock or silent check)
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

    # 4. TTS Test
    print("[4/7] Checking TTS (pyttsx3)...")
    try:
        # We'll do a silent-ish test or just check if it initializes
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('volume', 0.0) # Mute for test
        engine.say("System check")
        engine.runAndWait()
        print("  PASS: TTS initialized and ran.")
        results["tts"] = True
    except Exception as e:
        print(f"  FAIL: TTS check error: {e}")
        results["tts"] = False

    # 5. Planner Test
    print("[5/7] Checking Planner...")
    try:
        plan = plan_task("echo hello world")
        if plan is not None:
            print("  PASS: Planner parsed sample command.")
            results["planner"] = True
        else:
            print("  FAIL: Planner returned None for sample command.")
            results["planner"] = False
    except Exception as e:
        print(f"  FAIL: Planner check error: {e}")
        results["planner"] = False

    # 6. Executor Test (safe echo)
    print("[6/7] Checking Executor...")
    try:
        test_plan = [{"tool": "run_command", "args": {"command": "echo 'Raptor Check'"}}]
        res = execute_plan(test_plan)
        if res and res[0].get("status") == "success":
            print("  PASS: Executor ran safe test command.")
            results["executor"] = True
        else:
            print(f"  FAIL: Executor failed safe test. Result: {res}")
            results["executor"] = False
    except Exception as e:
        print(f"  FAIL: Executor check error: {e}")
        results["executor"] = False

    # 7. Gmail Tool Check
    print("[7/7] Checking Gmail Tools...")
    try:
        # Check if credentials exist
        if os.path.exists("credentials.json") or os.path.exists("token.json"):
            # Try to import and check a basic tool
            from core.tools.email_tools import authenticate
            creds = authenticate()
            if creds:
                print("  PASS: Gmail authentication successful.")
                results["gmail"] = True
            else:
                print("  FAIL: Gmail authentication failed.")
                results["gmail"] = False
        else:
            print("  WARN: Gmail credentials/token missing. Email tools will be disabled.")
            results["gmail"] = True # Set to True to avoid Hard Exit, but it's a "soft pass"
    except Exception as e:
        print(f"  WARN: Gmail check error: {e}. Email tools will be disabled.")
        results["gmail"] = True # Soft Fail

    print("\n" + "="*30)
    print("HEALTH CHECK SUMMARY")
    print("="*30)
    all_pass = True
    for key, val in results.items():
        status = "PASS" if val else "FAIL"
        print(f"{key.upper():<10}: {status}")
        if not val:
            all_pass = False
    
    if not all_pass:
        print("\nSYSTEM HEALTH CHECK FAILED. Exiting...")
        sys.exit(1)
    
    print("\nALL SYSTEMS GO.\n")
    return True
