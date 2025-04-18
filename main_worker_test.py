import multiprocessing as mp
import time
import unittest
import cv2
import argparse
import os
from frame_worker import FrameProducer
import test_frame_worker  # unit test module

def run_tests():
    print("Running unit tests...")
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(test_frame_worker)
    )
    print("Tests complete.\n")
    return result.wasSuccessful()

def simulate_track_output(duration=5.0, fps=30, output="output", save_video=True):
    print(f"Simulating ball track output for {duration}s at {fps} FPS (video={save_video})")
    frame_queue = mp.Queue(maxsize=2)
    stop_event = mp.Event()
    producer = FrameProducer(frame_queue, fps=fps, stop_event=stop_event, debug=True)
    producer.start()

    os.makedirs(output, exist_ok=True)
    frame_limit = int(duration * fps)
    frames = []

    try:
        for frame_id in range(frame_limit):
            if not frame_queue.empty():
                frame = frame_queue.get()
                print(f"[Simulator] Frame {frame_id} received")
                frames.append(frame)
            else:
                print(f"[Simulator] Frame {frame_id} missing (queue empty)")
            time.sleep(1 / fps)
    finally:
        print("[Simulator] Stopping producer...")
        stop_event.set()
        producer.join(timeout=1)
        if producer.is_alive():
            print("[Simulator] Producer still alive — terminating...")
            producer.terminate()
            producer.join()

    if frames:
        if save_video:
            out_path = os.path.join(output, "worker_output.mp4")
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(out_path, fourcc, fps, (frames[0].shape[1], frames[0].shape[0]))
            for f in frames:
                out.write(f)
            out.release()
            print(f"[Simulator] Saved video to {out_path}")
        else:
            for i, f in enumerate(frames):
                cv2.imwrite(os.path.join(output, f"frame_{i:04d}.png"), f)
            print(f"[Simulator] Saved {len(frames)} frames to {output}")

if __name__ == "__main__":
    mp.set_start_method('spawn', force=True)

    parser = argparse.ArgumentParser(description="Simulate bouncing ball output to file.")
    parser.add_argument("--duration", type=float, default=5.0, help="Simulation duration (seconds)")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second")
    parser.add_argument("--output", type=str, default="output", help="Output directory for frames or video")
    parser.add_argument("--video", action="store_true", default=True, help="Save as video instead of frames")
    args = parser.parse_args()

    if run_tests():
        simulate_track_output(
            duration=args.duration,
            fps=args.fps,
            output=args.output,
            save_video=args.video
        )
    else:
        print("Tests failed. Simulation skipped.")
