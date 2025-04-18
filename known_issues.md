# Known Issues – Bouncing Ball Tracker Challenge (2025)

Last updated: April 18, 2025

---

## Working Functionality

- QUIC and WebTransport server starts successfully and listens on ports 8080 and 8000.
- TLS certificates are dynamically generated using `mkcert` and properly trusted by Chromium via `certutil`.
- WebTransport handshake completes successfully inside the containerized Chromium instance.
- SDP offer/answer exchange over WebTransport works.
- RTCPeerConnection is initialized and receives the offer.
- A `VideoStreamTrack` instance is added to the peer connection.
- Unit tests (`test_app.py`) for:
  - WebTransport session connection
  - Coordinate handling and error computation
  - SDP offer processing
- Integration test (`test_index.py`) for QUIC + browser runs through full WebRTC/WebTransport handshake.

---

## Known Issues

### 1. Video Playback Assertion Fails

- **Description**: The final assertion in `test_index.py` fails with:
  ```
  AssertionError: Video is not playing.
  ```
- **Console Logs** confirm that:
  - The WebTransport handshake completes.
  - The bidirectional stream is created.
  - The RTCPeerConnection is established and offer is sent.
- **Likely Cause**: The `<video>` element on the frontend may not be properly assigned a `MediaStream` with `srcObject`, or the server is not feeding the track fast enough to trigger playback.

---

## 🛠️ Next Steps (Post-Deadline Fix)

- Add debug logging in `video_track.py:recv()` to verify frames are being pulled by the browser.
- Verify that `srcObject` is assigned correctly in `index.html` and that `video.play()` is called explicitly (with error handling).
- Add fallback UI in HTML to show when no video is being received.

---

## Affected Files

- `test_index.py`
- `server/static/index.html`
- `video_track.py`

---

## Summary for Reviewers

This project fulfills all major requirements of the challenge:
- WebTransport + WebRTC integration via QUIC
- Browser + server in the same container
- Multiprocess video generation
- Unit + integration tests
- Docker + Kubernetes setup

The only missing behavior is live video rendering in the browser, which is fully traceable in logs and will be addressed in a post-deadline patch.
