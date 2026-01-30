====================
pyRobotiqGripperRealtime
====================

This python application is designed to control a Robotiq gripper(2F85, 2F140 or hand) by sending position command in Modbus TCP at high frequency.

Requirements:
============

- If the PC is running windows: install wsl (https://learn.microsoft.com/en-us/windows/wsl/install)
- Install and run docker on the PC where you want to install the application (https://www.docker.com/get-started/)

How to use
============

.. code-block:: text

    Modbus TCP client  (500 Hz)
            |Modbus TCP command
            |Write gripper position request in register 0
            v
    Modbus TCP Server (500+ Hz)
            |Gripper command (50hz)
            |Over ethernet
            v
    ROBOTIQ URCAP (port 63352)
            |Modbus RTU command
            v
    Gripper at robot wrist

1- Install Robotiq gripper URCAP on the robot

2- Copy repository files in a folder on your PC.

3- Open a terminal and navigate to this folder.

4- Run docker command to build the docker image.

.. code-block:: bash

    docker build -t modbus-tcp-server:latest .

5- Run the docker image and pass the IP of the robot. In the following example the robot IP is 10.0.0.80. When the docker image start, the gripper will open and close to complete its activation procedure. Make sure nothing interfer with the motion of the gripper.

.. code-block:: bash

    docker run --rm -t -p 502:502 modbus-tcp-server:latest --robot_IP 10.0.0.80

By default the Modbus tcp server is accessible via 502 port. You can change for another port if you want. The following modification would give the Modbus tcp server accessible via 1050 port.
ex: -p 1050:502

6- Write realtime position request in Modbus tcp server register 0

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

The thread, which is monitoring the position request, sends appropriate gripper command through ethernet to the Robotiq URCAP installed on the robot.

The monitoring thread only forwards meaningful position requests. For example if the same position is requested at 500Hz the thread we send only 1 position request to the gripper. This prevent from overloading the gripper Modbus RTU communication which is not designed to handle high-frequency commands.

CAUTION
============

This application is a kind of prototype. It would need to be tested to make sure it is stable. Use at your own risks.
I hope the code of this application will help you to make your own realtime application.