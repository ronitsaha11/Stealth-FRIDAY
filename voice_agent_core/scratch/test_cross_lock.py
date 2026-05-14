import os
import fcntl
import sys
import time
import subprocess

def run_p1():
    print("P1 starting...")
    lock_file = open('/tmp/raptor_agent.lock', 'w')
    try:
        fcntl.lockf(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        print("P1 Lock Acquired.")
        time.sleep(5)
        print("P1 released.")
    except IOError:
        print("P1 Lock Failed.")

def run_p2():
    print("P2 starting...")
    time.sleep(2)
    lock_file = open('/tmp/raptor_agent.lock', 'w')
    try:
        fcntl.lockf(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        print("P2 Lock Acquired.")
    except IOError:
        print("P2 Lock Failed as expected.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "p2":
        run_p2()
    else:
        # Start P1 in background
        proc1 = subprocess.Popen([sys.executable, __file__, "p2"])
        run_p1()
        proc1.wait()
