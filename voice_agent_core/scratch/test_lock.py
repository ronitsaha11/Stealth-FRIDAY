import os
import fcntl
import sys
import time

def test_lock():
    lock_file_path = "/tmp/raptor_agent.lock"
    # Ensure lock file exists
    if not os.path.exists(lock_file_path):
        open(lock_file_path, 'w').close()
        
    f1 = open(lock_file_path, 'w')
    try:
        fcntl.lockf(f1, fcntl.LOCK_EX | fcntl.LOCK_NB)
        print("Lock 1 acquired.")
    except IOError:
        print("Lock 1 failed (already held).")
        return

    f2 = open(lock_file_path, 'w')
    try:
        fcntl.lockf(f2, fcntl.LOCK_EX | fcntl.LOCK_NB)
        print("Lock 2 acquired (FAIL - should have been blocked).")
    except IOError:
        print("Lock 2 failed as expected.")

    fcntl.lockf(f1, fcntl.LOCK_UN)
    f1.close()
    f2.close()

if __name__ == "__main__":
    test_lock()
