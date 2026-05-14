"""
validate_raptor.py — System Health & Pipeline Diagnostic
Checks all RAPTOR subsystems: Mic, STT, TTS, Planner, Executor.
"""

import sys
import os
import time
import logging

# Add current dir to path if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.local_audio import speak, listen_and_transcribe, get_stt_model
from core.planner import plan_task
from core.executor import TOOL_REGISTRY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAPTOR-VALIDATE")

def run_checks():
    print("\n" + "="*50)
    print("  RAPTOR SYSTEM DIAGNOSTIC v1.0")
    print("="*50 + "\n")

    # 1. Environment Check
    print("[1/6] Environment Check...")
    if not os.path.exists(".env"):
        print("  ⚠️  .env file missing.")
    else:
        print("  ✔ .env found.")
    
    if not os.environ.get("GROQ_API_KEY"):
        print("  ⚠️  GROQ_API_KEY missing. LLM fallback will be disabled.")
    else:
        print("  ✔ GROQ_API_KEY detected.")

    # 2. TTS Check
    print("\n[2/6] TTS Audio Check...")
    try:
        print("  -> Attempting to speak 'Raptor Diagnostic Initialized'...")
        speak("Raptor Diagnostic Initialized.", blocking=True)
        print("  ✔ TTS completed successfully.")
    except Exception as e:
        print(f"  ✘ TTS FAILED: {e}")
        return False

    # 3. STT Model Check
    print("\n[3/6] STT Model Check...")
    try:
        get_stt_model()
        print("  ✔ faster-whisper model loaded and ready.")
    except Exception as e:
        print(f"  ✘ STT Model FAILED: {e}")
        return False

    # 4. Planner Check
    print("\n[4/6] Planner Intent Check...")
    test_phrase = "what is the weather in Delhi"
    plan = plan_task(test_phrase)
    if plan and plan[0]["tool"] == "get_weather":
        print(f"  ✔ Planner correctly routed '{test_phrase}' to get_weather.")
    else:
        print(f"  ✘ Planner FAILED to route intent. Plan was: {plan}")
        return False

    # 5. Tool Registry Check
    print("\n[5/6] Tool Registry Check...")
    required_tools = ["get_weather", "get_news", "set_timer", "read_emails", "send_whatsapp_message"]
    missing = [t for t in required_tools if t not in TOOL_REGISTRY]
    if not missing:
        print(f"  ✔ All critical tools found in registry ({len(TOOL_REGISTRY)} total).")
    else:
        print(f"  ✘ Missing tools: {missing}")
        return False

    # 6. Microphone Check (Optional/Prompted)
    if "--no-mic" in sys.argv:
        print("\n[6/6] Microphone Check skipped (headless mode).")
        print("\n" + "="*50)
        print("  DIAGNOSTIC COMPLETE: RAPTOR CORE READY 🚀")
        print("="*50 + "\n")
        return True

    print("\n[6/6] Microphone & STT Loop Check...")
    print("  -> Please say 'test raptor' now (10s timeout)...")
    try:
        transcription = listen_and_transcribe(timeout=10)
        print(f"  ✔ Received: '{transcription}'")
        if "raptor" in transcription.lower():
            print("  ✔ Voice pipeline fully verified.")
        else:
            print("  ⚠️  Transcription received but didn't contain 'raptor'. Check your mic.")
    except Exception as e:
        print(f"  ✘ Mic/STT FAILED: {e}")
        return False

    print("\n" + "="*50)
    print("  DIAGNOSTIC COMPLETE: RAPTOR IS FLIGHT READY 🚀")
    print("="*50 + "\n")
    return True

if __name__ == "__main__":
    success = run_checks()
    sys.exit(0 if success else 1)
