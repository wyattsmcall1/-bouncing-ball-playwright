# Multiprocessing class that generates video frames in a background process

import time
import multiprocessing as mp
import cv2
from bouncing_ball import BouncingBall

class FrameProducer(mp.Process):
    def __init__(self, frame_queue: mp.Queue, width=640, height=480, fps=30, stop_event=None, duration=None, debug=False):
        super().__init__()
        self.frame_queue = frame_queue
        self.width = width
        self.height = height
        self.fps = fps
        self.stop_event = stop_event or mp.Event()
        self.duration = duration  # new: run time limit in seconds
        self.debug = debug

    def run(self):
        print(f"[Producer] Generating frame at {self.fps} FPS")
        ball = BouncingBall(width=640, height=480, radius=40, speed=(400, 300))
        frame_duration = 1.0 / self.fps
        start_time = time.time()

        if self.debug:
            print("[Worker] Frame generated")

        last_time = start_time
        while not self.stop_event.is_set():
            now = time.time()

            # new: check for max duration
            if self.duration is not None and (now - start_time) >= self.duration:
                if self.debug:
                    print("[Worker] Duration exceeded, stopping.")
                break

            dt = now - last_time
            last_time = now

            ball.step(dt)
            frame = ball.render()
            print("[FrameProducer] Sending frame of shape", frame.shape)
            try:
                print("[Producer] Putting frame into queue")
                cv2.imwrite("/tmp/test_frame.png", frame)
                self.frame_queue.put_nowait(frame)
                if self.debug:
                    print("[Worker] Frame enqueued")
            except mp.queues.Full:
                try:
                    self.frame_queue.get_nowait()
                    self.frame_queue.put_nowait(frame)
                    if self.debug:
                        print("[Worker] Frame queue full — dropped one and enqueued")
                except Exception:
                    if self.debug:
                        print("[Worker] Frame skipped (queue full)")

            if not self.stop_event.is_set():
                time.sleep(frame_duration)

        if self.debug:
            print("[Worker] Stopped")
