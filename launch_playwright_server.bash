#!/bin/bash
# Launches server + headful Chromium browser inside Docker

export IP=$(ifconfig en0 | grep inet | awk '$1=="inet" {print $2}')
xhost + $IP

docker build -t bouncing-ball-playwright .

docker run -it --rm \
  -e DISPLAY=$IP:0 \
  -e HOST_IP=127.0.0.1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "$(pwd)/output":/app/tests/output \
  bouncing-ball-playwright \
  python3 launch_playwright_server_interactive.py
