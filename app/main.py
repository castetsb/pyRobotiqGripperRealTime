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
parser.add_argument("--hmi", action='store_true', help='Generate a graphic interface to send psotion commadn to the TCP server. Use a VNC client and connect to localhost:5900 to see it.')

# Monitor-specific arguments

parser.add_argument('--method', type=str, default="RTU_VIA_TCP", help='Gripper communication method (default: RTU_VIA_TCP). RTU is also supported.')
parser.add_argument('--gripper_id', type=int, default=9, help='Gripper device ID (default: 9)')
parser.add_argument('--gripper_port', default='54321', help='TCP port or serial port of the gripper (default: 5020). In case of serial port should be something like /dev/ttyUSB0')

parser.add_argument('--gripper_IP', type=str, default='10.0.0.0', help='Gripper IP address (default: 10.0.0.0)')


args = parser.parse_args()

server_specific_args=[]
# ===== Server args =====
if args.debug:
    server_specific_args.append('--debug')

# ===== Monitor args =====
monitor_specific_args = [
    '--method', args.method,
    '--gripper_id', str(args.gripper_id),
    '--gripper_port', str(args.gripper_port),
    '--gripper_IP', args.gripper_IP,
]

server_args = [venv_python, "modbusTCPServer.py"] + server_specific_args
monitor_args = [venv_python, "gripperControlViaModbusTCP.py"] + monitor_specific_args
if args.hmi:
    hmi_args =[venv_python,"realtimeInterfaceTCP.py"]

# Start subprocesses in new process groups (platform-specific)
p1 = subprocess.Popen(server_args, preexec_fn=os.setsid)
p2 = subprocess.Popen(monitor_args, preexec_fn=os.setsid)
p3=None
if args.hmi:
    p3 = subprocess.Popen(hmi_args, preexec_fn=os.setsid)

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
    if p3:
        try:
            os.killpg(os.getpgid(p3.pid), signal.SIGTERM)
        except Exception as e:
            print("Error sending signal to hmi:", e)

    # Wait for processes to exit
    p1.wait()
    p2.wait()
    if args.hmi:
        p3.wait()
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
            if args.hmi:
                if p3.poll() is not None:
                    break
        time.sleep(0.5)
except KeyboardInterrupt:
    terminate_subprocesses()
