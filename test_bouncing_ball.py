import unittest
from bouncing_ball import BouncingBall

class TestBouncingBall(unittest.TestCase):
    def test_initial_position(self):
        ball = BouncingBall(200, 100)
        self.assertEqual(ball.get_position(), (100, 50))

    def test_movement(self):
        ball = BouncingBall(200, 100, speed=(50, 0))
        ball.step(1.0)
        x, y = ball.get_position()
        self.assertAlmostEqual(x, 150, delta=1)
        self.assertEqual(y, 50)

    def test_bounce_x(self):
        ball = BouncingBall(100, 100, speed=(500, 0))
        ball.step(0.5)  # Hits right wall and should bounce
        self.assertLessEqual(ball.get_position()[0], 100 - ball.radius)
        self.assertLess(ball.velocity[0], 0)  # Should now be negative

    def test_bounce_y(self):
        ball = BouncingBall(100, 100, speed=(0, -500))
        ball.step(0.5)  # Hits top wall and should bounce
        self.assertGreaterEqual(ball.get_position()[1], ball.radius)
        self.assertGreater(ball.velocity[1], 0)  # Should now be positive

    def test_render_output(self):
        ball = BouncingBall(100, 100)
        frame = ball.render()
        self.assertEqual(frame.shape, (100, 100, 3))
        self.assertEqual(frame.dtype, 'uint8')

if __name__ == '__main__':
    unittest.main()
