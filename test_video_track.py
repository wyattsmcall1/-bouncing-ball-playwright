# Unit test for the video stream wrapper

import unittest
import numpy as np
from video_track import BouncingBallTrack
from av.video.frame import VideoFrame
import asyncio
import multiprocessing as mp

class TestBouncingBallTrack(unittest.IsolatedAsyncioTestCase):
    async def test_recv_returns_valid_frame(self):
        queue = mp.Queue()
        dummy_frame = np.ones((480, 640, 3), dtype=np.uint8) * 127  # Gray
        queue.put(dummy_frame)

        track = BouncingBallTrack(queue, fps=10)
        frame = await track.recv()

        self.assertIsInstance(frame, VideoFrame)
        self.assertEqual(frame.width, 640)
        self.assertEqual(frame.height, 480)

        # Optional: only check that it's a known format
        self.assertIn(frame.format.name, ("bgr24", "yuv420p"))

    async def test_empty_queue_returns_black_frame(self):
        queue = mp.Queue()
        track = BouncingBallTrack(queue, fps=10)
        frame = await track.recv()

        self.assertIsInstance(frame, VideoFrame)
        self.assertEqual(frame.width, 640)
        self.assertEqual(frame.height, 480)

if __name__ == "__main__":
    unittest.main()
