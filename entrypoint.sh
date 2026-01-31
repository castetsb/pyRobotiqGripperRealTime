#!/bin/sh
set -e

echo "Container args: $@"

if echo "$@" | grep -q -- "--hmi"; then
    echo "HMI enabled → starting GUI stack"

    Xvfb :1 -screen 0 1280x800x16 &
    sleep 1

    export DISPLAY=:1
    export QT_QPA_PLATFORM=xcb

    fluxbox &
    sleep 2   # ⬅ IMPORTANT

    x11vnc -forever -shared -rfbport 5900 -display :1 &
    sleep 1
else
    echo "Headless mode (no GUI)"
fi

exec python ./main.py "$@"
