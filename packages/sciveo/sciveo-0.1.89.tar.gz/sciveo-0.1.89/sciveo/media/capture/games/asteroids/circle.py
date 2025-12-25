import math

from base_move import *


class Circle(BaseMoveConstantVelocity):
  def __init__(self, x0, y0, r, vx0, vy0, color=(0, 0, 255)):
    super().__init__(x0, y0, vx0, vy0, color)
    self.r = r

  def move(self, frame):
    w = frame.shape[1]
    h = frame.shape[0]

    self.x += self.vx
    self.y += self.vy

    self.x, self.y = frame_bounds_rewind(w - self.r, h - self.r, self.x, self.y)

    self.draw(frame)

  def draw(self, frame):
    angle = 0.0
    while(angle <= 2 * math.pi):
      x1 = self.x + self.r * math.cos(angle)
      y1 = self.y + self.r * math.sin(angle)
      x1 = int(x1)
      y1 = int(y1)
      angle += 0.01

      frame[y1, x1] = self.color
