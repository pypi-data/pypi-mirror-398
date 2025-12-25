import cv2
import numpy as np

from rocket import *
from asteroid import *
from volume_bar import *


class SpaceAsteroids:
  def __init__(self, w, h, rocket_lives=10):
    self.W = w
    self.H = h
    self.rocket_lives = rocket_lives

    self.rocket = Rocket(x0=50, y0=50, color=(255, 255, 0), txt_pos=(5, 30), laser_count=200)
    self.rocket_lives_bar = VolumeBar((200, 20), self.rocket_lives, name="LIVE", color=(0, 255, 0))

    self.asteroids_removed = 0
    self.asteroids = []
    self.init_asteroids()
    self.asteroids_bar = VolumeBar((200, 40), len(self.asteroids) * 2, name="ASTEROIDS", color=(0, 255, 255))

  def init_asteroids(self):
    dv = 1.1
    while(len(self.asteroids) < 30):
      x0 = np.random.randint(200, self.W)
      y0 = np.random.randint(200, self.H)
      r0 = np.random.randint(5, 100)
      is_usable = True
      for asteroid in self.asteroids:
        d = math.sqrt((asteroid.x - x0) ** 2 + (asteroid.y - y0) ** 2)
        if d < (asteroid.r + r0) * 1.2:
          is_usable = False
          break

      if is_usable:
        self.asteroids.append(
          Asteroid(
            x0, y0,
            np.random.uniform(-dv, dv),
            np.random.uniform(-dv, dv),
            r0,
            color=(255, 255, 255),
            size_contour=10
          )
        )

  def run(self):
    vrotate = 0

    while(True):
      k = cv2.waitKey(1)
      if k == 27:    # Esc key to stop
        break

      if k == ord('u'):
        self.rocket.accelerate(0.1)
      if k == ord('i'):
        self.rocket.accelerate(0.2)
      if k == ord('o'):
        self.rocket.accelerate(0.3)
      if k == ord('m'):
        self.rocket.fire()
      if k == ord('j'):
        vrotate = -2
      if k == ord('k'):
        vrotate = 0
      if k == ord('l'):
        vrotate = 2

      self.rocket.rotate(vrotate)

      frame = np.zeros(shape=[self.H, self.W, 3], dtype=np.uint8)

      self.rocket.move(frame)

      for asteroid in self.asteroids:
        asteroid.move(frame)

      for i in range(len(self.asteroids)):
        for j in range(i + 1, len(self.asteroids)):
          d = math.sqrt((self.asteroids[i].x - self.asteroids[j].x) ** 2 + (self.asteroids[i].y - self.asteroids[j].y) ** 2)
          if d < self.asteroids[i].r + self.asteroids[j].r:
            vx1 = ((self.asteroids[i].r - self.asteroids[j].r) * self.asteroids[i].vx + 2 * self.asteroids[j].r * self.asteroids[j].vx) / (self.asteroids[i].r + self.asteroids[j].r)
            vy1 = ((self.asteroids[i].r - self.asteroids[j].r) * self.asteroids[i].vy + 2 * self.asteroids[j].r * self.asteroids[j].vy) / (self.asteroids[i].r + self.asteroids[j].r)
            vx2 = ((self.asteroids[j].r - self.asteroids[i].r) * self.asteroids[j].vx + 2 * self.asteroids[i].r * self.asteroids[i].vx) / (self.asteroids[i].r + self.asteroids[j].r)
            vy2 = ((self.asteroids[j].r - self.asteroids[i].r) * self.asteroids[j].vy + 2 * self.asteroids[i].r * self.asteroids[i].vy) / (self.asteroids[i].r + self.asteroids[j].r)
            self.asteroids[i].vx = vx1
            self.asteroids[i].vy = vy1
            self.asteroids[j].vx = vx2
            self.asteroids[j].vy = vy2

      laser_positions = self.rocket.laser_positions()
      for asteroid in self.asteroids:
        for i, laser in enumerate(laser_positions):
          d1 = math.sqrt((asteroid.x - laser[0][0]) ** 2 + (asteroid.y - laser[0][1]) ** 2)
          d2 = math.sqrt((asteroid.x - laser[1][0]) ** 2 + (asteroid.y - laser[1][1]) ** 2)
          if d1 < asteroid.r or d2 < asteroid.r:
            self.asteroids.remove(asteroid)
            self.rocket.remove_laser(i)
            self.asteroids_removed += 1

            if asteroid.r > 10:
              angle1 = to_radians(laser[2] + 90)
              angle2 = to_radians(laser[2] - 90)
              self.asteroids.append(
                Asteroid(
                  asteroid.x + math.cos(angle1) * (asteroid.r / 1.9),
                  asteroid.y + math.sin(angle1) * (asteroid.r / 1.9),
                  math.cos(angle1) * asteroid.vx,
                  math.sin(angle1) * asteroid.vy,
                  asteroid.r / 2,
                  color=(255, 255, 255),
                  size_contour=10
                )
              )
              self.asteroids.append(
                Asteroid(
                  asteroid.x + math.cos(angle2) * (asteroid.r / 1.9),
                  asteroid.y + math.sin(angle2) * (asteroid.r / 1.9),
                  math.cos(angle2) * asteroid.vx,
                  math.sin(angle2) * asteroid.vy,
                  asteroid.r / 2,
                  color=(255, 255, 255),
                  size_contour=10
                )
              )

            break

      for asteroid in self.asteroids:
        if self.rocket.check_collision(asteroid.x, asteroid.y, asteroid.r):
          self.asteroids.remove(asteroid)
          self.rocket = RocketExplosion(self.rocket.x, self.rocket.y)
          self.rocket_lives -= 1
          break

      if not self.rocket.alive():
        if self.rocket_lives > 0:
          self.rocket = Rocket(x0=self.rocket.x, y0=self.rocket.y, color=(255, 255, 0), txt_pos=(5, 30), laser_count=len(self.asteroids) * 10)
        else:
          break

      if len(self.asteroids) == 0 and self.rocket_lives > 0:
        self.rocket = Rocket(x0=400, y0=400, color=(255, 255, 0), txt_pos=(5, 30), l=50)
        txt = "Winner"
        self.rocket_lives = -1
      else:
        txt = "Asteroids {} / {}".format(self.asteroids_removed, len(self.asteroids))
      cv2.putText(frame, txt, (5, 20), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.4, color=(255, 255, 255), thickness=1)

      self.rocket_lives_bar(frame, self.rocket_lives)
      self.asteroids_bar(frame, len(self.asteroids))

      cv2.imshow('asteroids', frame)