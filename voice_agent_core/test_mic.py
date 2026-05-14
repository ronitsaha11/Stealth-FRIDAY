import sounddevice as sd
import numpy as np
import time

sample_rate = 16000
block_duration = 0.1

print("Testing mic for 5 seconds...")
with sd.InputStream(samplerate=sample_rate, channels=1, dtype='float32') as stream:
    start = time.time()
    while time.time() - start < 5:
        chunk, overflowed = stream.read(int(sample_rate * block_duration))
        rms = np.sqrt(np.mean(chunk**2))
        print(f"RMS: {rms:.5f}")
