import time
from pymodbus.client import ModbusTcpClient
from gripperSerialControl import *
import numpy as np
import argparse

#TCP_COM_TIME=0.0011
#RTU_COM_TIME=0.0179

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
        modbusTCPServer_client = ModbusTcpClient("127.0.0.1", port=502)
        modbusTCPServer_client.connect()
        

        #Variables
        gClient=gripperClient(method=args.method, port=args.gripper_port, IP=args.gripper_IP)
        #print("Gripper ID is : ", args.gripper_id)
        gripper=Gripper(gClient,device_id=args.gripper_id)
        gripper.activate_gripper()
        gripper.writePSF(0,255,255)
        speedFactor=4
        previousCalculatedPos = 0
        previousPosRequest = 0
        previousSpeed = 0
        previousTime = time.monotonic()
        now =time.monotonic()

        total_tcp_com_time = 0
        nbr_tcp_com = 0
        average_tcp_com_time = 0

        total_rtu_com_time = 0
        nbr_rtu_com = 0
        average_rtu_com_time = 0






        while True:
            previousTime = now
            now =time.monotonic()
            #Loop duration
            duration = now-previousTime

            start_tcp_com = time.monotonic()
            newPosRequest = modbusTCPServer_client.read_holding_registers(address=0, count=1).registers[0]
            end_tcp_com = time.monotonic()
            total_tcp_com_time = total_tcp_com_time + end_tcp_com -start_tcp_com
            nbr_tcp_com += 1
            average_tcp_com_time = total_tcp_com_time / nbr_tcp_com
            

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
            
            force=0
            newSpeedCommand=0


            if newCalculatedPos != newPosRequest:
                
                if newPosRequest <3 and previousPosRequest>=3:
                    print("Full open")
                    force=255
                    gripper.writePSF(0,255,force)
                    gripper.waitComplete()

                elif newPosRequest >228 and previousPosRequest<=228:
                    print("Full close")
                    force=255
                    gripper.writePSF(255,255,force)
                    gripper.waitComplete()

                elif newPosRequest >=3 and newPosRequest <=228:
                    if (previousCalculatedPos<3 or previousCalculatedPos>228):
                        print("Released from endstop",previousCalculatedPos)
                        force=255
                        gripper.writePSF(newPosRequest,255,force)
                        gripper.waitComplete()

                    else:
                        
                        newSpeedCommand= int(abs(newPosDelta*speedFactor))
                        if newSpeedCommand>255:
                            newSpeedCommand=int(255)
                        #newSpeedCommand=int((newSpeedCommand//10)*10)
                        
                        force=0
                        if (previousPosRequest != newPosRequest) or (previousSpeed != newSpeedCommand):
                            start_rtu_com = time.monotonic()
                            gripper.writePSF(newPosRequest,newSpeedCommand,force)
                            end_rtu_com = time.monotonic()
                            total_rtu_com_time = total_rtu_com_time + end_rtu_com -start_rtu_com
                            nbr_rtu_com += 1
                            average_rtu_com_time = total_rtu_com_time / nbr_rtu_com
                            print(f"Currently at {newCalculatedPos}, moving to {newPosRequest} at speed {newSpeedCommand}")
                        else:
                            pass

                else:
                    pass
            else:
                pass

            #print("send wait")
            #print(f"continue_sleep : {abs(continue_sleep_time):.4f}  send sleep : {abs(send_command_sleep_time):.4f}")
            #print(f"----{duration}----")
            #print(f"resquest {previousPosRequest} , calc pos {previousCalculatedPos} , speed {previousSpeed:.4f} ")
            #print(f"resquest {newPosRequest} , calc pos {newCalculatedPos} , speed {newSpeedCommand:.4f} ")
            #print(f"tcp time {average_tcp_com_time:.4f}, rtu time {average_rtu_com_time:.4f}")
            previousCalculatedPos = newCalculatedPos
            previousPosRequest = newPosRequest
            previousSpeed = newSpeedCommand
            time.sleep(0.001)
            
    except KeyboardInterrupt:
        print("Server monitoring received Ctrl+C, shutting down...")
    finally:
        modbusTCPServer_client.close()  # ensure the client is always closed
        print("Client connection closed.")

if __name__ == "__main__":
    run_monitor()
