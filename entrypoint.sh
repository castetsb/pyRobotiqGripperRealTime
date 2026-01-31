#!/bin/sh
set -e

echo "Container args: $@"

if echo "$@" | grep -q -- "--hmi"; then
    echo "HMI enabled → starting GUI stack"

    # Start X server
    Xvfb :1 -screen 0 1280x800x16 &
    sleep 0.5

    export DISPLAY=:1
    echo "DISPLAY=$DISPLAY"

    # Start window manager
    fluxbox &
    sleep 0.5

    # Start VNC server
    x11vnc -forever -shared -rfbport 5900 -display :1 &
    sleep 0.5
else
    echo "Headless mode (no GUI)"
fi

# IMPORTANT: Python must inherit DISPLAY
exec python ./main.py "$@"
