# launcher.py
import subprocess
import sys
import signal
import time
import os

venv_python = sys.executable

# Arguments for each subprocess
server_args = [venv_python, "modbusTCPServer.py"] + sys.argv[1:4]
monitor_args = [venv_python, "gripperControlViaModbusTCP.py"] + sys.argv[4:]

# Start subprocesses in new process groups (platform-specific)
if os.name == 'nt':  # Windows
    p1 = subprocess.Popen(server_args, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    p2 = subprocess.Popen(monitor_args, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
else:  # Linux/Unix
    p1 = subprocess.Popen(server_args, preexec_fn=os.setsid)
    p2 = subprocess.Popen(monitor_args, preexec_fn=os.setsid)

def terminate_subprocesses():
    print("\nTerminating subprocesses...")
    try:
        if os.name == 'nt':  # Windows
            p1.send_signal(signal.CTRL_BREAK_EVENT)
        else:  # Linux/Unix
            os.killpg(os.getpgid(p1.pid), signal.SIGTERM)
    except Exception as e:
        print("Error sending signal to server:", e)
    try:
        if os.name == 'nt':  # Windows
            p2.send_signal(signal.CTRL_BREAK_EVENT)
        else:  # Linux/Unix
            os.killpg(os.getpgid(p2.pid), signal.SIGTERM)
    except Exception as e:
        print("Error sending signal to monitor:", e)

    # Wait for processes to exit
    p1.wait()
    p2.wait()
    print("Both subprocesses terminated.")

# Handle Ctrl+C
def signal_handler(sig, frame):
    terminate_subprocesses()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

try:
    # Keep the launcher alive and monitor subprocesses
    while True:
        if p1.poll() is not None and p2.poll() is not None:
            # Both subprocesses exited
            break
        time.sleep(0.5)
except KeyboardInterrupt:
    terminate_subprocesses()
