import asyncio
import av
import numpy as np
from aiortc import VideoStreamTrack
from av.video.frame import VideoFrame
import time
from fractions import Fraction

class BouncingBallTrack(VideoStreamTrack):
    def __init__(self, frame_queue, fps=30):
        super().__init__()  # Don't forget this!
        self.frame_queue = frame_queue
        self.fps = fps
        self.frame_duration = 1.0 / fps
        self._start = time.time()

    async def recv(self):
        print("[Track] recv() called at", time.time())
        await asyncio.sleep(self.frame_duration)

        try:
            frame = self.frame_queue.get_nowait()
            print("[Track] Frame dequeued with min =", frame.min(), "max =", frame.max())
        except Exception:
            # Toggle frame content to show motion
            t = int(time.time() * 2) % 2
            color = (0, 0, 255) if t == 0 else (0, 255, 0)
            frame = np.full((480, 640, 3), color, dtype=np.uint8)
            print("[Track] Queue empty, returning fallback frame:", color)

        video_frame = VideoFrame.from_ndarray(frame, format="bgr24")
        pts = int((time.time() - self._start) * 90000)
        print("[Track] Returning frame with PTS:", pts)
        video_frame.pts = pts
        video_frame.time_base = Fraction(1, 90000)

        return video_frame
