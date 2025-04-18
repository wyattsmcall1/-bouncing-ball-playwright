# Runs standalone OpenCV-based ball simulation

import time
import cv2
import argparse
import os
from bouncing_ball import BouncingBall


def run_simulation(width=640, height=480, fps=30, duration=5, output_dir="output", save_video=True):
    os.makedirs(output_dir, exist_ok=True)
    ball = BouncingBall(width, height, radius=40, speed=(400, 300))
    frame_duration = 1.0 / fps
    total_frames = int(fps * duration)

    print(f"Running simulation for {duration} seconds at {fps} FPS ({total_frames} frames).")

    if save_video:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_path = os.path.join(output_dir, "bouncing_ball.mp4")
        out = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
        print(f"Saving video to: {video_path}")

    try:
        frame_duration = 1.0 / fps
        last_time = time.time()
        for frame_id in range(total_frames):
            now = time.time()
            dt = now - last_time
            last_time = now

            ball.step(dt)
            pos = ball.get_position()
            vel = tuple(ball.velocity)

            print(f"[Frame {frame_id}] Position: {pos} | Velocity: {vel} | Δt: {dt:.3f}s")

            frame = ball.render()

            if save_video:
                out.write(frame)
            else:
                frame_path = os.path.join(output_dir, f"frame_{frame_id:04d}.png")
                cv2.imwrite(frame_path, frame)
            
            # sleep to simulate real-time frame rate
            time_to_sleep = max(0.0, frame_duration - dt)
            if time_to_sleep > 0:
                time.sleep(time_to_sleep)
    finally:
        if save_video:
            out.release()
        print("Simulation finished.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Visualize a bouncing ball simulation.")
    parser.add_argument("--duration", type=float, default=5.0, help="Simulation duration (seconds)")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second")
    parser.add_argument("--output", type=str, default="output", help="Output directory for frames or video")
    parser.add_argument("--video", action="store_true", default=True, help="Save as video instead of frames")

    args = parser.parse_args()
    run_simulation(fps=args.fps, duration=args.duration, output_dir=args.output, save_video=args.video)
