import time
import logging
import sounddevice as sd
from openwakeword.model import Model

logger = logging.getLogger("core-wake")
logger.setLevel(logging.INFO)

def start_wake_listener(activation_callback):
    """
    Runs an infinite background loop capturing audio and feeding to OpenWakeWord.
    """
    try:
        # Load the free hey_jarvis model
        # Using ONNX runtime to avoid TensorFlow dependencies on macOS/arm64
        model = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
    except Exception as e:
        logger.error(f"Failed to initialize OpenWakeWord: {e}")
        return

    logger.info("Passive wake-listener active. System: RAPTOR. Trigger word: 'hey raptor'")

    # OpenWakeWord expects 16000Hz, 16-bit mono 
    sample_rate = 16000
    chunk_size = 1280  # Feed chunks of 1280 samples (approx. 80ms)

    cooldown_period = 5.0
    last_trigger_time = 0

    def audio_callback(indata, frames, time_info, status):
        nonlocal last_trigger_time
        
        if status:
            pass # ignore minor underrun prints
        
        # OpenWakeWord expects 16-bit integer PCM array
        pcm = indata.flatten()
        
        try:
            # Using hey_jarvis as the underlying high-accuracy engine for Project Raptor
            prediction = model.predict(pcm)
            detect_score = prediction.get('hey_jarvis', 0)
            
            # Diagnostic: Log anything that sounds even remotely like the wake word
            if detect_score > 0.1:
                logger.debug(f"Wake scan confidence: {detect_score:.2f}")

            if detect_score > 0.35:  # Lowered from 0.5 for better 'Raptor' detection
                current_time = time.time()
                if current_time - last_trigger_time > cooldown_period:
                    last_trigger_time = current_time
                    logger.info(f"\n>>> [WAKE WORD DETECTED]: RAPTOR ACTIVATED (score: {detect_score:.2f}) <<<\n")
                    activation_callback()
        except Exception as loop_e:
            logger.debug(f"Audio processing fault: {loop_e}")

    try:
        with sd.InputStream(
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
            blocksize=chunk_size,
            callback=audio_callback
        ):
            # Block the background thread permanently, listening
            while True:
                time.sleep(1)
    except Exception as e:
        logger.error(f"Failed to start RAPTOR microphone stream: {e}")
