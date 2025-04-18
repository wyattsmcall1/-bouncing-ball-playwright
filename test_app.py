# Unit tests for server-side WebTransport + WebRTC logic

import pytest
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock, patch
from server.app import WebTransportProtocol
from aiortc import RTCSessionDescription
from aioquic.h3.events import HeadersReceived
from aioquic.quic.events import StreamDataReceived

def init_protocol(app_ctx):
    """Helper to create and initialize WebTransportProtocol with _http mocked."""
    dummy_quic = MagicMock()
    dummy_quic.configuration.is_client = False
    dummy_quic._quic_logger = None

    protocol = WebTransportProtocol(quic=dummy_quic, stream_handler=None, app_ctx=app_ctx)
    protocol.connection_made(MagicMock())  # triggers _http = H3Connection(...)
    protocol._http.send_data = AsyncMock()
    protocol._http.send_headers = AsyncMock()
    return protocol

@pytest.mark.asyncio
async def test_handle_coords():
    protocol = init_protocol({"ground_truth": (320, 240)})
    stream_id = 2
    coords_msg = json.dumps({"type": "coords", "x": 310, "y": 230}).encode()

    await protocol.handle_stream_data(stream_id, coords_msg)

    protocol._http.send_data.assert_awaited_once()
    args = protocol._http.send_data.call_args.args
    assert args[0] == stream_id
    assert json.loads(args[1].decode()) == {"type": "error", "error_x": 10, "error_y": 10}

@pytest.mark.asyncio
async def test_process_offer():
    protocol = init_protocol({"fps": 5, "duration": 1})

    with patch("server.app.RTCPeerConnection") as MockPC:
        mock_pc = MockPC.return_value
        mock_pc.createAnswer = AsyncMock(return_value=RTCSessionDescription(sdp="dummy_sdp", type="answer"))
        mock_pc.setLocalDescription = AsyncMock()
        mock_pc.setRemoteDescription = AsyncMock()
        mock_pc.getSenders.return_value = []
        mock_pc.localDescription = RTCSessionDescription(sdp="dummy_sdp", type="answer")
        mock_pc.sctp.transport.iceGatherer.getLocalCandidates.return_value = []

        offer_msg = {"type": "offer", "sdp": "v=0..."}
        await protocol.process_offer(stream_id=3, message=offer_msg)

        protocol._http.send_data.assert_awaited_once()
        sent = json.loads(protocol._http.send_data.call_args.args[1].decode())
        assert sent["type"] == "answer"
        assert "sdp" in sent

@pytest.mark.asyncio
async def test_handle_event_connect():
    protocol = init_protocol({})
    protocol._sessions = set()

    connect_event = HeadersReceived(
        stream_id=7,
        headers=[
            (b":method", b"CONNECT"),
            (b":protocol", b"webtransport"),
            (b":path", b"/webtransport"),
            (b":authority", b"127.0.0.1")
        ],
        stream_ended=False
    )

    await protocol.handle_event(connect_event)

    assert 7 in protocol._sessions
    protocol._http.send_headers.assert_awaited_once()
    headers = dict(protocol._http.send_headers.call_args.args[1])  # args[1] = 
    assert headers[b":status"] == b"200"
