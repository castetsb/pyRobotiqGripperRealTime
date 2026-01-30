import time
from pymodbus.client import ModbusTcpClient
import numpy as np
import argparse
from robotiq_gripper import *

GRIPPER_VMAX = 332  # max speed in steps per second
GRIPPER_VMIN = 68   # min speed in steps per second
GRIPPER_BAUDRATE = 115200

#TCP_COM_TIME=0.0011
#RTU_COM_TIME=0.0179

# parse args
parser = argparse.ArgumentParser()
parser.add_argument('--robot_IP', type=str, default='10.0.0.0', help='IP of the robot on which is mounted the gripper')
args = parser.parse_args()

def timeToPos(startPos,endPos,speed):
    
    time=abs((endPos-startPos)/(GRIPPER_VMIN+(GRIPPER_VMAX-GRIPPER_VMIN)*speed/255))
    return time


def run_monitor():
    print("Modbus TCP server monitoring running...")
    try:
        modbusTCPServer_client = ModbusTcpClient("127.0.0.1", port=502)
        modbusTCPServer_client.connect()
        

        #Variables
        print("Creating gripper...")
        gripper = RobotiqGripper()
        print("Connecting to gripper...")
        gripper.connect(hostname = args.robot_IP, port = 63352)
        print("Activating gripper...")
        gripper.activate()

        gripper.move(position = 0,speed = 255,force = 255)

        speedFactor=4

        previousCalculatedPos = 0
        previousPosRequest = 0
        previousSpeed = 0
        previousTime = time.monotonic()
        now =time.monotonic()

        while True:
            previousTime = now
            now =time.monotonic()
            #Loop duration
            duration = now-previousTime

            newPosRequest = modbusTCPServer_client.read_holding_registers(address=0, count=1).registers[0]
            
            #Calculate predicted position
            previousPosDelta = previousPosRequest - previousCalculatedPos
            
            previousDirection = np.sign(previousPosDelta)

            motion = int(previousDirection * (GRIPPER_VMIN + (GRIPPER_VMAX - GRIPPER_VMIN) * previousSpeed / 255) * duration)

            #print(f"Previous direction {previousDirection} , previous spped {previousSpeed} ,  {duration:.4f} , {motion:.4f}")
            
            newCalculatedPos = 0
            
            if abs(previousPosDelta) < abs(motion):
                newCalculatedPos = previousPosRequest
            else:
                newCalculatedPos = previousCalculatedPos + motion
            
            if newCalculatedPos<3 or previousPosRequest<3:
                newCalculatedPos=2
            if newCalculatedPos>228 or previousPosRequest>228:
                newCalculatedPos=229
            

            #Calculate new speed
            newPosDelta = newPosRequest - newCalculatedPos

            #Calculate new speed command

            newSpeedCommand= int(abs(newPosDelta*speedFactor))
            if newSpeedCommand>255:
                newSpeedCommand=int(255)
            
            force=0


            if newCalculatedPos != newPosRequest:
                
                if newPosRequest <3 and previousPosRequest>=3:
                    print("Full open")
                    force=255
                    gripper.move(0,255,force)
                    time.sleep(timeToPos(newCalculatedPos,0,255))

                elif newPosRequest >228 and previousPosRequest<=228:
                    print("Full close")
                    force=255
                    gripper.move(255,255,force)
                    time.sleep(timeToPos(newCalculatedPos,255,255))

                elif newPosRequest >=3 and newPosRequest <=228:
                    if (previousCalculatedPos<3 or previousCalculatedPos>228):
                        print("Released from endstop",previousCalculatedPos)
                        force=255
                        gripper.move(0,255,force)
                        time.sleep(timeToPos(newCalculatedPos,newPosRequest,255))

                    else:
                        #print(f"Currently at {newCalculatedPos}, moving to {newPosRequest} at speed {newSpeedCommand}")
                        
                        gripper.move(newPosRequest,newSpeedCommand,force)

                else:
                    pass
            else:
                pass

            previousCalculatedPos = newCalculatedPos
            previousPosRequest = newPosRequest
            previousSpeed = newSpeedCommand
            time.sleep(0.001)
            
    except KeyboardInterrupt:
        print("Server monitoring received Ctrl+C, shutting down...")
    finally:
        gripper.disconnect()
        modbusTCPServer_client.close()  # ensure the client is always closed
        print("Client connection closed.")

if __name__ == "__main__":
    run_monitor()
