import time
from pymodbus.client import ModbusTcpClient
from gripperSerialControl import *
import numpy as np
import argparse



CONTINUE = 0
SEND_COMMAND = 1
SEND_WAIT_COMMAND = 2



# parse args
parser = argparse.ArgumentParser()
parser.add_argument('--method', type=str, default="RTU_VIA_TCP", help='Gripper communication method (default: RTU_VIA_TCP). RTU is also supported.')
parser.add_argument('--gripper_id', type=int, default=9, help='Gripper device ID (default: 9)')
parser.add_argument('--gripper_port', default='5020', help='TCP port or serial port of the gripper (default: 5020)')
parser.add_argument('--gripper_IP', type=str, default='10.0.0.0', help='Gripper IP address (default: 10.0.0.0)')

args = parser.parse_args()

MONITORING_FREQUENCY = 500
MONITORING_PERIOD = 1/500

def run_monitor():
    print("Server monitoring running...")
    try:
        modbusTCPServer_client = ModbusTcpClient("127.0.0.1", port=502)
        modbusTCPServer_client.connect()
        

        #Variables
        communicationStatus= CONTINUE
        continue_sleep_time=0
        send_command_sleep_time=0.001
        gClient=gripperClient(method=args.method, port=args.gripper_port, IP=args.gripper_IP)
        print("Gripper ID is : ", args.gripper_id)
        gripper=Gripper(gClient,device_id=args.gripper_id)
        gripper.activate_gripper()
        gripper.writePSF(0,255,255)
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
            
            if communicationStatus == CONTINUE:
                continue_sleep_time=(MONITORING_PERIOD-(duration-continue_sleep_time))
                continue_sleep_time=continue_sleep_time*(continue_sleep_time>0)
            elif communicationStatus == SEND_COMMAND:
                send_command_sleep_time=MONITORING_PERIOD-(duration-send_command_sleep_time)
                send_command_sleep_time=send_command_sleep_time*(send_command_sleep_time>0)
            print(f"frequency {1/duration:.0f} send sleep {send_command_sleep_time:.4f} continue sleep {continue_sleep_time:.4f}")


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
                    gripper.writePSF(0,255,force)
                    gripper.waitComplete()
                    communicationStatus = SEND_WAIT_COMMAND

                elif newPosRequest >228 and previousPosRequest<=228:
                    print("Full close")
                    force=255
                    gripper.writePSF(255,255,force)
                    gripper.waitComplete()
                    communicationStatus = SEND_WAIT_COMMAND

                elif newPosRequest >=3 and newPosRequest <=228:
                    if (previousCalculatedPos<3 or previousCalculatedPos>228):
                        print("Released from endstop",previousCalculatedPos)
                        force=255
                        gripper.writePSF(newPosRequest,255,force)
                        gripper.waitComplete()
                        communicationStatus = SEND_WAIT_COMMAND

                    else:
                        #print(f"Currently at {newCalculatedPos}, moving to {newPosRequest} at speed {newSpeedCommand}")
                        force=0
                        gripper.writePSF(newPosRequest,newSpeedCommand,force)
                        communicationStatus = SEND_COMMAND
                else:
                    communicationStatus = CONTINUE
            else:
                communicationStatus = CONTINUE
            
            if communicationStatus == CONTINUE:
                #print("continue")
                time.sleep(continue_sleep_time)
            elif communicationStatus == SEND_COMMAND:
                #print("send")
                time.sleep(send_command_sleep_time)
            else:
                pass
                #print("send wait")
            #print(f"continue_sleep : {abs(continue_sleep_time):.4f}  send sleep : {abs(send_command_sleep_time):.4f}")
            #print(f"----{duration}----")
            #print(f"resquest {previousPosRequest} , calc pos {previousCalculatedPos} , speed {previousSpeed:.4f} ")
            #print(f"resquest {newPosRequest} , calc pos {newCalculatedPos} , speed {newSpeedCommand:.4f} ")
            previousCalculatedPos = newCalculatedPos
            previousPosRequest = newPosRequest
            previousSpeed = newSpeedCommand
            
    except KeyboardInterrupt:
        print("Server monitoring received Ctrl+C, shutting down...")
    finally:
        modbusTCPServer_client.close()  # ensure the client is always closed
        print("Client connection closed.")

if __name__ == "__main__":
    run_monitor()
