import math
import cv2
import numpy as np

from geometrics import *
from laser import *
from volume_bar import *
from base_move import *


class RocketBase(BaseMoveConstantVelocity):
  def __init__(self, x0, y0):
    super().__init__(x0, y0, 0, 0, (255, 0, 0))
    self.l = 10000000000
    self.angle = 0

  def check_collision(self, x, y, r):
    return False

  def rotate(self, angle):
    self.angle += angle

  def accelerate(self, a):
    pass

  def fire(self):
    pass

  def alive(self):
    return True

  def laser_positions(self):
    return []


class SimpleRocket(RocketBase):
  def __init__(self, x0=0, y0=0, color=(255, 0, 0)):
    super().__init__(x0, y0)
    self.color = color
    self.r = 10

    self.vx = 0
    self.vy = 0

  def accelerate(self, gx, gy):
    self.vx += gx
    self.vy += gy

  def draw(self, frame):
    cv2.circle(frame, (int(self.x), int(self.y)), self.r, self.color, thickness=-1)
    cv2.putText(frame, "V ({},{})".format(round(self.vx, 2), round(self.vy, 2)), (5, 20), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.5, color=(255, 255, 255), thickness=1)


class Rocket(RocketBase):
  def __init__(self, x0=0, y0=0, color=(255, 0, 0), txt_pos=(5, 20), l=10, laser_count=100, fuel=20):
    super().__init__(x0, y0)
    self.color = color
    self.txt_pos = txt_pos
    self.l = l

    self.thruster_default = 30
    self.thruster = 0
    self.fuel = fuel

    self.a = 0
    self.ax = 0
    self.ay = 0

    self.vx = 0
    self.vy = 0

    self.laser_count = laser_count
    self.lasers = []

    self.fuel_bar = VolumeBar((400, 20), self.fuel, name="FUEL", color=(255, 0, 0))
    self.laser_bar = VolumeBar((400, 50), self.laser_count, name="LASER", color=(0, 0, 255))

  def accelerate(self, a):
    if self.fuel < a:
      a = self.fuel
    self.fuel -= a

    angle = to_radians(self.angle)
    self.ax = a * math.cos(angle)
    self.ay = a * math.sin(angle)
    self.a = a

    self.vx += self.ax
    self.vy += self.ay

    self.thruster = self.thruster_default

  def draw(self, frame):
    angle = to_radians(self.angle)
    p0 = (int(self.x), int(self.y))
    p1 = (int(self.x + self.l * math.cos(angle)), int(self.y + self.l * math.sin(angle)))
    p2 = (int(self.x - self.l * math.cos(angle)), int(self.y - self.l * math.sin(angle)))
    p3, p4 = line_perpendicular(p1, p2, self.l)

    cv2.line(frame, p1, p2, self.color, 2)
    # cv2.line(frame, p3, p4, self.color, 4)
    cv2.line(frame, p3, p1, (0, 0, 255), 3)
    cv2.line(frame, p4, p1, (0, 255, 0), 3)
    cv2.line(frame, p3, p0, self.color, 2)
    cv2.line(frame, p4, p0, self.color, 2)

    if self.thruster > 0:
      l = self.a * 200
      p1 = p2
      da = 0.3
      p2 = [int(p1[0] - l * math.cos(angle - da)), int(p1[1] - l * math.sin(angle - da))]
      p3 = [int(p1[0] - l * math.cos(angle + da)), int(p1[1] - l * math.sin(angle + da))]
      cv2.drawContours(frame, [np.array([p1, p2, p3])], 0, (0, 0, 255), -1)
      self.thruster -= 1

    txt = "V ({},{}) A[{}]".format(round(self.vx, 3), round(self.vy, 3), self.angle)
    cv2.putText(frame, txt, self.txt_pos, fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.3, color=(255, 255, 255), thickness=1)

    self.move_lasers(frame)

    self.fuel_bar(frame, self.fuel)
    self.laser_bar(frame, self.laser_count)

  def move_lasers(self, frame):
    for laser in self.lasers:
      if not laser.move(frame):
        self.lasers.remove(laser)

  def fire(self):
    if self.laser_count > 0:
      self.laser_count -= 1
      self.lasers.append(Laser(self.x, self.y, self.angle))

  def laser_positions(self):
    positions = []
    for laser in self.lasers:
      positions.append([laser.p1, laser.p2, laser.angle])
    return positions

  def remove_laser(self, idx):
    if idx < len(self.lasers):
      del self.lasers[idx]

  def check_collision(self, x, y, r):
    # d = np.linalg.norm(np.array([x, y]) - np.array([self.x, self.y]))
    d = math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)
    return d < r + self.l


class RocketExplosion(RocketBase):
  def __init__(self, x0, y0):
    super().__init__(x0, y0)
    self.r = 3

  def move(self, frame):
    cv2.circle(frame, (int(self.x), int(self.y)), int(self.r), (0, 0, 255), thickness=-1)
    self.r += 0.8

  def alive(self):
    return self.r < 100