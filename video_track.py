# WebRTC-compatible video stream track that serves frames from the queue

import asyncio
import av
import numpy as np
from aiortc import VideoStreamTrack
from av.video.frame import VideoFrame
import time
from fractions import Fraction

#DEBUG = False

class BouncingBallTrack(VideoStreamTrack):
    def __init__(self, frame_queue, fps=30):
        super().__init__()
        self.frame_queue = frame_queue
        self.fps = fps
        self.frame_duration = 1.0 / fps
        self._start = time.time()
        self.frame_count = 0

    async def recv(self):
        #if DEBUG:
        #    print("[Track] recv() called at", time.time())

        #await asyncio.sleep(self.frame_duration)

        print("[Track] recv() called")

        try:
            frame = self.frame_queue.get_nowait()
            print("[Track] Frame dequeued with shape:", frame.shape)
        except Exception:
            print("[Track] Queue empty, sending fallback frame")
            frame = np.full((480, 640, 3), (0, 255, 0), dtype=np.uint8)

        video_frame = VideoFrame.from_ndarray(frame, format="bgr24")
        video_frame.pts = int((time.time() - self._start) * 90000)
        video_frame.time_base = Fraction(1, 90000)

        #if DEBUG:
        #    print("[Track] Returning frame with PTS:", pts)

        return video_frame
