#################################################################
#
# LIBRARIES
#
#################################################################
import sys
import numpy as np
from PyQt5 import QtWidgets
import pyqtgraph as pg
from pyqtgraph import QtCore
import time
from pymodbus.client import ModbusTcpClient
from commandFilter import *

def updateData(data, value):
    data[:] = np.roll(data, -1)
    data[-1] = value
#################################################################
#
# Variables
#
#################################################################

#Number of value in buffer

timeBuffer=1000

timedData={}
timedData["time"]= np.ones(timeBuffer) * time.monotonic()
timedData["toExecute"] = np.zeros(timeBuffer)
timedData["posRequest"]= np.zeros(timeBuffer)
timedData["pos"]= np.zeros(timeBuffer)
timedData["speed"]= np.zeros(timeBuffer)
timedData["force"]= np.zeros(timeBuffer)

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

#Main widget
mainWidget=QtWidgets.QWidget()
mainWindow.setCentralWidget(mainWidget)

# Set up the timed data plot
##############################
timedPlot = pg.PlotWidget()#win.addPlot(title="Last 5s events",row=1,col=0)
timedPlot.setRange(yRange=[0,255],xRange=[-5,0])
timedPlot.showGrid(True, True)

#Create curves
timedCurves={}
timedCurves["posRequest"]=timedPlot.plot(pen='r')
timedCurves["toExecute"]=timedPlot.plot(pen='y')
timedCurves["currentPos"]=timedPlot.plot(pen='g')
timedCurves["speedCommand"]=timedPlot.plot(pen='b')

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

#################################################################
#
# MAIN PROGRAM
#
#################################################################

# Real-time data generation
def loop():
    newPosRequest = posCommandSlider.value()
    now=time.monotonic()
    command=commandFilter(newPosRequest,now,timedData["time"][-1],timedData["pos"][-1],timedData["posRequest"][-1],timedData["speed"][-1],timedData["force"][-1],5,110)
    posRequest = command["positionRequest"]
    pos = command["currentPosition"]
    speed = command["speedRequest"]
    force = command["forceRequest"]
    toExecute = command["toExecute"]

    client.write_register(address=0, value=newPosRequest)
    updateData(timedData["time"],now)#timedData["time"][-1]+tcp_elapsedTime/1000)
    updateData(timedData["toExecute"],toExecute)
    updateData(timedData["posRequest"],newPosRequest)
    updateData(timedData["pos"],pos)
    updateData(timedData["speed"],speed)
    updateData(timedData["force"],force)

    timedCurves["currentPos"].setData(timedData["time"]-timedData["time"][-1], timedData["pos"])
    timedCurves["posRequest"].setData(timedData["time"]-timedData["time"][-1], timedData["posRequest"])
    timedCurves["toExecute"].setData(timedData["time"]-timedData["time"][-1], timedData["toExecute"]*125)
    timedCurves["speedCommand"].setData(timedData["time"]-timedData["time"][-1], timedData["speed"])

    speedCommandSlider.setValue(int(timedData["speed"][-1]))
    forceCommandSlider.setValue(int(timedData["force"][-1]))

# Create a timer for regular updates
timer = pg.QtCore.QTimer()
timer.timeout.connect(lambda: loop())
timer.start(2)  # Refresh rate in milliseconds (500Hz)

# Show the window
mainWindow.show()
mainWindow.raise_()
mainWindow.activateWindow()
mainWindow.showMaximized()
#mainWindow.showFullScreen()

# Start the application event loop
if __name__ == '__main__':
    sys.exit(app.exec_())

#################################################################
#
# CLOSING
#
#################################################################

sys.stdout.write("\rComplete!\n")