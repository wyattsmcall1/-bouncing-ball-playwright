# Bouncing Ball Tracker Challenge

This project simulates a bouncing ball rendered using OpenCV, and streams it using WebRTC/WebTransport to a browser for real-time tracking and error feedback. The app is containerized with Docker and supports GUI display via X11 forwarding.

---

## Environment Setup

### 1. Build Docker Image

```bash
docker build -t bouncing-ball-playwright .
```

### 2. Set DISPLAY Variable

On macOS with XQuartz or Linux with X11, set the display environment:

```bash
export IP=$(ifconfig en0 | grep inet | awk '$1=="inet" {print $2}')
```

Then allow connections:

```bash
xhost + $IP
```

---

## Running Tests and Simulations

All tests below assume you're in the project root and have already built the Docker image.

### test_index.py

Launches a Chromium browser inside Docker and runs an end-to-end test of the WebTransport + WebRTC handshake and video streaming.

```bash
docker run -it --rm \
  -e DISPLAY=$IP:0 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "$(pwd)/output":/app/tests/output \
  bouncing-ball-playwright \
  pytest test_index.py -s -v
```

---

### main_ball_test.py

Simulates a bouncing ball and renders directly using OpenCV.

Arguments:
- `--duration`: Simulation duration in seconds (default: 5.0)
- `--fps`: Frames per second (default: 30)
- `--output`: Output directory (default: output)
- `--video`: Save as video (default: True)

Run:

```bash
docker run -it --rm \
  -e DISPLAY=$IP:0 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "$(pwd)/output":/app/output \
  bouncing-ball-playwright \
  python3 main_ball_test.py --fps 30 --duration 5
```

---

### main_worker_test.py

Tests the FrameProducer multiprocessing class that generates frames.

Arguments:
- `--duration`: Simulation duration (seconds)
- `--fps`: Frames per second
- `--output`: Output directory
- `--video`: Save as video instead of individual frames

Run:

```bash
docker run -it --rm \
  -e DISPLAY=$IP:0 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "$(pwd)/output":/app/output \
  bouncing-ball-playwright \
  python3 main_worker_test.py --fps 30 --duration 5
```

---

### main_video_test.py

Runs a full simulation using the multiprocessing worker and renders the output.

Arguments:
- `--duration`: Simulation duration (seconds)
- `--fps`: Frames per second
- `--output`: Output directory
- `--video`: Save as video instead of individual frames

Run:

```bash
docker run -it --rm \
  -e DISPLAY=$IP:0 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "$(pwd)/output":/app/output \
  bouncing-ball-playwright \
  python3 main_video_test.py --fps 30 --duration 5
```

---

### test_app.py

Launches the QUIC server and runs unit tests for WebRTC/WebTransport functionality.

```bash
docker run -it --rm \
  -e DISPLAY=$IP:0 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -p 8000:8000 -p 8080:8080 \
  bouncing-ball-playwright \
  pytest test_app.py -s -v
```

---

## Output Files

All frames and videos are saved inside `output/` (mounted at `/app/output` in the container). You can view them on your host machine after each run.

---

## Notes

- The GUI (video display) requires X11. On macOS, ensure XQuartz is running.
- Self-signed certificates are used (via mkcert) and trusted inside the browser container.
- WebTransport runs over QUIC (port 8080) and the HTML frontend is served over HTTPS (8000).

---

## Troubleshooting

- If you see a black screen, confirm X11 forwarding and mkcert trust store setup.
- If WebTransport handshake fails, ensure localhost.pem is valid and trusted.
- Use `xhost + $IP` to allow Docker to access your display.
