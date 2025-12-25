import cv2
import math
import numpy as np

from geometrics import to_radians
from base_move import *


class Laser(BaseMoveConstantVelocity):
  def __init__(self, x0, y0, angle):
    super().__init__(x0, y0, 0, 0, (0, 0, 255))
    # self.path = 0
    # self.x0 = x0
    # self.y0 = y0

    self.l = 10
    self.angle = angle

    self.points()

    self.v = 2.5
    self.vx = self.v * math.cos(to_radians(self.angle))
    self.vy = self.v * math.sin(to_radians(self.angle))

  def points(self):
    angle = to_radians(self.angle)
    self.p1 = (int(self.x), int(self.y))
    self.p2 = (int(self.x + self.l * math.cos(angle)), int(self.y + self.l * math.sin(angle)))
    # self.path = math.sqrt((self.x - self.x0) ** 2 + (self.y - self.y0) ** 2)

  def move(self, frame):
    w = frame.shape[1]
    h = frame.shape[0]

    self.x += self.vx
    self.y += self.vy

    self.points()

    cv2.line(frame, self.p1, self.p2, self.color, 2)

    return self.x >= 0 and self.x <= w and self.y >= 0 and self.y <= h