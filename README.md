pyRobotiqGripperRealtime
========================
This python application is made to control in realtime a robotiq gripper like 2F85, 2F140 or ePick connected at the wirst of a UR robot from a remote PC.

Requirements:
=============
- The RS485 URCAP needs to be installed on the UR robot. See the following documentation:
https://github.com/UniversalRobots/Universal_Robots_ToolComm_Forwarder_URCap
- Install docker on the PC where you want to install the application

How to use it ?
===============
1- Copy repository files in a folder on your PC.
2- Open a terminal and navigate to this folder.
3- Run docker command to build the docker image.

.. code-block:: bash

    docker build -t modbus-tcp-server:latest .

4- Run the docker image and pass the IP of the robot. In the following example the robot IP is 10.0.0.80.

.. code-block:: bash

    docker run --rm -t -p 502:502 modbus-tcp-server:latest --gripper_IP 10.0.0.80

By default the modbus tcp server is accessible via 502 port. You can change for another port if you want. The following modification would give the modbus tcp server accessible via 1050 port.
ex: -p 1050:502

5- Write realtime position request in modbus tcp server register 0

Here below is an example of python script to send a position request to the modbus TCP server.

.. code-block:: python

    from pymodbus.client import ModbusTcpClient
    client = ModbusTcpClient("127.0.0.1", port=502)
    client.connect()
    client.write_register(address=0, value=position)

The concept
============
The application consist of:
- A modbus TCP server on which is save the realtime position request of the gripper at register 0
- A thread that monitor the realtime position request of the modbus TCP server and send appropriate command to the gripper conected at the wrist of the robot.

Both are packaged into a docker container to ease implementation.

The modbus TCP server can receive position request at high frequency similar to UR RTDE (500Hz). So you can send realtime position request at 500Hz.

The thread, which is monitoring the position request, sends appropriate modbus RTU command over ethernet to the UR robot ethernet port 54321. The URCAP RS485 installed on the robot get the modbus request at port 54321 and send it to the gripper via robot wrist serial.

The thread send position request which are meaning full. For example if the same position is requested at 500Hz the thread we send only 1 position request to the gripper. This prevent from overloading the gripper with unnecessary communication.

CAUTION
=======
This application is a kind of prototype. It would need to be tested to make sure it is stable. Use at your own risks.