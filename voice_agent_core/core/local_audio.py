"""
local_audio.py — TTS + STT for Raptor (Windows-optimized)

TTS Strategy:
  Primary:  Direct Windows SAPI via win32com.client.Dispatch("SAPI.SpVoice")
            - Most reliable on Windows — no pyttsx3 engine state corruption
            - win32com creates a fresh COM object per speak, no stale state
  Fallback: pyttsx3 (if pywin32 not available)

Root cause of the "speaks on startup but not after wake word" bug:
  pyttsx3 wraps SAPI5 but its engine object becomes unreliable after the
  first runAndWait() + stop() cycle within a background thread. Each new
  pyttsx3.init() call in subsequent speak() calls was silently failing.
  win32com.client.Dispatch creates a fresh SAPI object every call — no state.

STT:
  WhisperModel lazy singleton, shared with wake_listener (no double load).
  Noise gate at 0.015 RMS to filter background noise.
"""

import queue
import threading
import time
import numpy as np

# ── STT Model (lazy singleton — loaded once, shared with wake_listener) ───────
_stt_model = None
_stt_model_lock = threading.Lock()


def get_stt_model():
    """Return the shared WhisperModel, loading it on first call."""
    global _stt_model
    if _stt_model is None:
        with _stt_model_lock:
            if _stt_model is None:
                print("[SYSTEM] Loading faster-whisper model (first boot, please wait)...")
                from faster_whisper import WhisperModel
                _stt_model = WhisperModel(
                    "tiny.en",
                    device="cpu",
                    compute_type="int8",
                    num_workers=1,
                    cpu_threads=2,
                )
                print("[SYSTEM] Whisper model loaded.")
    return _stt_model


# ── TTS Engine — single persistent thread + queue ─────────────────────────────
_tts_queue: queue.Queue = queue.Queue()
_tts_speaking = threading.Event()
_tts_skip = threading.Event()


def _say_via_sapi(text: str):
    """
    Speak using direct Windows SAPI (win32com).
    Creates a fresh SpVoice COM object every call — immune to state corruption.
    """
    import pythoncom
    import win32com.client
    pythoncom.CoInitialize()
    try:
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        speaker.Rate = -2       # Slightly slower speech rate
        speaker.Volume = 100    # Full volume
        speaker.Speak(text)     # Synchronous — blocks until done
    finally:
        pythoncom.CoUninitialize()


def _say_via_pyttsx3(text: str):
    """Fallback TTS using pyttsx3 (if pywin32 not available)."""
    import pyttsx3
    engine = pyttsx3.init()
    engine.setProperty("rate", 165)
    engine.setProperty("volume", 1.0)
    engine.say(text)
    engine.runAndWait()
    engine.stop()


def _tts_worker():
    """
    Long-lived TTS background thread.
    Picks items from _tts_queue and speaks them one at a time.
    """
    # Detect which TTS backend to use (done once at thread start)
    try:
        import pythoncom  # noqa
        import win32com.client  # noqa
        use_sapi = True
        print("[TTS] Using direct Windows SAPI (win32com) for TTS.")
    except ImportError:
        use_sapi = False
        print("[TTS] win32com unavailable — falling back to pyttsx3.")

    while True:
        try:
            text = _tts_queue.get(timeout=1.0)
        except queue.Empty:
            continue

        if text is None:    # sentinel — shut down
            break

        _tts_skip.clear()
        _tts_speaking.set()
        try:
            if use_sapi:
                _say_via_sapi(text)
            else:
                _say_via_pyttsx3(text)
        except Exception as exc:
            print(f"[TTS WARNING] Speech failed: {exc}")
        finally:
            _tts_speaking.clear()
            _tts_queue.task_done()


# Start TTS thread once at module import
_tts_thread = threading.Thread(target=_tts_worker, daemon=True, name="RaptorTTS")
_tts_thread.start()


# ── Public TTS API ────────────────────────────────────────────────────────────

def is_speaking() -> bool:
    return _tts_speaking.is_set()


def speak(text: str, blocking: bool = True):
    """Queue text for TTS. If blocking=True waits until speech finishes."""
    stop_speaking()
    print(f"[RAPTOR] {text}")
    _tts_queue.put(text)

    if blocking:
        # Wait up to 3 s for TTS to START (fixes race condition)
        deadline = time.time() + 3.0
        while not _tts_speaking.is_set() and time.time() < deadline:
            time.sleep(0.02)
        # Wait for TTS to FINISH
        while _tts_speaking.is_set() and not _tts_skip.is_set():
            time.sleep(0.05)


def stop_speaking():
    """Interrupt current speech immediately."""
    if _tts_speaking.is_set():
        print("[SYSTEM] Interrupting TTS output...")
        _tts_skip.set()
        # Drain pending queue items
        while not _tts_queue.empty():
            try:
                _tts_queue.get_nowait()
                _tts_queue.task_done()
            except queue.Empty:
                break
        # Wait for speaking flag to clear (max 1 s)
        for _ in range(20):
            if not _tts_speaking.is_set():
                break
            time.sleep(0.05)


# ── STT — Listen + Transcribe ─────────────────────────────────────────────────

def listen_and_transcribe(timeout: int = 15) -> str:
    """
    Record audio until 1 s of trailing silence, then transcribe.
    Raises TimeoutError if no speech detected within `timeout` seconds.
    """
    import sounddevice as sd

    sample_rate = 16000
    block_duration = 0.1
    threshold = 0.015           # RMS gate — filters typical laptop background noise
    max_speech_duration = 10.0

    audio_buffer = []
    silence_time = 0.0
    has_spoken = False
    speech_start_time = None
    start_time = time.time()

    try:
        with sd.InputStream(samplerate=sample_rate, channels=1, dtype="float32") as stream:
            print("[AUDIO] Listening...")
            while True:
                if not has_spoken and (time.time() - start_time) > timeout:
                    raise TimeoutError("Silence timeout reached.")

                if has_spoken and speech_start_time and \
                        (time.time() - speech_start_time) > max_speech_duration:
                    print("[AUDIO] Max speech duration hit — forcing cutoff.")
                    break

                chunk, _ = stream.read(int(sample_rate * block_duration))
                rms = float(np.sqrt(np.mean(chunk ** 2)))

                if rms > threshold:
                    if not has_spoken:
                        print(f"[AUDIO] Speech detected (RMS={rms:.4f})")
                        speech_start_time = time.time()
                    has_spoken = True
                    silence_time = 0.0
                    audio_buffer.append(chunk)
                elif has_spoken:
                    silence_time += block_duration
                    audio_buffer.append(chunk)
                    if silence_time >= 1.0:
                        print("[AUDIO] 1 s silence → transcribing.")
                        break

    except TimeoutError:
        raise
    except Exception as e:
        print(f"[ERROR] STT capture failed: {e}")
        return ""

    if not audio_buffer:
        return ""

    print("[RAPTOR] Processing audio...")
    raw_data = np.concatenate(audio_buffer).flatten()

    try:
        segments, _ = get_stt_model().transcribe(
            raw_data, beam_size=1, language="en", condition_on_previous_text=False
        )
        return " ".join(seg.text for seg in segments).strip()
    except Exception as e:
        print(f"[ERROR] Whisper transcription failed: {e}")
        return ""
