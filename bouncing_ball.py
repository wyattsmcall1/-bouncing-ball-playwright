# Ball physics logic for standalone simulation

import numpy as np
import cv2

class BouncingBall:
    def __init__(self, width, height, radius=20, speed=(400, 300)):
        self.width = width
        self.height = height
        self.radius = radius
        self.position = np.array([width // 2, height // 2], dtype=np.float32)
        self.velocity = np.array(speed, dtype=np.float32)

    def step(self, dt: float):
        """Update ball position by dt seconds, handle wall collisions."""
        self.position += self.velocity * dt

        for i in range(2):  # 0: x, 1: y
            if self.position[i] - self.radius < 0:
                self.position[i] = self.radius
                self.velocity[i] *= -1
            elif self.position[i] + self.radius > (self.width if i == 0 else self.height):
                self.position[i] = (self.width if i == 0 else self.height) - self.radius
                self.velocity[i] *= -1

    def render(self):
        """Render current ball position to a frame (numpy image)."""
        print("[Ball] Rendering at", tuple(self.position.astype(int)))
        
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        center = tuple(self.position.astype(int))
        cv2.circle(frame, center, self.radius, (0, 255, 0), -1)
        return frame

    def get_position(self):
        return tuple(self.position.astype(int))
