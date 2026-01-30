import subprocess
import sys
import signal
import time
import os
import argparse

venv_python = sys.executable

# Parse command-line arguments by name
parser = argparse.ArgumentParser(description='Launch Modbus TCP server and gripper monitor')

# Server-specific arguments
parser.add_argument("-d", "--debug", action='store_true', help='set debug mode')

# Monitor-specific arguments

parser.add_argument('--robot_IP', type=str, default='10.0.0.0', help='IP of the robot on which is mounted the gripper')

args = parser.parse_args()

server_specific_args=[]
# ===== Server args =====
if args.debug:
    server_specific_args.append('--debug')

# ===== Monitor args =====
monitor_specific_args = [
    '--robot_IP', args.robot_IP,
]

server_args = [venv_python, "modbusTCPServer.py"] + server_specific_args
monitor_args = [venv_python, "gripperControlViaModbusTCP.py"] + monitor_specific_args

# Start subprocesses in new process groups (platform-specific)
p1 = subprocess.Popen(server_args, preexec_fn=os.setsid)
p2 = subprocess.Popen(monitor_args, preexec_fn=os.setsid)

def terminate_subprocesses():
    print("\nTerminating subprocesses...")
    try:
        os.killpg(os.getpgid(p1.pid), signal.SIGTERM)
    except Exception as e:
        print("Error sending signal to server:", e)
    try:
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
