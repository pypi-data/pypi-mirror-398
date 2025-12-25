import math

from geometrics import *


class BaseMoveConstantVelocity:
  def __init__(self, x0, y0, vx0, vy0, color=(0, 0, 255)):
    self.x = x0
    self.y = y0
    self.vx = vx0
    self.vy = vy0
    self.color = color

  def move(self, frame):
    w = frame.shape[1]
    h = frame.shape[0]

    self.x += self.vx
    self.y += self.vy

    self.x, self.y = frame_bounds_rewind(w, h, self.x, self.y)

    self.draw(frame)

  def draw(self, frame):
    pass
