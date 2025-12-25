import math
import cv2
import numpy as np

from geometrics import *
from base_move import *


class Asteroid(BaseMoveConstantVelocity):
  def __init__(self, x0, y0, vx0, vy0, r0, color=(255, 0, 0), size_contour=20):
    super().__init__(x0, y0, vx0, vy0, color)

    self.r0 = r0
    self.r = r0
    self.size_contour = size_contour

    self.generate_contour()

  def draw(self, frame):
    # self.generate_contour()
    list_points = []
    for p in self.list_points:
      list_points.append((int(self.x + p[0]), int(self.y + p[1])))
    cv2.drawContours(frame, [np.array(list_points)], 0, self.color, 1)
    cv2.circle(frame, (int(self.x), int(self.y)), int(self.r), (0, 0, 200), thickness=1)

  def generate_contour(self):
    self.list_points = []
    for i in range(self.size_contour):
      r = self.r0 * np.sqrt(np.random.uniform(0.3, 1.0))
      # angle = np.random.uniform() * 2 * PI
      angle = i * 2 * PI / self.size_contour
      p = (r * math.cos(angle), r * math.sin(angle))
      self.list_points.append(p)
