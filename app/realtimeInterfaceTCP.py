#################################################################
#
# LIBRARIES
#
#################################################################


import sys
from gripperSerialControl import *

import numpy as np
#import os
#os.environ["QT_QPA_PLATFORM"] = "offscreen"

import os
print("DISPLAY =", os.environ.get("DISPLAY"))

from PyQt5 import QtWidgets
import pyqtgraph as pg

from pyqtgraph import QtCore, QtGui

from pathlib import Path

from datetime import datetime
import time
from scipy import signal, interpolate
from scipy.interpolate import UnivariateSpline
from scipy.interpolate import PchipInterpolator
from scipy.interpolate import CubicSpline

from pymodbus.client import ModbusTcpClient

def find_intercept(x, y, m):
    """
    Calculate y-intercept c of a line y = m*x + c
    given a point (x, y) and slope m.
    """
    c = y - m * x
    return c

#################################################################
#
# Variables
#
#################################################################


#Time buffer in ms
timeBuffer=1000
minComTime = 1
maxComTime = 0
speedFactor=4

client = ModbusTcpClient("127.0.0.1", port=502)
client.connect()


#################################################################
#
# GUI
#
#################################################################

# Create the application
app = QtWidgets.QApplication([])
#Main window
mainWindow=QtWidgets.QMainWindow()
mainWindow.setWindowTitle("Robotiq realtime gripper controller")

#ToolBar
#toolbar = QtWidgets.QToolBar("Main toolbar")
#mainWindow.addToolBar(toolbar)

#Main widget
mainWidget=QtWidgets.QWidget()
mainWindow.setCentralWidget(mainWidget)

# Set up the timed data plot
##############################
timedPlot = pg.PlotWidget()#win.addPlot(title="Last 5s events",row=1,col=0)
timedPlot.setRange(yRange=[0,255],xRange=[-5,1])
timedPlot.showGrid(True, True)

#Create curves
timedCurves={}
timedCurves["posRequest"]=timedPlot.plot(pen='r')
timedCurves["filteredPosRequest"]=timedPlot.plot(pen='w')
timedCurves["linePosCommand"]=timedPlot.plot(pen='y')
timedCurves["calculatedPos"]=timedPlot.plot(pen='b')
timedCurves["speedCommand"]=timedPlot.plot(pen='c')

"""
Possible plot colors
'b' - blue
'g' - green
'r' - red
'c' - cyan
'm' - magenta
'y' - yellow
'k' - black
'w' - white

or (r, g, b)
"""
timedData={}
timedData["time"]= np.ones(timeBuffer) * time.time()
timedData["posRequest"]= np.zeros(timeBuffer)
timedData["currentPos"]= np.zeros(timeBuffer)
timedData["calculatedPos"]= np.zeros(timeBuffer)
timedData["speedCommand"]= np.zeros(timeBuffer)
timedData["forceCommand"]= np.zeros(timeBuffer)

#Create a grid layout to manage the widgets size and position
layout=QtWidgets.QGridLayout()

mainWidget.setLayout(layout)

#Add widgets to the layout in their proper positions
#row, column, rowSpan, columnSpan

layout.addWidget(timedPlot, 0, 0, 1, 2)



# Legend timed datea
legend = pg.LegendItem(offset=(30, 0))
legend.setParentItem(timedPlot.graphicsItem())
for key, curve in timedCurves.items():
    legend.addItem(curve, key)

# Create control sliders
##############################
# Position Command Slider
posCommandLabel = QtWidgets.QLabel("Position Command: 0")
posCommandSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
posCommandSlider.setMinimum(0)
posCommandSlider.setMaximum(255)
posCommandSlider.setValue(0)

# Speed Command Slider
speedCommandLabel = QtWidgets.QLabel("Speed Command: 0")
speedCommandSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
speedCommandSlider.setMinimum(0)
speedCommandSlider.setMaximum(255)
speedCommandSlider.setValue(0)
speedCommandSlider.setEnabled(False)

# Force Command Slider
forceCommandLabel = QtWidgets.QLabel("Force Command: 0")
forceCommandSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
forceCommandSlider.setMinimum(0)
forceCommandSlider.setMaximum(255)
forceCommandSlider.setValue(0)
forceCommandSlider.setEnabled(False)

# Add control sliders
layout.addWidget(posCommandLabel, 1, 0, 1, 1)
layout.addWidget(posCommandSlider, 1, 1, 1, 1)
layout.addWidget(speedCommandLabel, 2, 0, 1, 1)
layout.addWidget(speedCommandSlider, 2, 1, 1, 1)
layout.addWidget(forceCommandLabel, 3, 0, 1, 1)
layout.addWidget(forceCommandSlider, 3, 1, 1, 1)

# Update label when slider changes
def update_posCommand_label(value):
    posCommandLabel.setText(f"Position Command: {value}")

def update_speedCommand_label(value):
    speedCommandLabel.setText(f"Speed Command: {value}")

def update_forceCommand_label(value):
    forceCommandLabel.setText(f"Force Command: {value}")

posCommandSlider.valueChanged.connect(update_posCommand_label)
speedCommandSlider.valueChanged.connect(update_speedCommand_label)
forceCommandSlider.valueChanged.connect(update_forceCommand_label)

################################################################
#
# DATA
#
#################################################################



#################################################################
#
# MAIN PROGRAM
#
#################################################################

def updateData(data, value):
        data[:-1] = data[1:]  # Shift the y_data array by one position
        data[-1] = value  # Add the new value at the last position



# Real-time data generation
def loop():
    global maxComTime
    global minComTime
    global timedData
    global timedCurves

    #Loop duration
    now =time.time()
    duration = now-timedData["time"][-1]
    if duration > maxComTime:
        maxComTime=np.round(duration,3)
    if duration < minComTime:
        minComTime = np.round(duration,3)
    
    #Update time

    #Calculate predicted position
    previousPos = timedData["calculatedPos"][-1]
    previousPosRequest = timedData["posRequest"][-1]
    previousPosDelta = previousPosRequest - previousPos
    
    previousDirection = np.sign(previousPosDelta)
    previousSpeed= timedData["speedCommand"][-1]
    motion = int(previousDirection * (GRIPPER_VMIN + (GRIPPER_VMAX - GRIPPER_VMIN) * previousSpeed / 255) * duration)
    #print(previousPosDelta," ",motion)
    
    newPos = 0

    if abs(previousPosDelta) < abs(motion):
        newPos = previousPosRequest
    else:
        newPos = previousPos + motion
    if newPos<3:
        newPos=3
    if newPos>228:
        newPos=228

    #Calculate new speed
    newPosRequest = posCommandSlider.value()
    newPosDelta = newPosRequest - newPos

    #Calcualte new position command
    newPosCommand = int(newPosRequest)

    newSpeedCommand= int(abs(newPosDelta*speedFactor))
    if newSpeedCommand>255:
        newSpeedCommand=int(255)
    
    force=0
    if previousPosRequest != newPosRequest:
        if newPosRequest <3 and previousPosRequest>=3:
            force=255
        elif newPosRequest >228 and previousPosRequest<=228:
            force=255
        elif newPosRequest >=3 and newPosRequest <=228:
            if (previousPosRequest<3 or previousPosRequest>228):
                force=255
            else:
                force=0

    client.write_register(address=0, value=newPosRequest)
    
    #print(newData["calculatedPos"])
    
    
    #gripper.writeSF(speedCommandSlider.value(),forceCommandSlider.value()) 

    updateData(timedData["time"], now)
    updateData(timedData["calculatedPos"], newPos)
    updateData(timedData["posRequest"], newPosRequest)
    updateData(timedData["speedCommand"], newSpeedCommand)
    updateData(timedData["forceCommand"], force)

    speedCommandSlider.setValue(newSpeedCommand)
    forceCommandSlider.setValue(force)

    #updateData(timedData["currentPos"], gripper.currentPos())


    timedCurves["calculatedPos"].setData(timedData["time"]-now, timedData["calculatedPos"])
    timedCurves["posRequest"].setData(timedData["time"]-now, timedData["posRequest"])
    #timedCurves["posCommand"].setData(timedData["time"]-now, timedData["posCommand"])
    timedCurves["speedCommand"].setData(timedData["time"]-now, timedData["speedCommand"])
    #timedCurves["currentPos"].setData(timedData["time"]-now, timedData["currentPos"])



    #filter position commands
    t=timedData["time"]-now
    p=timedData["posRequest"]

    fs=500
    t_uniform = np.arange(-5, 0, 1/fs)

    # interpolate
    interp = interpolate.interp1d(t, p, kind='linear', fill_value="extrapolate")
    p_uniform = interp(t_uniform)

    # low-pass Butterworth filter
    cutoff = 2  # Hz
    b, a = signal.butter(4, cutoff / (0.5 * fs), btype='low')
    p_filtered = signal.filtfilt(b, a, p_uniform)

    #t_uniform=t_uniform[int(0.5*fs):-int(0.5*fs)]
    #p_filtered=p_filtered[int(0.5*fs):-int(0.5*fs)]
    


    t_square=t[t>-0.5]
    p_square=p[-len(t_square):]
    #print(len(t_square)," , " ,len(p_square))

    




    A = np.vstack([t_square, np.ones(len(t_square))]).T
    m, c = np.linalg.lstsq(A, p_square)[0]

    c3=find_intercept(t_uniform[-int(0.5*fs)],p_filtered[-int(0.5*fs)],m)

    p_filtered[t_uniform>-0.5]=m*t_uniform[t_uniform>-0.5]+c3

    timedCurves["filteredPosRequest"].setData(t_uniform, p_filtered)

    
    zeroZone=10

    m2=0
    if m > GRIPPER_VMAX:
        m2=GRIPPER_VMAX
    elif (m>GRIPPER_VMIN) and (m<=GRIPPER_VMAX):
        m2=m
    elif (m>zeroZone) and (m<=GRIPPER_VMIN):
        m2=GRIPPER_VMIN
    elif (m>-zeroZone) and (m<=zeroZone):
        m2=0
    elif (m>-GRIPPER_VMIN) and (m<=-zeroZone):
        m2=-GRIPPER_VMIN
    elif (m>-GRIPPER_VMAX) and (m<=-GRIPPER_VMIN):
        m2=m
    else:
        m2=-GRIPPER_VMAX
    
    
    c2=find_intercept(0,m*(0) + c,m2)
    
    t_line = np.arange(0, 1, 1/fs)
    p_line = m2*t_line + c2

    timedCurves["linePosCommand"].setData(t_line, p_line)








# Create a timer for regular updates
timer = pg.QtCore.QTimer()
timer.timeout.connect(lambda: loop())
timer.start(1)  # Refresh rate in milliseconds (500Hz)


# Show the window
mainWindow.show()
mainWindow.raise_()
mainWindow.activateWindow()
mainWindow.showFullScreen()

# Start the application event loop
if __name__ == '__main__':
    sys.exit(app.exec_())

#################################################################
#
# CLOSING
#
#################################################################

sys.stdout.write("\rComplete!\n")

