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

parser.add_argument('--method', type=str, default="RTU_VIA_TCP", help='Gripper communication method (default: RTU_VIA_TCP). RTU is also supported.')
parser.add_argument('--gripper_id', type=int, default=9, help='Gripper device ID (default: 9)')
parser.add_argument('--gripper_port', default='54321', help='TCP port or serial port of the gripper (default: 5020). In case of serial port should be something like /dev/ttyUSB0')
"""
In situation where you want to control a gripper connected to the windows PC
where is running the docker. Use usbipd in window terminal to share the USB
device.

A similar procedure should exist for people running on linux.

usbipd list

This will list all USB device available on the PC
ex:
Connected:
BUSID  VID:PID    DEVICE                                                        STATE
2-2    0403:6015  USB Serial Converter                                          Attached
2-3    2357:0604  TP-Link Bluetooth 5.3 USB Adapter                             Not shared
2-5    0c45:6705  Integrated Webcam                                             Not shared
2-7    04f3:0201  USB Input Device                                              Not shared
3-6    8087:07dc  Intel(R) Wireless Bluetooth(R)                                Not shared

usbipd attach --wsl -busid 2-2

This will attach the device 2-2 to wsl which is docker environment

wsl -d docker-desktop

This start the linux distribution of docker in the terminal

ls /dev/ttyUSB*

This will list all connected device
ex:
/dev/ttyUSB0

We have now the name of the port
"""

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
