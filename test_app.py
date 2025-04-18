import pytest
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock, patch
from server.app import WebTransportProtocol
from aiortc import RTCSessionDescription
from aioquic.h3.events import HeadersReceived

@pytest.mark.asyncio
async def test_handle_coords():
    dummy_quic = MagicMock()
    dummy_quic.configuration.is_client = False
    dummy_quic._quic_logger = None

    protocol = WebTransportProtocol(quic=dummy_quic, stream_handler=None, app_ctx={"ground_truth": (320, 240)})
    protocol._http.send_data = AsyncMock()

    class DummyEvent:
        stream_id = 2
        data = json.dumps({"type": "coords", "x": 310, "y": 230}).encode()

    await protocol.handle_stream_data(DummyEvent())

    protocol._http.send_data.assert_awaited_once()
    args = protocol._http.send_data.call_args.args
    assert args[0] == 2
    assert json.loads(args[1].decode()) == {"type": "error", "error_x": 10, "error_y": 10}

@pytest.mark.asyncio
async def test_process_offer():
    dummy_quic = MagicMock()
    dummy_quic.configuration.is_client = False
    dummy_quic._quic_logger = None

    protocol = WebTransportProtocol(quic=dummy_quic, stream_handler=None, app_ctx={"fps": 5, "duration": 1})
    protocol._http.send_data = AsyncMock()

    with patch("server.app.RTCPeerConnection") as MockPC:
        mock_pc = MockPC.return_value
        mock_pc.createAnswer = AsyncMock(return_value=RTCSessionDescription(sdp="dummy_sdp", type="answer"))
        mock_pc.setLocalDescription = AsyncMock()
        mock_pc.setRemoteDescription = AsyncMock()
        mock_pc.getSenders.return_value = []
        # Inject localDescription directly to avoid MagicMock issues
        mock_pc.localDescription = RTCSessionDescription(sdp="dummy_sdp", type="answer")
        mock_pc.sctp.transport.iceGatherer.getLocalCandidates.return_value = []

        message = {"type": "offer", "sdp": "v=0..."}

        await protocol.process_offer(stream_id=3, message=message)

        protocol._http.send_data.assert_called_once()
        args = protocol._http.send_data.call_args.args
        assert args[0] == 3
        assert json.loads(args[1].decode())["type"] == "answer"

@pytest.mark.asyncio
async def test_handle_event_connect():
    dummy_quic = MagicMock()
    dummy_quic.configuration.is_client = False
    dummy_quic._quic_logger = None

    protocol = WebTransportProtocol(quic=dummy_quic, stream_handler=None, app_ctx={})
    protocol._http.send_headers = AsyncMock()
    protocol._sessions = set()
    
    # This simulates what `self._http.handle_event()` would return
    event = HeadersReceived(
        stream_id=5,
        headers=[
            (b":method", b"CONNECT"),
            (b":protocol", b"webtransport"),
            (b":path", b"/webtransport"),
            (b":authority", b"127.0.0.1")
        ],
        stream_ended=False
    )
        
    await protocol.handle_event(event)

    # stream should be registered
    assert 5 in protocol._sessions

    # headers should be sent
    protocol._http.send_headers.assert_awaited_once()
    args = protocol._http.send_headers.call_args.kwargs
    assert args["stream_id"] == 5
    assert dict(args["headers"])[b":status"] == b"200"
