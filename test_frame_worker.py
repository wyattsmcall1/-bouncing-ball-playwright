import unittest
import multiprocessing as mp
import time
import numpy as np
from frame_worker import FrameProducer

class TestFrameProducer(unittest.TestCase):
    def setUp(self):
        self.queue = mp.Queue(maxsize=2)
        self.fps = 10
        self.stop_event = mp.Event()
        self.producer = FrameProducer(self.queue, width=320, height=240, fps=self.fps, stop_event=self.stop_event)
        mp.set_start_method('spawn', force=True)

    def test_frame_generation(self):
        self.producer.start()
        time.sleep(1.0)  # Allow it to produce some frames
        frames_collected = 0

        while not self.queue.empty():
            frame = self.queue.get()
            frames_collected += 1
            self.assertIsInstance(frame, np.ndarray)
            self.assertEqual(frame.shape, (480, 640, 3))
            self.assertEqual(frame.dtype, np.uint8)

        self.assertGreater(frames_collected, 0, "No frames were produced.")

        self.stop_event.set()
        self.producer.join(timeout=5)
        if self.producer.is_alive():
            self.producer.terminate()
            self.producer.join()

    def tearDown(self):
        if self.producer.is_alive():
            self.producer.terminate()
            self.producer.join()
