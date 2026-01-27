import time
from pymodbus.client import ModbusTcpClient
from gripperSerialControl import *
import numpy as np

def run_monitor():
    print("Server monitoring running...")
    try:
        client = ModbusTcpClient("127.0.0.1", port=502)
        client.connect()



        #Variables
        gripper=Gripper()
        gripper.activate_gripper()
        gripper.writePSF(0,255,255)
        speedFactor=4
        previousCalculatedPos = 0
        previousPosRequest = 0
        previousSpeed = 0
        previousTime = time.time()

        while True:
            newPosRequest = client.read_holding_registers(address=0, count=1).registers[0]

            #Loop duration
            now =time.time()
            duration = now-previousTime

            #Calculate predicted position
            previousPosDelta = previousPosRequest - previousCalculatedPos
            
            previousDirection = np.sign(previousPosDelta)

            motion = int(previousDirection * (GRIPPER_VMIN + (GRIPPER_VMAX - GRIPPER_VMIN) * previousSpeed / 255) * duration)
            
            newCalculatedPos = 0
            
            if abs(previousPosDelta) < abs(motion):
                newCalculatedPos = previousPosRequest
            else:
                newCalculatedPos = previousCalculatedPos + motion
            
            if newCalculatedPos<3:
                newCalculatedPos=3
            if newCalculatedPos>228:
                newCalculatedPos=228

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
                    gripper.writePSF(0,255,force)
                elif newPosRequest >228 and previousPosRequest<=228:
                    print("Full close")
                    force=255
                    gripper.writePSF(255,255,force)
                elif newPosRequest >=3 and newPosRequest <=228:
                    if (previousPosRequest<3 or previousPosRequest>228):
                        print("Released from endstop")
                        force=255
                        gripper.writePSF(newPosRequest,255,force)
                        gripper.waitComplete()
                    else:
                        print(f"Currently at {newCalculatedPos}, moving to {newPosRequest} at speed {newSpeedCommand}")
                        force=0
                        gripper.writePSF(newPosRequest,newSpeedCommand,force)
            previousCalculatedPos = newCalculatedPos
            previousPosRequest = newPosRequest
            previousSpeed = newSpeedCommand
            previousTime = now
    except KeyboardInterrupt:
        print("Server monitoring received Ctrl+C, shutting down...")
    finally:
        client.close()  # ensure the client is always closed
        print("Client connection closed.")

if __name__ == "__main__":
    run_monitor()
