#A minimalist Modbus RTU client to control a Robotiq 2F-85 gripper over serial communication.


import numpy as np
from socket import timeout
from pymodbus.client import ModbusSerialClient
import logging
import time

GRIPPER_VMAX = 332  # max speed in steps per second
GRIPPER_VMIN = 68   # min speed in steps per second
"""
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
"""

class Gripper(ModbusSerialClient):

    def __init__(self, port="/dev/ttyUSB0", baudrate=115200, parity="N", stopbits=1, bytesize=8, timeout=1):
        super().__init__(port="/dev/ttyUSB0", baudrate=115200, parity="N", stopbits=1, bytesize=8, timeout=1)
        self.debug = False
        #To have com port accessible on docker image running on windows, use usbipd to attach the usb device to the linux vm

    def activate_gripper(self):
        position=int(0)
        speed=int(255)
        force=int(0)
        startTime=time.time()
        res=self.write_registers(1000,
                                [0,
                                    0,
                                    0],
                                device_id=9)
        res=self.write_registers(1000,
                                [0b0000100100000000,
                                    position,
                                    speed * 0b100000000 + force],
                                device_id=9)
        duration=time.time()-startTime
        #print(f"Activation duration: {duration} seconds")

        # Check result
        if res.isError():
            print("Activation failed:", res)
        time.sleep(3)

    def writePSF(self,position, speed, force):
        startTime=time.time()
        res=self.write_registers(1001,
                                [position,
                                    speed * 0b100000000 + force],
                                    device_id=9)
        duration=time.time()-startTime
        #print(f"Write duration: {duration} seconds")

        # Check result
        if res.isError():
            print("Write failed:", res)

    def writeP(self,position):
        startTime=time.time()
        res=self.write_registers(1001,
                                [position],
                                    device_id=9)
        duration=time.time()-startTime
        #print(f"Write duration: {duration} seconds")

        # Check result
        if res.isError():
            print("Write failed:", res)

    def writeSF(self,speed, force):
        startTime=time.time()
        res=self.write_registers(1002,
                                [speed * 0b100000000 + force],
                                    device_id=9)
        duration=time.time()-startTime
        #print(f"Write duration: {duration} seconds")

        # Check result
        if res.isError():
            print("Write failed:", res)

    def waitComplete(self, timeout=5.0):
        startTime=time.time()
        gOBJ=0b00
        while gOBJ == 0b00 and (time.time() - startTime) < timeout:
            result=self.read_input_registers(2000,count=1,device_id=9)
            registers=result.registers
            gripperStatusReg0=(registers[0] >> 8) & 0b11111111
            gOBJ=(gripperStatusReg0 >> 6) & 0b11
        duration=time.time()-startTime
        print(f"Wait complete duration: {duration} seconds, gOBJ={gOBJ}")

    def currentPos(self):
        result=self.read_input_registers(2002,count=1,device_id=9)
        registers=result.registers
        position=(registers[0] >> 8) & 0b11111111 #xxxxxxxx00000000
        return position

