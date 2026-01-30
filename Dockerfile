FROM python:3.11-slim

# Install build tools and CMake
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

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


#Docker command to run the docker
#docker run --rm -t -p 502:502 modbus-tcp-server:latest --robot_IP 10.0.0.80