FROM python:3.14.2

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libx11-6 \
    libx11-xcb1 \
    libxrender1 \
    libxi6 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libxcursor1 \
    libsm6 \
    libfontconfig1 \
    libxcomposite1 \
    libxdamage1 \
    python3-pyqt5 \
    xvfb \
    x11vnc \
    fluxbox \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./app /app
COPY ./entrypoint.sh /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

EXPOSE 502/tcp
EXPOSE 5900

ENTRYPOINT ["/app/entrypoint.sh"]