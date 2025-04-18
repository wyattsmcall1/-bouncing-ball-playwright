# Runs full video pipeline: producer + viewer

import argparse
import multiprocessing as mp
import asyncio
import unittest
import os
import cv2
import numpy as np
import test_video_track

def run_tests():
    print("Running unit tests for BouncingBallTrack...")
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(test_video_track)
    )
    print("Tests complete.\n")
    return result.wasSuccessful()

async def simulate_track_output(duration=5.0, fps=30, output="output", save_video=True):
    from video_track import BouncingBallTrack
    from frame_worker import FrameProducer

    os.makedirs(output, exist_ok=True)
    frame_queue = mp.Queue(maxsize=2)
    stop_event = mp.Event()
    producer = FrameProducer(frame_queue, fps=fps, stop_event=stop_event, duration=duration)
    producer.start()

    try:
        track = BouncingBallTrack(frame_queue, fps=fps)
        num_frames = int(duration * fps)

        print(f"Simulating {num_frames} frames at {fps} FPS:")

        video_writer = None
        if save_video:
            video_path = os.path.join(output, "video_track_output.mp4")
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            video_writer = cv2.VideoWriter(video_path, fourcc, fps, (640, 480))
            print(f"[INFO] Saving video to {video_path}")

        for i in range(num_frames):
            frame = await track.recv()
            img = frame.to_ndarray(format="bgr24")

            if save_video:
                video_writer.write(img)
            else:
                filename = os.path.join(output, f"frame_{i:04d}.png")
                cv2.imwrite(filename, img)

            print(f"[Frame {i}] {frame.width}x{frame.height} - pts: {frame.pts}")

        if video_writer:
            video_writer.release()
            print("[INFO] Video saved successfully.")

    finally:
        stop_event.set()
        producer.terminate()
        producer.join()

if __name__ == '__main__':
    mp.set_start_method('spawn', force=True)

    parser = argparse.ArgumentParser(description="Visualize a bouncing ball simulation.")
    parser.add_argument("--duration", type=float, default=5.0, help="Simulation duration (seconds)")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second")
    parser.add_argument("--output", type=str, default="output", help="Output directory for frames or video")
    parser.add_argument("--video", action="store_true", default=True, help="Save as video instead of frames")

    args = parser.parse_args()

    if run_tests():
        asyncio.run(simulate_track_output(
            duration=args.duration,
            fps=args.fps,
            output=args.output,
            save_video=args.video
        ))
    else:
        print("Tests failed. Simulation skipped.")
