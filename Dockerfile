FROM python:3.14.2

WORKDIR /app


COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./app /app

EXPOSE 502/tcp

ENTRYPOINT [ "python", "./main.py" ]
#CMD [ "--host", "0.0.0.0", "--port", "502" ]

#Docker command to build the image
#docker build -t modbus-tcp-server:latest .

#Docker command to get help
#docker run --rm -t modbus-tcp-server:latest --help


#Docker command to run with a device connected on docker PC serial
#docker run --rm -t --device=/dev/ttyUSB0:/dev/ttyUSB0 -p 502:502 modbus-tcp-server:latest --method "RTU" --gripper_id 9 --gripper_port "/dev/ttyUSB0"

#Docker command to run with a device on a UR robot wrist with toolcomm URCAP tunnelling serial to ethernet (change IP for robot IP)
#docker run --rm -t -p 502:502 modbus-tcp-server:latest --method "RTU_VIA_TCP" --gripper_port 54321 --gripper_IP 10.0.0.80