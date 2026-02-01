from socket import timeout
from pymodbus.client import ModbusSerialClient
from pymodbus.client import ModbusTcpClient
from pymodbus.framer import FramerType
rtuFramer=FramerType.RTU
import logging
import time


GRIPPER_BAUDRATE = 115200
"""
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
"""
GRIPPER_MODE_RTU_VIA_TCP = "RTU_VIA_TCP"
GRIPPER_MODE_RTU = "RTU"

def gripperClient(method=GRIPPER_MODE_RTU, port = 5020, IP = "127.0.0.1", baudrate=115200, timeout=1):
    client=None
    if method == GRIPPER_MODE_RTU_VIA_TCP:
        client = ModbusTcpClient(
            host=IP,
            port=port,
            framer=rtuFramer
        )
    elif method == GRIPPER_MODE_RTU:
        client = ModbusSerialClient(
            port=port,
            baudrate=baudrate,
            timeout=timeout
        )
    return client

class Gripper():

    def __init__(self,client, device_id=9):
        self.client = client
        self.debug = False
        self.device_id = device_id

    def activate_gripper(self):
        position=int(0)
        speed=int(255)
        force=int(0)
        startTime=time.time()
        res=self.client.write_registers(1000,
                                [0,
                                    0,
                                    0],
                                device_id=self.device_id)
        res=self.client.write_registers(1000,
                                [0b0000100100000000,
                                    position,
                                    speed * 0b100000000 + force],
                                device_id=self.device_id)
        duration=time.time()-startTime
        #print(f"Activation duration: {duration} seconds")

        # Check result
        if res.isError():
            print("Activation failed:", res)
        time.sleep(3)

    def writePSF(self,position, speed, force):
        startTime=time.time()
        res=self.client.write_registers(1001,
                                [position,
                                    speed * 0b100000000 + force],
                                    device_id=self.device_id)
        duration=time.time()-startTime
        #print(f"Write duration: {duration} seconds")

        # Check result
        if res.isError():
            print("Write failed:", res)

    def writeP(self,position):
        startTime=time.time()
        res=self.client.write_registers(1001,
                                [position],
                                    device_id=self.device_id)
        duration=time.time()-startTime
        #print(f"Write duration: {duration} seconds")

        # Check result
        if res.isError():
            print("Write failed:", res)

    def writeSF(self,speed, force):
        startTime=time.time()
        res=self.client.write_registers(1002,
                                [speed * 0b100000000 + force],
                                    device_id=self.device_id)
        duration=time.time()-startTime
        #print(f"Write duration: {duration} seconds")

        # Check result
        if res.isError():
            print("Write failed:", res)

    def waitComplete(self, timeout=5.0):
        startTime=time.time()
        gOBJ=0b00
        while gOBJ == 0b00 and (time.time() - startTime) < timeout:
            result=self.client.read_input_registers(2000,count=1,device_id=self.device_id)
            registers=result.registers
            gripperStatusReg0=(registers[0] >> 8) & 0b11111111
            gOBJ=(gripperStatusReg0 >> 6) & 0b11
        duration=time.time()-startTime
        print(f"Wait complete duration: {duration} seconds, gOBJ={gOBJ}")
    def estimateAndWaitComplete(self,currentPos,requestedPos,speed):
        GRIPPER_VMAX = 332  # max speed in steps per second
        GRIPPER_VMIN = 68   # min speed in steps per second
        posBitPerSecond = GRIPPER_VMIN + ((GRIPPER_VMAX-GRIPPER_VMIN)/255)*speed
        timeToRequestedPos = abs(requestedPos-currentPos)/posBitPerSecond
        time.sleep(timeToRequestedPos)



    def currentPos(self):
        result=self.client.read_input_registers(2002,count=1,device_id=self.device_id)
        registers=result.registers
        position=(registers[0] >> 8) & 0b11111111 #xxxxxxxx00000000
        return position

#test MODE RTU
if False:
    client=gripperClient(method=GRIPPER_MODE_RTU, port = "COM8")
    client.connect()
    gripper = Gripper(client, device_id=9)
    gripper.activate_gripper()
    gripper.writeP(100)
    time.sleep(1)
    gripper.writeP(200)
    time.sleep(1)
    gripper.writeP(100)
    time.sleep(1)
    gripper.writeP(200)

#Test MODE RTU VIA TCP
if False:
    client=gripperClient(method=GRIPPER_MODE_RTU_VIA_TCP, port = 5020, IP = "10.0.0.220")
    client.connect()
    gripper = Gripper(client, device_id=9)
    gripper.activate_gripper()
    gripper.writeP(100)
    gripper.waitComplete()
    print("Current position:", gripper.currentPos())
    gripper.writePSF(200,255,255)
    gripper.waitComplete()
    print("Current position:", gripper.currentPos())
    gripper.writeP(100)
    time.sleep(1)
    gripper.writeP(200)
    time.sleep(1)
    gripper.writeP(100)
    time.sleep(1)
    gripper.writeP(200)