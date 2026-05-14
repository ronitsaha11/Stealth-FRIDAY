import multiprocessing
import pyttsx3
import numpy as np
from faster_whisper import WhisperModel

# Initialize TTS
engine = pyttsx3.init()
engine.setProperty('rate', 170) 

# Lazy loaded STT Model
_model = None

def get_stt_model():
    global _model
    if _model is None:
        print("[SYSTEM] Loading faster-whisper model (this may take a moment on first boot)...")
        _model = WhisperModel("tiny.en", device="cpu", compute_type="int8") # Use float32 on MacOS, or int8
        print("[SYSTEM] Model loaded successfully.")
    return _model


def _speak_worker(text: str):
    import pyttsx3
    """Isolated process worker for TTS ensuring clean OS execution without blocking main thread GUI loops."""
    engine = pyttsx3.init()
    engine.setProperty('rate', 170)
    engine.say(text)
    engine.runAndWait()

# Global reference to current speaking process
_current_speaker_proc = None

def is_speaking() -> bool:
    global _current_speaker_proc
    return _current_speaker_proc is not None and _current_speaker_proc.is_alive()

def speak(text: str, blocking: bool = True):
    """Fallback-free OS native speech. Spawned in a process for killability."""
    global _current_speaker_proc
    
    stop_speaking()  # assure any previous speech finishes/terminates
    
    print(f"[RAPTOR] {text}")
    _current_speaker_proc = multiprocessing.Process(target=_speak_worker, args=(text,))
    _current_speaker_proc.daemon = True
    _current_speaker_proc.start()
    
    if blocking:
        _current_speaker_proc.join()

def stop_speaking():
    """Immediately halts the OS TTS execution cleanly."""
    global _current_speaker_proc
    if _current_speaker_proc is not None and _current_speaker_proc.is_alive():
        print("[SYSTEM] Interrupting TTS output...")
        _current_speaker_proc.terminate()
        _current_speaker_proc.join()
        _current_speaker_proc = None

def listen_and_transcribe(timeout: int = 15) -> str:
    """Listens until 1 sec of silence is detected, then transcribes using faster-whisper natively with sounddevice."""
    import sounddevice as sd
    import time
    
    sample_rate = 16000
    block_duration = 0.1  # 100ms chunks
    threshold = 0.007     # RMS energy threshold for speech (silence was ~0.00002)
    
    audio_buffer = []
    silence_time = 0.0
    has_spoken = False
    start_time = time.time()
    
    try:
        with sd.InputStream(samplerate=sample_rate, channels=1, dtype='float32') as stream:
            print("[AUDIO DEBUG] Starting listening loop...")
            speech_start_time = None
            max_speech_duration = 10.0  # Force cut-off after 10 seconds of continuous speech/noise
            
            while True:
                # Check timeout before speech starts
                if not has_spoken and (time.time() - start_time) > timeout:
                    print("[AUDIO DEBUG] Timeout reached without speech.")
                    raise TimeoutError("Silence timeout reached.")
                    
                # Force cutoff if speech is going on for too long (prevents infinite loop from background noise)
                if has_spoken and speech_start_time and (time.time() - speech_start_time) > max_speech_duration:
                    print("[AUDIO DEBUG] Max speech duration reached. Forcing cutoff.")
                    break
                    
                # Read 100ms chunk
                chunk, overflowed = stream.read(int(sample_rate * block_duration))
                
                # Calculate energy (Root Mean Square)
                rms = np.sqrt(np.mean(chunk**2))
                
                if rms > threshold:
                    if not has_spoken:
                        print(f"[AUDIO DEBUG] Speech DETECTED! (RMS: {rms:.5f})")
                        speech_start_time = time.time()
                    # Speech detected
                    has_spoken = True
                    silence_time = 0.0
                    audio_buffer.append(chunk)
                elif has_spoken:
                    # Trailing silence tracking
                    silence_time += block_duration
                    audio_buffer.append(chunk)
                    
                    if silence_time >= 1.0: # Stop after 1 full second of trailing silence
                        print("[AUDIO DEBUG] 1 second of trailing silence detected. Stopping.")
                        break
                        
        if not audio_buffer:
            print("[AUDIO DEBUG] Audio buffer is empty.")
            return ""
            
        print("[RAPTOR] Processing audio...")
        # Flatten all chunks into a continuous 1D float32 array
        raw_data = np.concatenate(audio_buffer).flatten()
        
        segments, info = get_stt_model().transcribe(raw_data, beam_size=1, language="en")
        
        transcription = ""
        for segment in segments:
            transcription += segment.text + " "
        
        return transcription.strip()
        
    except TimeoutError:
        raise TimeoutError("Silence timeout reached.")
    except Exception as e:
        print(f"[ERROR] STT failed: {e}")
        return ""
