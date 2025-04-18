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
        print("[Track] recv() called at", time.time())
        frame = None

        # Wait longer on the first few frames to let the producer fill
        max_attempts = 30 if self.frame_count < 5 else 5

        for _ in range(max_attempts):
            try:
                frame = self.frame_queue.get_nowait()
                print("[Track] Frame dequeued with shape:", frame.shape)
                break
            except Exception:
                await asyncio.sleep(self.frame_duration / 5)

        # If no frame was available, reuse the previous frame if any
        if frame is None:
            print("[Track] Queue empty, dropping to black")
            frame = np.zeros((480, 640, 3), dtype=np.uint8)

        video_frame = VideoFrame.from_ndarray(frame, format="bgr24")
        video_frame.pts = int((time.time() - self._start) * 90000)
        video_frame.time_base = Fraction(1, 90000)

        if self.frame_count < 5:
            print(f"[Track] Sending frame {self.frame_count}, PTS={video_frame.pts}")

        self.frame_count += 1
        return video_frame
