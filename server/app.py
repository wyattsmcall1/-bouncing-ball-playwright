# Entry point for the QUIC+WebTransport server (serves HTML and video)

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import ssl
import json
import asyncio
import logging
import argparse
import multiprocessing as mp
import traceback

from aioquic.asyncio import QuicConnectionProtocol, serve
from aioquic.h3.connection import H3Connection
from aioquic.h3.events import HeadersReceived, DataReceived
from aioquic.quic.events import ProtocolNegotiated, StreamDataReceived
from aioquic.quic.configuration import QuicConfiguration
from aioquic.h3.connection import H3_ALPN
from OpenSSL import crypto
import hashlib
from aiortc import RTCPeerConnection, RTCSessionDescription

from video_track import BouncingBallTrack
from frame_worker import FrameProducer
import contextlib

pcs = set()

from aiohttp import web

async def serve_http():
    app = web.Application()

    # Explicit route for "/"
    app.router.add_get("/", lambda req: web.FileResponse(
        os.path.join(os.path.dirname(__file__), "static/index.html")
    ))

    # Static files
    app.router.add_static("/", path=os.path.join(os.path.dirname(__file__), "static"), show_index=True)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=8000)
    await site.start()
    print("[DEBUG] HTTP server running on http://0.0.0.0:8000")

class WebTransportProtocol(QuicConnectionProtocol):
    def __init__(self, *args, app_ctx=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._sessions = set()
        self.app_ctx = app_ctx
        self._http = None

    def connection_made(self, transport):
        super().connection_made(transport)
        self._http = H3Connection(self._quic, enable_webtransport=True)

    def quic_event_received(self, event):
        print("[DEBUG] Received QUIC event:", type(event).__name__)
        if isinstance(event, ProtocolNegotiated):
            print(f" ALPN negotiated: {event.alpn_protocol}")
        if isinstance(event, StreamDataReceived):
            print(f"[DEBUG] StreamDataReceived: stream_id={event.stream_id}, session_ids={self._sessions}")
            # Add this:
            if not self._sessions:
                print("[ERROR] No WebTransport sessions accepted yet!")
            if event.stream_id in self._sessions:
                print("[DEBUG] Dispatching stream data to handle_stream_data")
                asyncio.ensure_future(self.handle_stream_data(event.stream_id, event.data))
            else:
                print("[DEBUG] Ignoring non-WebTransport stream:", event.stream_id)

        try:
            for http_event in self._http.handle_event(event):
                asyncio.ensure_future(self.handle_event(http_event))
        except Exception as e:
            print("[ERROR] Failed to handle HTTP/3 event:", e)

    async def handle_event(self, event):
        print(f"[DEBUG] handle_event called: {event}")
        if isinstance(event, HeadersReceived):
            headers = dict(event.headers)
            print("[DEBUG] HeadersReceived:", headers)
            method = headers.get(b":method", b"").decode()
            protocol = headers.get(b":protocol", b"").decode()
            authority = headers.get(b":authority", b"").decode()

            if method == "CONNECT" and protocol == "webtransport":
                stream_id = event.stream_id
                print(f"[QUIC] Accepted WebTransport session on stream {stream_id} from {authority}")
                self._sessions.add(stream_id)
                await self._http.send_headers(stream_id, [
                    (b":status", b"200"),
                    (b"sec-webtransport-http3-draft", b"draft02"),
                    (b"access-control-allow-origin", b"*")
                ])
                self._quic.send_stream_data(stream_id, b"", end_stream=False)
            else:
                print(f"[WARN] Rejected stream {event.stream_id}: method={method}, protocol={protocol}")
                self._http.send_headers(event.stream_id, [(b":status", b"400")])

    async def handle_stream_data(self, stream_id, data):
        try:
            print(f"[DEBUG] Raw stream data on stream {stream_id}: {data!r}")
            message = json.loads(data.decode())
            print("[DEBUG] Stream data received:", message)
            if message.get("type") == "offer":
                await self.process_offer(stream_id, message)
            elif message.get("type") == "coords":
                cx, cy = message["x"], message["y"]
                tx, ty = self.app_ctx.get("ground_truth", (320, 240))
                error = {"type": "error", "error_x": tx - cx, "error_y": ty - cy}
                await self._http.send_data(stream_id, json.dumps(error).encode(), end_stream=False)
                print("[DEBUG] Sent SDP answer to stream", stream_id)
        except Exception as e:
            print("[ERROR] Failed to handle stream data:", e)

    async def process_offer(self, stream_id, message):
        print("[DEBUG] Received offer with SDP length:", len(message.get("sdp", "")))
        pc = RTCPeerConnection()
        pcs.add(pc)
        await pc.setRemoteDescription(RTCSessionDescription(sdp=message["sdp"], type=message["type"]))

        frame_queue = mp.Queue(maxsize=2)
        stop_event = mp.Event()
        producer = FrameProducer(frame_queue, fps=self.app_ctx["fps"], stop_event=stop_event, duration=self.app_ctx["duration"], debug=True)
        producer.start()

        track = BouncingBallTrack(frame_queue, fps=self.app_ctx["fps"])
        pc.addTransceiver("video", direction="sendonly")  # <-- add this
        pc.addTrack(track)
        print("[SERVER] Track added to peer connection.")
        print("[DEBUG] pc.addTrack(track) completed")

        @pc.on("connectionstatechange")
        def on_state_change():
            print(f"[SERVER] WebRTC state: {pc.connectionState}")
            if pc.connectionState == "connected":
                print("[SERVER] WebRTC connection established.")

        # Optionally log if anything is received (not expected in sendonly mode)
        @pc.on("track")
        def on_track(track):
            print(f"[SERVER] Unexpected incoming track: kind={track.kind}")

        print("[DEBUG] Creating and setting local description")
        await pc.setLocalDescription(await pc.createAnswer())
        await asyncio.sleep(0.1)
        print("[DEBUG] pc.setLocalDescription() completed")
        print("[SERVER] Local description set.")

        response = {
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type
        }
        await self._http.send_data(stream_id, json.dumps(response).encode(), end_stream=False)

async def run_app():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--duration", type=int, default=10)
    parser.add_argument("--fps", type=int, default=10)
    parser.add_argument("--cert", type=str, default="localhost.pem")
    parser.add_argument("--key", type=str, default="localhost-key.pem")
    args = parser.parse_args()

    config = QuicConfiguration(is_client=False, alpn_protocols=H3_ALPN)
    config.load_cert_chain(args.cert, args.key)
    config.support_webtransport = True
    config.max_datagram_frame_size = 65536

    with open(args.cert, "r") as f:
        x509 = crypto.load_certificate(crypto.FILETYPE_PEM, f.read())
        pubkey = x509.get_pubkey()
        pub_der = crypto.dump_publickey(crypto.FILETYPE_ASN1, pubkey)
        spki_hash = hashlib.sha256(pub_der).hexdigest()
        print(f"[DEBUG] SPKI Fingerprint: {spki_hash}")

    app_ctx = {
        "duration": args.duration,
        "fps": args.fps
    }

    print(f"[DEBUG] Starting HTTP server on http://{args.host}:8000")
    print(f"QUIC server running on https://{args.host}:{args.port}")

    http_task = asyncio.create_task(serve_http())
    print("[DEBUG] Created HTTP Task", flush=True)
    quic_task = asyncio.create_task(serve(
        host=args.host,
        port=args.port,
        configuration=config,
        create_protocol=lambda *a, **kw: WebTransportProtocol(*a, app_ctx=app_ctx, **kw)
    ))
    print("[QUIC LOG] QUIC server running", flush=True)

    try:
        await asyncio.sleep(args.duration + 5)
    finally:
        http_task.cancel()
        quic_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await http_task
            await quic_task

if __name__ == "__main__":
    asyncio.run(run_app())
