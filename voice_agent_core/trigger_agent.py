import time
import threading
from agent import LocalVoiceAgent

def auto_wake(agent):
    time.sleep(3)
    print(">>> ARTIFICIALLY TRIGGERING WAKE WORD <<<")
    agent.on_wake_word_detected()

agent = LocalVoiceAgent()
t = threading.Thread(target=auto_wake, args=(agent,))
t.start()
agent.run()
