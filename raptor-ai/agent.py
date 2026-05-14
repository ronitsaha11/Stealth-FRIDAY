"""
Core – Voice Agent (Local Offline Mode)
=======================================
Fully local, non-LiveKit voice agent. Runs continuously on the host machine.
Listens for 'hey raptor', transcribes using faster-whisper, processes the command,
and speaks back using pyttsx3.

Interaction Flow:
  IDLE       → wait for wake word
  SPEAKING   → TTS active (interruptible)
  LISTENING  → capturing user input (continuous after first activation)
  PROCESSING → planning + executing
"""

import os
import sys
import re
import threading
import time
import webbrowser
import socket
import subprocess
import fcntl
from datetime import datetime
from dotenv import load_dotenv

from core.wake_listener import start_wake_listener
from core.local_audio import is_speaking, speak, stop_speaking, listen_and_transcribe
from core.planner import plan_task
from core.executor import execute_plan
from core.intelligence import is_automation_plan, execute_intelligent
from core.monitor import RaptorMonitor
from core.health_check import run_system_check
from core.ws_bridge import bridge as ws_bridge
from core.browser_bridge import browser_bridge

from groq import Groq

load_dotenv()

# Words that make the agent go back to sleep
EXIT_COMMANDS = ["stop", "exit", "sleep", "goodbye", "go to sleep", "shut up", "that's all"]

CONFIRMATION_TOOLS = {
    "send_whatsapp_message",
    "send_file_via_whatsapp",
    "read_emails",
    "read_last_emails",
    "summarize_emails",
    "search_emails",
    "read_latest_email",
    "open_email_in_browser",
    "read_context_email",
    "describe_context_email_sender",
    "describe_context_email_topic",
}
CONFIRMATION_WORDS = ["yes", "yeah", "confirm", "do it", "send it"]


class LocalVoiceAgent:
    def __init__(self):
        self.wake_event = threading.Event()
        self.client = Groq() if os.environ.get("GROQ_API_KEY") else None

        self.state = "IDLE"
        self.last_command = ""
        self.last_command_time = 0
        self.ui_launched = False

        # Proactive background monitoring daemon
        self.monitor = RaptorMonitor(agent=self)

    # ------------------------------------------------------------------ #
    #   State Management                                                    #
    # ------------------------------------------------------------------ #
    def set_state(self, new_state: str):
        if self.state != new_state:
            print(f"[STATE CHANGE] {self.state} → {new_state}")
            self.state = new_state
            ws_bridge.update_state({"state": new_state})

    # ------------------------------------------------------------------ #
    #   Wake Word Callback (fires from background thread)                   #
    # ------------------------------------------------------------------ #
    def on_wake_word_detected(self):
        if self.state != "IDLE":
            print(f"[WAKE] Ignoring trigger – System is currently {self.state}")
            return

        if self.state == "SPEAKING":
            stop_speaking()
        self.wake_event.set()

    # ------------------------------------------------------------------ #
    #   LLM Fallback                                                        #
    # ------------------------------------------------------------------ #
    def process_general_chat(self, user_string: str) -> str:
        if not self.client:
            return "I am currently disconnected from Groq. I cannot answer general questions."
        try:
            resp = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": (
                        "You are Raptor, a highly advanced and incredibly concise AI assistant. "
                        "Respond with short, direct answers under 30 words."
                    )},
                    {"role": "user", "content": user_string},
                ],
                model="llama-3.1-8b-instant",
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f"[GROQ ERROR] {e}")
            return "My neural network is encountering latency. Please try again."

    def _speak_response(self, text: str):
        self.set_state("SPEAKING")
        speak(text, blocking=False)

        while is_speaking():
            if self.wake_event.is_set():
                print("[PIPELINE] Speech interrupted by wake event.")
                stop_speaking()
                self.wake_event.clear()
                self.set_state("LISTENING")
                return
            time.sleep(0.05)

    def _confirmation_prompt_for_plan(self, plan: list) -> tuple[list, str] | tuple[None, str]:
        if not plan:
            return None, "There is nothing to confirm."

        sensitive_index = next(
            (index for index, step in enumerate(plan) if step.get("tool") in CONFIRMATION_TOOLS),
            None,
        )
        if sensitive_index is None:
            return plan, ""

        step = plan[sensitive_index]
        tool_name = step.get("tool")
        args = dict(step.get("args", {}))

        if tool_name == "send_whatsapp_message":
            contact = args.get("contact", "that contact")
            message = args.get("message", "")
            preview = f'You are about to send "{message}" to {contact} on WhatsApp. Are you sure?'
            print(f"[CONFIRM] Planned sensitive action: {preview}")
            return plan, preview

        if tool_name == "read_emails":
            limit = args.get("limit", 5)
            preview = f"You are about to read your latest {limit} email subjects. Are you sure?"
            print(f"[CONFIRM] Planned sensitive action: {preview}")
            return plan, preview

        if tool_name == "read_last_emails":
            preview = "You are about to read the emails from the last summary aloud. Are you sure?"
            print(f"[CONFIRM] Planned sensitive action: {preview}")
            return plan, preview

        if tool_name == "summarize_emails":
            preview = "You are about to summarize your recent emails. Are you sure?"
            print(f"[CONFIRM] Planned sensitive action: {preview}")
            return plan, preview

        if tool_name == "search_emails":
            query = args.get("query", "your email search")
            preview = f'You are about to search your emails for "{query}". Are you sure?'
            print(f"[CONFIRM] Planned sensitive action: {preview}")
            return plan, preview

        if tool_name == "read_latest_email":
            preview = "You are about to read your latest email aloud. Are you sure?"
            print(f"[CONFIRM] Planned sensitive action: {preview}")
            return plan, preview

        if tool_name == "open_email_in_browser":
            preview = "You are about to open an email in Gmail. Are you sure?"
            print(f"[CONFIRM] Planned sensitive action: {preview}")
            return plan, preview

        if tool_name == "read_context_email":
            preview = "You are about to read the current email in context aloud. Are you sure?"
            print(f"[CONFIRM] Planned sensitive action: {preview}")
            return plan, preview

        if tool_name == "describe_context_email_sender":
            preview = "You are about to reveal who sent the current email. Are you sure?"
            print(f"[CONFIRM] Planned sensitive action: {preview}")
            return plan, preview

        if tool_name == "describe_context_email_topic":
            preview = "You are about to describe what the current email is about. Are you sure?"
            print(f"[CONFIRM] Planned sensitive action: {preview}")
            return plan, preview

        if tool_name == "send_file_via_whatsapp":
            preparatory_steps = plan[:sensitive_index]
            if preparatory_steps:
                prep_results = execute_plan(preparatory_steps)
                prep_failure = next((result for result in prep_results if result.get("status") != "success"), None)
                if prep_failure:
                    message = prep_failure.get("message") or "I could not prepare that file send."
                    return None, message

                last_result = prep_results[-1].get("result")
                if not isinstance(last_result, dict) or not last_result.get("file_path"):
                    return None, "I could not resolve the file to send."
                resolved_path = last_result["file_path"]
            else:
                resolved_path = args.get("file_path", "")

            updated_plan = []
            for current_step in plan[sensitive_index:]:
                updated_step = {
                    "tool": current_step.get("tool"),
                    "args": dict(current_step.get("args", {})),
                }
                if updated_step["args"].get("file_path") == "$last_file_path":
                    updated_step["args"]["file_path"] = resolved_path
                updated_plan.append(updated_step)

            contact = args.get("contact", "that contact")
            preview = (
                f"You are about to send {os.path.basename(resolved_path)} "
                f"to {contact} on WhatsApp. Are you sure?"
            )
            print(f"[CONFIRM] Planned sensitive action: {preview}")
            return updated_plan, preview

        return plan, ""

    def _confirm_sensitive_action(self, plan: list) -> tuple[list | None, bool]:
        if not plan or not any(step.get("tool") in CONFIRMATION_TOOLS for step in plan):
            return plan, True

        prepared_plan, prompt = self._confirmation_prompt_for_plan(plan)
        if prepared_plan is None:
            self.set_state("SPEAKING")
            speak(prompt, blocking=True)
            return None, False

        self.set_state("SPEAKING")
        speak(prompt, blocking=True)
        self.set_state("LISTENING")
        try:
            confirmation = listen_and_transcribe(timeout=10).lower()
        except TimeoutError:
            print("[CONFIRM] Confirmation timed out.")
            self.set_state("SPEAKING")
            speak("No confirmation received. Action cancelled.", blocking=True)
            return None, False

        if any(word in confirmation for word in CONFIRMATION_WORDS):
            print("[CONFIRM] Confirmation granted.")
            return prepared_plan, True

        print("[CONFIRM] Confirmation denied.")
        self.set_state("SPEAKING")
        speak("Action cancelled.", blocking=True)
        return None, False

    # ------------------------------------------------------------------ #
    #   Single Interaction Turn                                             #
    # ------------------------------------------------------------------ #
    def _handle_turn(self, user_input: str) -> bool:
        """
        Process one user utterance. Returns True if agent should keep
        conversing, False if it should return to IDLE (sleep/exit/timeout).
        """
        user_input_lower = user_input.lower().strip()

        # Debounce: Prevent terminal spam / duplicate command execution
        current_time = time.time()
        if user_input_lower == self.last_command.lower() and (current_time - self.last_command_time) < 2.0:
            print(f"[PIPELINE] Ignoring duplicate command (debounce): {user_input}")
            return True

        # Check exit commands first
        if any(cmd in user_input_lower for cmd in EXIT_COMMANDS):
            self.set_state("SPEAKING")
            speak("Going to sleep. Say Hey Raptor when you need me.", blocking=True)
            return False  # Signal: return to IDLE

        # Context memory: resolve "it" / "that" to last executed thing
        if self.last_command and re.search(r"\bit\b|\bthat\b", user_input_lower):
            user_input_lower = re.sub(r"\bit\b|\bthat\b", self.last_command, user_input_lower)
            user_input = re.sub(r"\bit\b|\bthat\b", self.last_command, user_input, flags=re.IGNORECASE)

        print(f"[PIPELINE] USER INPUT: {user_input}")

        # ── Learning controls (before planner) ──
        try:
            from core.learning_controls import detect_learning_intent, execute_learning_command
            learning_intent = detect_learning_intent(user_input_lower)
            if learning_intent:
                self.set_state("PROCESSING")
                print(f"[PIPELINE] Learning control: {learning_intent['action']}")
                response = execute_learning_command(learning_intent)
                self._speak_response(response)
                ws_bridge.update_state({
                    "last_command": user_input,
                    "last_response": response,
                    "active_module": "learning",
                })
                self.last_command = user_input
                self.last_command_time = time.time()
                return True
        except ImportError:
            pass

        self.set_state("PROCESSING")
        plan = plan_task(user_input_lower)

        if plan and any(step.get("tool") in CONFIRMATION_TOOLS for step in plan):
            plan, confirmed = self._confirm_sensitive_action(plan)
            if not confirmed:
                return True
            self.set_state("PROCESSING")

        # --- Execute plan or fall back to LLM ---
        if plan:
            print(f"[PIPELINE] Plan: {plan}")
            
            # Determine active module
            first_tool = plan[0].get("tool", "")
            active_mod = "none"
            if "weather" in first_tool: active_mod = "weather"
            elif "world_monitor" in first_tool: active_mod = "world_monitor"
            elif "email" in first_tool: active_mod = "email"
            elif "cricket" in first_tool or "football" in first_tool: active_mod = "sports"
            elif "music" in first_tool: active_mod = "music"
            elif "stock" in first_tool: active_mod = "stock"
            elif "whatsapp" in first_tool: active_mod = "whatsapp"
            elif "automation" in first_tool: active_mod = "automation"
            elif "browser" in first_tool: active_mod = "browser"
            
            ws_bridge.update_state({"last_command": user_input, "active_module": active_mod})
            
            try:
                # Route automation-engine tools through the intelligence layer
                if is_automation_plan(plan):
                    print("[PIPELINE] Automation plan detected → intelligence layer")
                    results = execute_intelligent(plan)
                else:
                    results = execute_plan(plan)

                # Check for conversational follow-up (ask)
                ask_message = None
                ask_tool = None
                for step, result in zip(plan, results):
                    if result.get("status") == "ask":
                        ask_message = result.get("message")
                        ask_tool = step.get("tool")
                        break
                
                if ask_message and ask_tool:
                    self._speak_response(ask_message)
                    ws_bridge.update_state({"last_response": ask_message})
                    self.set_state("LISTENING")
                    try:
                        answer = listen_and_transcribe(timeout=10)
                        ws_bridge.update_state({"last_command": answer})
                        self.set_state("PROCESSING")
                        # Hardcoded play_music follow-up for now
                        if ask_tool == "play_music":
                            results = execute_plan([{"tool": "play_music", "args": {"query": answer}}])
                    except TimeoutError:
                        self._speak_response("I didn't hear a response, canceling.")
                        ws_bridge.update_state({"last_response": "I didn't hear a response, canceling."})
                        return True

                latest_success_message = None
                failure_message = None
                for result in results:
                    if result.get("status") == "success" and result.get("message"):
                        latest_success_message = result["message"]
                    elif result.get("status") != "success" and result.get("status") != "ask":
                        failure_message = result.get("message") or result.get("error")

                final_response = ""
                if failure_message:
                    final_response = failure_message
                    self._speak_response(failure_message)
                elif latest_success_message:
                    final_response = latest_success_message
                    self._speak_response(latest_success_message)
                elif all(result.get("status") in ["success", "ask"] for result in results) and not ask_tool:
                    final_response = "Done. Completed successfully."
                    self._speak_response(final_response)
                elif not ask_tool:
                    final_response = "I encountered an issue completing that task."
                    self._speak_response(final_response)
                    
                if final_response:
                    ws_bridge.update_state({"last_response": final_response})

                last_args = plan[-1].get("args", {})
                self.last_command = (
                    last_args.get("command")
                    or last_args.get("path")
                    or last_args.get("app_name")
                    or last_args.get("file_path")
                    or "that"
                )
                self.last_command_time = time.time()

            except Exception as e:
                print(f"[ERROR] Execute plan fault: {e}")
                self._speak_response("Something went wrong.")
        else:
            # No tools matched → LLM
            print("[PIPELINE] No tools matched. Routing to Groq...")
            ws_bridge.update_state({"last_command": user_input, "active_module": "none"})
            response = self.process_general_chat(user_input)
            self._speak_response(response)
            ws_bridge.update_state({"last_response": response})
            self.last_command = ""

        return True  # Stay awake

    def _launch_ui(self):
        """Launches the local interactive UI. Checks if server is running first."""
        if self.ui_launched:
            return
        
        def is_port_in_use(port):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(('localhost', port)) == 0

        if not is_port_in_use(3000):
            print("[SYSTEM] No frontend detected on port 3000. Attempting launch...")
            try:
                # Try to launch actual frontend if script exists
                # Workspace Root/frontend/launch_frontend.sh
                root_dir = os.path.dirname(os.path.abspath(__file__))
                frontend_script = os.path.join(os.path.dirname(root_dir), "frontend", "launch_frontend.sh")
                
                if os.path.exists(frontend_script):
                    subprocess.Popen(["bash", frontend_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    # Fallback to python server
                    subprocess.Popen(["python3", "-m", "http.server", "3000"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                time.sleep(2) # Give server a moment to bind
            except Exception as e:
                print(f"[SYSTEM] Could not auto-start frontend: {e}")

        # Removed webbrowser.open("http://localhost:3000") to avoid duplicate tabs
        # The frontend will be launched by launch_frontend.sh independently if closed
        self.ui_launched = True

    # ------------------------------------------------------------------ #
    #   Main Loop                                                           #
    # ------------------------------------------------------------------ #
    def run(self):
        # 0. Singleton Lock Check
        lock_file_path = "/tmp/raptor_agent.lock"
        self._lock_file = open(lock_file_path, 'w')
        try:
            fcntl.lockf(self._lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._lock_file.write(str(os.getpid()))
            self._lock_file.flush()
        except IOError:
            print("[CRITICAL] Another instance of Raptor Agent is already running. Exiting.")
            sys.exit(1)

        # 1. Run System Health Check
        run_system_check()

        print("==" * 30)
        print("RAPTOR CORE – LOCAL OFFLINE PIPELINE INITIALIZED")
        print("==" * 30)

        # 2. Start WebSocket Bridge
        ws_bridge.start()

        # 3. Start Browser Intelligence Bridge
        browser_bridge.start()

        # Start passive wake word listener in daemon thread
        wake_thread = threading.Thread(
            target=start_wake_listener,
            args=(self.on_wake_word_detected,),
            daemon=True,
        )
        wake_thread.start()

        # Start proactive background monitoring daemon
        self.monitor.start()

        self.set_state("SPEAKING")
        speak("Raptor local systems online. Waiting for wake word.", blocking=True)
        self.set_state("IDLE")

        while True:
            # ── IDLE: wait for wake word ──────────────────────────────
            self.set_state("IDLE")
            print("\n[PIPELINE] Passive listening for wake word...")
            self.wake_event.wait()
            self.wake_event.clear()

            print("\n[PIPELINE] Wake word triggered!")
            
            # UI Launch on Wake
            self._launch_ui()

            self.set_state("SPEAKING")
            speak("Raptor online. What can I do for you?", blocking=True)
            self.wake_event.clear()  # Discard any echo triggers

            # ── CONTINUOUS CONVERSATION LOOP ──────────────────────────
            while True:
                self.set_state("LISTENING")

                try:
                    user_input = listen_and_transcribe(timeout=15)
                except TimeoutError:
                    print("[PIPELINE] 15-second silence timeout. Returning to IDLE.")
                    self.set_state("SPEAKING")
                    speak("I'll be here when you need me.", blocking=True)
                    break  # Exit inner loop → back to IDLE / wake word

                if not user_input or not user_input.strip():
                    print("[PIPELINE] Empty transcription. Listening again...")
                    continue  # Stay in conversation loop, try again

                # Process the turn; break out if agent should sleep
                stay_awake = self._handle_turn(user_input)
                if not stay_awake:
                    break  # Go back to outer IDLE loop

                print("\n[PIPELINE] Turn complete. Still listening...\n")
                time.sleep(0.3)  # Brief pause before next listen to avoid echo
                self.wake_event.clear()


def _re_patch():
    pass  # re is imported at module level


if __name__ == "__main__":
    agent = LocalVoiceAgent()
    try:
        agent.run()
    except KeyboardInterrupt:
        stop_speaking()
        print("\nRAPTOR systems shutting down.")
