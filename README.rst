====================
pyRobotiqGripperRealtime
====================

This python application is designed to control a Robotiq gripper(2F85, 2F140 or hand) by sending position command in Modbus TCP at high frequency.

The gripper can be connected in two ways:

A- on the wrist of the UR robot (May be a bit laggy)
B- on the PC on which is install the application (Fast). The gripper is mounted at the wrist of the robot and have its communication cable routed along the arm and connected to the PC. It is actually very similar to using the Robotiq Modbus TCP universal controller.

Requirements:
============

- If the PC is running windows: install wsl (https://learn.microsoft.com/en-us/windows/wsl/install)
- Install and run docker on the PC where you want to install the application (https://www.docker.com/get-started/)

## Method A: Gripper connected at the wrist of the robot

.. code-block:: text

    Modbus TCP client  (500 Hz)
            |Modbus TCP command
            |Write gripper position request in register 0
            v
    Modbus TCP Server (500+ Hz)
            |Modbus RTU command (50hz)
            |Over ethernet
            v
    RS 485 URCAP (port 54321)
            |Modbus RTU command
            v
    Gripper at robot wrist

1- Install the RS485 URCAP on the UR robot. See the following documentation for instruction on how to install it:
https://github.com/UniversalRobots/Universal_Robots_ToolComm_Forwarder_URCap

2- Copy repository files in a folder on your PC.

3- Open a terminal and navigate to this folder.

4- Run docker command to build the docker image.

.. code-block:: bash

    docker build -t modbus-tcp-server:latest .

5- Run the docker image and pass the IP of the robot and the gripper Modbus id (default is 9). In the following example the robot IP is 10.0.0.80. When the docker image start, the gripper will open and close to complete its activation procedure. Make sure nothing interfer with the motion of the gripper.

.. code-block:: bash

    docker run --rm -t -p 502:502 modbus-tcp-server:latest --gripper_IP 10.0.0.80 --gripper_id 9 

By default the Modbus tcp server is accessible via 502 port. You can change for another port if you want. The following modification would give the Modbus tcp server accessible via 1050 port.
ex: -p 1050:502

6- Write realtime position request in Modbus tcp server register 0

Here below is an example of python script to send a position request to the Modbus TCP server.

.. code-block:: python

    from pymodbus.client import ModbusTcpClient
    client = ModbusTcpClient("127.0.0.1", port=502)
    client.connect()
    client.write_register(address=0, value=position)

Method B: Gripper connected to the PC serial port
============

.. code-block:: text

    Modbus TCP client  (500 Hz)
            |Modbus TCP command
            |Write gripper position request in register 0
            v
    Modbus TCP Server (500+ Hz)
            |Modbus RTU command (50hz)
            |Over PC serial
            v
    Gripper at PC serial port

1- Copy repository files in a folder on your PC.

2- Open a terminal and navigate to this folder.

3- Run docker command to build the docker image.

.. code-block:: bash

    docker build -t modbus-tcp-server:latest .

4- Only if the PC is running on windows:
- Install usbipd (https://github.com/dorssel/usbipd-win)
- Open window terminal ad administrator (right click on terminal application and select run as administrator)
- Excute the following command:

.. code-block:: bash

    usbipd list

This should return something like that :

.. code-block:: bash

    Connected:
    BUSID  VID:PID    DEVICE                                                        STATE
    2-1    0403:6015  USB Serial Converter                                          Attached
    2-3    2357:0604  TP-Link Bluetooth 5.3 USB Adapter                             Not shared
    2-5    0c45:6705  Integrated Webcam                                             Not shared
    2-7    04f3:0201  USB Input Device                                              Not shared
    3-6    8087:07dc  Intel(R) Wireless Bluetooth(R)                                Not shared

- Search for the busid of the usd device corresponding to the gripper. In this example "2-1".
- Share and attach the busid of the gripper with wsl using the following commant. Use the previously identified busid.

.. code-block:: bash

    busipd bind --busid 2-1
    busipd attach --wsl --busid 2-1

4- In linux terminal (If the PC use window launch linux terminal by typing wsl in windows terminal) and search for gripper device name by copy and paste the following code in the terminal:

.. code-block:: bash

    {
    printf "%-15s %-20s %-25s %s\n" DEVICE VENDOR MODEL SERIAL
    for d in /dev/ttyUSB* /dev/ttyACM*; do
        [ -e "$d" ] || continue
        VENDOR=$(udevadm info -q property -n "$d" | sed -n 's/^ID_VENDOR=//p')
        MODEL=$(udevadm info -q property -n "$d" | sed -n 's/^ID_MODEL=//p')
        SERIAL=$(udevadm info -q property -n "$d" | sed -n 's/^ID_SERIAL=//p')
        printf "%-15s %-20s %-25s %s\n" "$d" "$VENDOR" "$MODEL" "$SERIAL"
    done
    }

You should see something like that:

.. code-block:: bash

    DEVICE          VENDOR               MODEL                     SERIAL
    /dev/ttyUSB0    FTDI                 USB_TO_RS-485             FTDI_USB_TO_RS-485_DA1P5HRO

5- Run the docker image and pass the previously identified device name of the gripper. When the docker image start, the gripper will open and close to complete its activation procedure. Make sure nothing interfer with the motion of the gripper.

.. code-block:: bash

    docker run --rm -t --device=/dev/ttyUSB0:/dev/ttyUSB0 -p 502:502 modbus-tcp-server:latest --method "RTU" --gripper_id 9 --gripper_port "/dev/ttyUSB0"

By default the Modbus tcp server is accessible via 502 port. You can change for another port if you want. The following modification would give the Modbus tcp server accessible via 1050 port.
ex: -p 1050:502

5- Write realtime position request in Modbus tcp server register 0

Here below is an example of python script to send a position request to the Modbus TCP server.

.. code-block:: python

    from pymodbus.client import ModbusTcpClient
    client = ModbusTcpClient("127.0.0.1", port=502)
    client.connect()
    client.write_register(address=0, value=position)


The concept
============

The application consist of:
- A Modbus TCP server which can recieve at high frequency position request (0-255) on its register 0
- A thread that monitor the position request saved in register 0 of the Modbus server and send appropriate command (position,speed,force) to the gripper connected at the wrist of the robot.

Both are packaged into a docker container to ease implementation.

The Modbus TCP server can receive position request at high frequency similar to UR RTDE (500Hz). So you can send realtime position request at 500Hz.

The thread, which is monitoring the position request, sends appropriate Modbus RTU command over serial port (method A) or ethernet to the UR robot ethernet port 54321 (method B).

The monitoring thread only forwards meaningful position requests. For example if the same position is requested at 500Hz the thread we send only 1 position request to the gripper. This prevent from overloading the gripper Modbus RTU communication which is not designed to handle high-frequency commands.

Go further
============

It would be possible to integrate this control concept by making a URCAP which reads an RTDE register and send RTU command to the gripper connected at the wrist. RTDE is better suited for realtime control and RTU command are directly send to the gripper which would provide the smoothest communication.
The only draw back would be that such URCAP would ptentially load the robot controller processor and slow dow execution.

.. code-block:: text

    RTDE client  (500 Hz)
            |(ethernet)
            v
    RTDE to Modbus URCAP (50 Hz)
            |
            v
    Gripper at robot wrist

CAUTION
============

This application is a kind of prototype. It would need to be tested to make sure it is stable. Use at your own risks.
I hope the code of this application will help you to make your own realtime application.