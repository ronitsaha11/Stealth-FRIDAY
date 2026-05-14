import os, fcntl
LOCK_FILE_AGENT = "/tmp/raptor_agent.lock"
if not os.path.exists(LOCK_FILE_AGENT):
    print("Lock file missing")
else:
    try:
        with open(LOCK_FILE_AGENT, 'a') as f:
            try:
                fcntl.lockf(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.lockf(f, fcntl.LOCK_UN)
                print("Lock is FREE (agent not running)")
            except IOError:
                print("Lock is HELD (agent is running)")
    except Exception as e:
        print(f"Error: {e}")
