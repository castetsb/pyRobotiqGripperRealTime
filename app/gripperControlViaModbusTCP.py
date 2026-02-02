import time
from pymodbus.client import ModbusTcpClient
from gripperSerialControl import *
import numpy as np
import argparse
from commandFilter import commandFilter

# parse args
parser = argparse.ArgumentParser()
parser.add_argument('--method', type=str, default="RTU_VIA_TCP", help='Gripper communication method (default: RTU_VIA_TCP). RTU is also supported.')
parser.add_argument('--gripper_id', type=int, default=9, help='Gripper device ID (default: 9)')
parser.add_argument('--gripper_port', default='5020', help='TCP port or serial port of the gripper (default: 5020)')
parser.add_argument('--gripper_IP', type=str, default='10.0.0.0', help='Gripper IP address (default: 10.0.0.0)')

args = parser.parse_args()

def run_monitor():
    print("Server monitoring running...")
    try:
        #Connect to modbus TCP server
        print("Gripper driver connecting to TCP server")
        modbusTCPServer_client = ModbusTcpClient("127.0.0.1", port=502)
        modbusTCPServer_client.connect()
        
        #Connect to the gripper, activate it and open it
        gClient=gripperClient(method=args.method, port=args.gripper_port, IP=args.gripper_IP)

        gripper=Gripper(gClient,device_id=args.gripper_id)
        print("Gripper Activation")
        gripper.activate_gripper()
        print("Gripper performing a full open")
        gripper.writePSF(0,0,0)
        gripper.estimateAndWaitComplete(255,0,0)

        maxFrequency = 0
        
        previousRequestTime = time.monotonic()
        previousPosRequest = 0
        previousPos = 0
        previousSpeed = 0
        previousForce = 0
        
        while True:
            #1- Get new positon command
            newPosRequest = modbusTCPServer_client.read_holding_registers(address=0, count=1).registers[0]

            #2- Get time
            now=time.monotonic()
            
            #2 Build gripper command
            command = commandFilter(newPosRequest,now,previousRequestTime,previousPos,previousPosRequest,previousSpeed,previousForce,5,110)
            if command["toExecute"]:

                print(f"maPrevious P_request {previousPosRequest:.0f}, P{previousPos:.0f} , S {previousSpeed:.0f}, F{previousForce:.0f}, New P_request {command['positionRequest']:.0f}, P{command['currentPosition']:.0f}, S {command['speedRequest']:.0f}, F{command['forceRequest']:.0f}")
            else:
                pass
            
            previousRequestTime = now
            previousPosRequest = command["positionRequest"]
            previousPos = command["currentPosition"]
            previousSpeed = command["speedRequest"]
            previousForce = command["forceRequest"]

            if command["toExecute"]:
                gripper.writePSF(command["positionRequest"],command["speedRequest"],command["forceRequest"])
                if command["waitUntilComplete"]:
                    gripper.estimateAndWaitComplete(command["currentPosition"],command["positionRequest"],command["speedRequest"])
            time.sleep(0.001)
            
    except KeyboardInterrupt:
        print("Server monitoring received Ctrl+C, shutting down...")
    finally:
        modbusTCPServer_client.close()  # ensure the client is always closed
        print("Client connection closed.")

if __name__ == "__main__":
    run_monitor()
