import sounddevice as sd
import numpy as np
import time

def list_and_test_mic():
    print("\n--- AUDIO DEVICE DIAGNOSTIC ---")
    devices = sd.query_devices()
    print(devices)
    
    default_input = sd.query_devices(kind='input')
    print(f"\nDefault Input Device: {default_input['name']}")
    
    print("\n--- TESTING INPUT LEVELS (5 seconds) ---")
    print("Please make some noise or say 'Hey Raptor'...")
    
    def callback(indata, frames, time_info, status):
        volume_norm = np.linalg.norm(indata) * 10
        print(f"|{'=' * int(volume_norm)}", end='\r')

    with sd.InputStream(callback=callback):
        time.sleep(5)
    print("\n--- TEST COMPLETE ---")

if __name__ == "__main__":
    try:
        list_and_test_mic()
    except Exception as e:
        print(f"Error during audio test: {e}")
