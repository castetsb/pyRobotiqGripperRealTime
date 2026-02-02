import time
import pygame
from  gripperSerialControl import *
from commandFilter import *


# --- Init joystick ---


def map_0_255(x):
    """
    Map a value from [-1, 1] to [2, 255].
    """
    return int((x + 1) * (228-2)/(1-(-1))+2)

try:
    pygame.init()
    pygame.joystick.init()
    js = pygame.joystick.Joystick(0)
    js.init()

    print("Joystick:", js.get_name())


    gClient=gripperClient(method="RTU",port="COM8")
    gripper = Gripper(gClient)
    gripper.activate_gripper()
    
    
    
    
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
    print("Stopping")

finally:
    pygame.quit()
