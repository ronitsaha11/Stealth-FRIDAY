"""
wake_listener.py - Wake word detector for Raptor (Windows-optimized).

Key changes vs macOS version:
  - Whisper model is SHARED from local_audio.get_stt_model() — no second model load.
  - A threading.Semaphore caps concurrent Whisper inference threads to 1 so they
    never pile up and saturate all CPU cores.
  - OpenWakeWord (OWW) is still the primary detector; Whisper is a lightweight fallback.
  - Model loading is deferred until start_wake_listener() is called (not at import).
"""

import logging
import threading
import time

import numpy as np
import sounddevice as sd

logger = logging.getLogger("core-wake")
logger.setLevel(logging.INFO)

SAMPLE_RATE = 16000
CHUNK_SIZE = 1280          # ~80 ms per callback
OWW_THRESHOLD = 0.20       # Lowered from 0.35 → catches more valid detections
COOLDOWN_SECONDS = 2.5     # Reduced from 4.0s → allows quicker re-triggering

WHISPER_WINDOW_SEC = 3.5   # Wider window from 2.5s → captures full phrase reliably
WHISPER_KEYWORDS = {
    # Primary wake words
    "hey jarvis",
    "jarvis",
    "hey raptor",
    # Phonetic near-misses Whisper commonly transcribes
    "hey jarvice",
    "hey jarvus",
    "hey jarves",
    "hey travis",   # common Whisper mishear
    "hey rafter",
    "hey rapper",
    "hey wrapper",
    "hey rapta",
    # Single-word catches
    "jarvice",
    "jarves",
}
WHISPER_RMS_GATE = 0.005   # Lowered from 0.01 → catches quieter/distant speech

# Only 1 Whisper inference at a time — prevents CPU saturation from stacked threads
_whisper_semaphore = threading.Semaphore(1)


def _load_oww_model():
    """Load OpenWakeWord's built-in Hey Jarvis model."""
    try:
        from openwakeword.model import Model
        model = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
        logger.info("[WAKE] OpenWakeWord model loaded: hey_jarvis.")
        return model
    except Exception as e:
        logger.warning(f"[WAKE] OpenWakeWord unavailable: {e}.")
        return None


def start_wake_listener(activation_callback):
    """
    Start the wake-word listener.
    Blocks the calling thread — run it in a daemon thread from agent.py.

    Model loading strategy (Windows-friendly):
      - OWW loads its own small ONNX model (~10 MB, fast).
      - Whisper is obtained from local_audio.get_stt_model() which caches it
        globally — so we NEVER load a second copy of the Whisper model.
    """
    oww_model = _load_oww_model()

    # Reuse the shared Whisper model from local_audio — avoids loading a 2nd copy
    # which would cost ~300-400 MB extra RAM.
    try:
        from core.local_audio import get_stt_model
        whisper_model = get_stt_model()
        logger.info("[WAKE] Whisper wake model: shared from local_audio (no extra RAM).")
    except Exception as e:
        logger.warning(f"[WAKE] Could not get shared Whisper model: {e}")
        whisper_model = None

    if oww_model is None and whisper_model is None:
        logger.error("[WAKE] No wake word engine available. Listener disabled.")
        return

    last_trigger_time = 0.0
    trigger_lock = threading.Lock()
    whisper_buffer = []
    whisper_buffer_size = int(SAMPLE_RATE * WHISPER_WINDOW_SEC)

    def _fire_activation(source: str, score: float):
        nonlocal last_trigger_time
        with trigger_lock:
            now = time.time()
            if now - last_trigger_time < COOLDOWN_SECONDS:
                return
            last_trigger_time = now

        logger.info(f"[WAKE] *** RAPTOR ACTIVATED via {source} (score={score:.2f}) ***")
        activation_callback()

    def _whisper_check(audio_chunk_int16: np.ndarray):
        """Run Whisper on a short window — guarded by semaphore (max 1 concurrent)."""
        if whisper_model is None:
            return

        rms = np.sqrt(np.mean(audio_chunk_int16.astype(np.float32) ** 2)) / 32768.0
        if rms < WHISPER_RMS_GATE:
            return

        # Non-blocking acquire — if a Whisper thread is already running, skip this window
        if not _whisper_semaphore.acquire(blocking=False):
            logger.debug("[WAKE-STT] Skipping window — previous inference still running.")
            return

        try:
            audio_float = audio_chunk_int16.astype(np.float32) / 32768.0
            segments, _ = whisper_model.transcribe(
                audio_float,
                beam_size=1,
                language="en",
                condition_on_previous_text=False,
            )
            transcript = " ".join(seg.text.lower().strip() for seg in segments)
            if transcript:
                logger.debug(f"[WAKE-STT] '{transcript}'")
            if any(keyword in transcript for keyword in WHISPER_KEYWORDS):
                logger.info(f"[WAKE-STT] Keyword matched: '{transcript}'")
                _fire_activation("whisper", 1.0)
        except Exception as e:
            logger.debug(f"[WAKE-STT] Transcription error: {e}")
        finally:
            _whisper_semaphore.release()

    def audio_callback(indata, frames, time_info, status):
        nonlocal whisper_buffer

        pcm_int16 = indata[:, 0].copy()

        # ── Primary: OpenWakeWord (very fast, ONNX, ~1 ms per chunk) ──
        if oww_model is not None:
            try:
                prediction = oww_model.predict(pcm_int16)
                detect_score = prediction.get("hey_jarvis", 0)

                if detect_score > 0.1:
                    logger.debug(f"[WAKE-OWW] confidence={detect_score:.2f}")

                if detect_score > OWW_THRESHOLD:
                    _fire_activation("hey_jarvis", detect_score)
                    whisper_buffer.clear()   # discard buffer after trigger
                    return
            except Exception as e:
                logger.debug(f"[WAKE-OWW] predict error: {e}")

        # ── Fallback: Whisper keyword spotting ──
        if whisper_model is None:
            return

        whisper_buffer.append(pcm_int16)
        buffered = sum(len(c) for c in whisper_buffer)

        if buffered >= whisper_buffer_size:
            chunk = np.concatenate(whisper_buffer)
            whisper_buffer.clear()
            # Spawn a thread only if the semaphore slot is free — otherwise drop
            t = threading.Thread(target=_whisper_check, args=(chunk,), daemon=True)
            t.start()

    logger.info("[WAKE] Listening for 'Hey Jarvis' or 'Hey Raptor'...")

    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=CHUNK_SIZE,
            callback=audio_callback,
        ):
            while True:
                time.sleep(1)
    except Exception as e:
        logger.error(f"[WAKE] Microphone stream failed: {e}")
