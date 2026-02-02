import time
import pygame
from  gripperSerialControl import *
from commandFilter import *
import argparse
import robotiq_gripper
import sys

# parse args
parser = argparse.ArgumentParser()
parser.add_argument('--joystick_id', type=int, default=0, help='ID of the joystick')
parser.add_argument('--method', type=str, default="RTU", help='Gripper communication method (default: RTU). RTU_VIA_TCP and ROBOTIQ_URCAP are also available')
parser.add_argument('--gripper_id', type=int, default=9, help='Gripper device ID (default: 9)')
parser.add_argument('--gripper_port', default='5020', help='TCP port or serial port of the gripper. 54321 for RS485 URCAP. 63352 for Robotiq URCAP. COM0 (Windows) or /dev/tty/USB0 (Linux) for serial.')
parser.add_argument('--robot_ip', type=str, default='10.0.0.0', help='Robot IP address (default: 10.0.0.0)')

args = parser.parse_args()


# --- Init joystick ---


def map_0_255(x):
    """
    Map a value from [-1, 1] to [2, 255].
    """
    return int((x + 1) * (228-2)/(1-(-1))+2)

def run_joystickControl():
    try:
        pygame.init()
        pygame.joystick.init()
        js = pygame.joystick.Joystick(args.joystick_id)
        js.init()

        print("Joystick:", js.get_name())

        if args.method == "RTU":
            gClient=gripperClient(method="RTU",port=args.gripper_port)
            gripper = Gripper(gClient)
            gripper.activate_gripper()
        elif args.method == "RTU_VIA_TCP":
            gClient=gripperClient(method="RTU_VIA_TCP",port=54321,IP = args.robot_ip)
            gripper = Gripper(gClient)
            gripper.activate_gripper()
        elif args.method == "ROBOTIQ_URCAP":
            gripper = robotiq_gripper.RobotiqGripper()
            gripper.connect(args.robot_ip, gripper_port)
            gripper.activate()
        
        previousRequestTime = time.monotonic()
        previousPosRequest = 0
        previousPos = 0
        previousSpeed = 0
        previousForce = 0
        
        
        while True:
            pygame.event.pump()
            joy0 = js.get_axis(0)  # Right stick Y

            newPosRequest = map_0_255(joy0)
            #print(joy0)

            #2- Get time
            now=time.monotonic()
            
            #2 Build gripper command
            command = commandFilter(newPosRequest,now,previousRequestTime,previousPos,previousPosRequest,previousSpeed,previousForce,5,110)
            if command["toExecute"]:

                print(f"Previous: P_request {previousPosRequest:.0f}, P{previousPos:.0f} , S {previousSpeed:.0f}, F{previousForce:.0f} >> New: P_request {command['positionRequest']:.0f}, P{command['currentPosition']:.0f}, S {command['speedRequest']:.0f}, F{command['forceRequest']:.0f}")
            else:
                pass
            
            previousRequestTime = now
            previousPosRequest = command["positionRequest"]
            previousPos = command["currentPosition"]
            previousSpeed = command["speedRequest"]
            previousForce = command["forceRequest"]

            if command["toExecute"]:
                if args.method == "ROBOTIQ_URCAP":
                    gripper.move(command["positionRequest"],command["speedRequest"],command["forceRequest"])
                else:
                    gripper.writePSF(command["positionRequest"],command["speedRequest"],command["forceRequest"])
                
                if command["waitUntilComplete"]:
                    gripper.estimateAndWaitComplete(command["currentPosition"],command["positionRequest"],command["speedRequest"])
            time.sleep(0.001)

    except KeyboardInterrupt:
        print("Stopping")

    finally:
        pygame.quit()

# Start the application event loop
if __name__ == '__main__':
    run_joystickControl()