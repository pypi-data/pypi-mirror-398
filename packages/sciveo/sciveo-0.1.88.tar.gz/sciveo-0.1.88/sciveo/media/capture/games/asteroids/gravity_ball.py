import cv2

class GravityBall:
  def __init__(self, r, x=0, y=0, gx=0.2, gy=0.1, color=(255, 0, 0)):
    self.color = color
    self.r = r

    self.x = 0
    self.y = 0

    self.vx = 0
    self.vy = 0
    self.gx = gx
    self.gy = gy

  def move(self, frame):
    w = frame.shape[1]
    h = frame.shape[0]

    self.vx += self.gx
    self.vy += self.gy
    self.x += self.vx
    self.y += self.vy

    if self.x + self.r >= w:
      self.x = w - self.r
      self.vx = - self.vx
    if self.y + self.r >= h:
      self.y = h - self.r
      self.vy = - self.vy

    cv2.circle(frame, (int(self.x), int(self.y)), self.r, self.color, thickness=-1)