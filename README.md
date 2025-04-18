# Bouncing Ball Tracker Challenge (with Kubernetes Deployment)

This project simulates a bouncing ball rendered using OpenCV and streams it using WebRTC/WebTransport to a browser for real-time tracking and error feedback. It supports containerized testing with Docker, GUI via X11, and full deployment on Kubernetes using Minikube.

---

## Project Structure

```
.
├── Dockerfile                  # Defines the container image used for local and Kubernetes deployment
├── bouncing_ball.py           # Ball physics logic for standalone simulation
├── frame_worker.py            # Multiprocessing class that generates video frames in a background process
├── video_track.py             # WebRTC-compatible video stream track that serves frames from the queue
├── launch_minikube.bash       # Launches the full stack on Minikube (build + deploy + expose)
├── launch_playwright_server.bash  # Launches server + headful Chromium browser inside Docker
├── launch_playwright_server_interactive.py  # Launch logic for server and browser using Playwright
├── main_ball_test.py          # Runs standalone OpenCV-based ball simulation
├── main_worker_test.py        # Tests only the multiprocessing frame producer
├── main_video_test.py         # Runs full video pipeline: producer + viewer
├── test_app.py                # Unit tests for server-side WebTransport + WebRTC logic
├── test_index.py              # End-to-end tests for WebRTC/WebTransport using Chromium inside Docker
├── test_bouncing_ball.py      # Unit test for bouncing ball physics
├── test_frame_worker.py       # Unit test for multiprocessing frame producer
├── test_video_track.py        # Unit test for the video stream wrapper
├── requirements.txt           # Python dependencies for server and tests
├── pytest.ini                 # Pytest configuration file
├── localhost.pem              # TLS certificate generated via mkcert
├── localhost-key.pem          # TLS private key generated via mkcert
├── k8s/
│   ├── deployment.yaml        # Kubernetes Deployment spec for the server pod
│   └── service.yaml           # Kubernetes Service for exposing HTTP + QUIC
└── server/
    ├── app.py                 # Entry point for the QUIC+WebTransport server (serves HTML and video)
    └── static/
        └── index.html         # Browser frontend for video playback and WebTransport handshake
```

---

## Docker Environment Setup

### 1. Build Docker Image

```bash
docker build -t bouncing-ball-playwright .
```

### 2. Set DISPLAY Variable (macOS/Linux)

```bash
export IP=$(ifconfig en0 | grep inet | awk '$1=="inet" {print $2}')
xhost + $IP
```

---

## Running Tests and Simulations

### `test_index.py` — End-to-end test of browser and QUIC server

```bash
docker run -it --rm   -e DISPLAY=$IP:0   -v /tmp/.X11-unix:/tmp/.X11-unix   -v "$(pwd)/output":/app/tests/output   bouncing-ball-playwright   pytest test_index.py -s -v
```

### `main_ball_test.py` — OpenCV-only ball simulation

```bash
docker run -it --rm   -e DISPLAY=$IP:0   -v /tmp/.X11-unix:/tmp/.X11-unix   -v "$(pwd)/output":/app/output   bouncing-ball-playwright   python3 main_ball_test.py --fps 30 --duration 5
```

### `main_worker_test.py` — Frame generation test via worker process

```bash
docker run -it --rm   -e DISPLAY=$IP:0   -v /tmp/.X11-unix:/tmp/.X11-unix   -v "$(pwd)/output":/app/output   bouncing-ball-playwright   python3 main_worker_test.py --fps 30 --duration 5
```

### `main_video_test.py` — Full pipeline test with multiprocessing + OpenCV render

```bash
docker run -it --rm   -e DISPLAY=$IP:0   -v /tmp/.X11-unix:/tmp/.X11-unix   -v "$(pwd)/output":/app/output   bouncing-ball-playwright   python3 main_video_test.py --fps 30 --duration 5
```

### `test_app.py` — Isolated server test without browser

```bash
docker run -it --rm   -e DISPLAY=$IP:0   -v /tmp/.X11-unix:/tmp/.X11-unix   -p 8000:8000 -p 8080:8080   bouncing-ball-playwright   pytest test_app.py -s -v
```

---

## Output Files

- Saved to `output/` directory.
- Available as individual frames or videos depending on flags.

---

## Kubernetes Deployment with Minikube

### Prerequisites

- Minikube
- Docker
- `kubectl` CLI

---

### Launch Instructions

#### 1. Start Minikube

```bash
minikube start --driver=docker
```

#### 2. Point Docker to Minikube

```bash
eval $(minikube docker-env)
```

#### 3. Build Docker Image in Minikube

```bash
docker build -t bouncing-ball-playwright .
```

#### 4. Apply Kubernetes Manifests

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

#### 5. Verify

```bash
kubectl get pods
```

#### 6. Access the UI

```bash
minikube service bouncing-ball-service
```

---

### Cleanup

```bash
kubectl delete -f k8s/
minikube stop
```

---

## Minikube Launch Script

You can automate everything with:

```bash
chmod +x launch_minikube.sh
./launch_minikube.sh
```

This will build the image, apply Kubernetes resources, and give you the public URL.

---

## Design Decisions

To keep the testing and deployment process agile and unified, this project uses **Playwright with Chromium** inside the Docker container. This enables:

- **Headful browser automation** within the container stack, avoiding host-browser synchronization issues on macOS and Linux.
- **Isolated unit testing** of backend and frontend logic:
  - `test_app.py` tests the `app.py` server logic (WebTransport/WebRTC) independently.
  - `test_index.py` tests the frontend `index.html` behavior and its integration with the server.

This modular design helps identify and debug issues in isolation before verifying end-to-end behavior.

### Directly Launch the Server with Playwright

You can run the WebTransport+WebRTC server directly inside the container (without running `test_index.py`) using:

```bash
./launch_playwright_server.sh
```

---

## Known Issues

Some features are partially implemented due to time constraints. Please see [known_issues.md](known_issues.md) for a full list of limitations and workarounds.

---

## Notes

- The GUI requires X11 (e.g., XQuartz on macOS).
- mkcert is used for local TLS.
- QUIC runs over port 8080. HTTP over 8000.
- Use supported browsers (Chromium, Chrome) with WebTransport.
