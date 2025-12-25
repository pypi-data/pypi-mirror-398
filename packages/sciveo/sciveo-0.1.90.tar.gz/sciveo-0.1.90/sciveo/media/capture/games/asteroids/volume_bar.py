import math
import cv2


class VolumeBar:
  def __init__(self, p1, max_vol, name, color):
    self.w = 100
    self.h = 10
    self.p1 = p1
    self.max_vol = max_vol
    self.name = name
    self.color = color

    self.p2 = [p1[0] + self.w, p1[1] + self.h]

  def __call__(self, frame, vol):
    self.draw(frame, vol)

  def draw(self, frame, vol):
    vol = min(self.max_vol, vol)
    p3 = [int(self.p1[0] + self.w * vol / self.max_vol), self.p1[1] + self.h]
    cv2.putText(frame, self.name, (self.p2[0] + 3, self.p2[1]), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.5, color=(255, 255, 255), thickness=1)
    cv2.rectangle(frame, self.p1, p3, self.color, -1)
    cv2.rectangle(frame, self.p1, self.p2, (255, 255, 255), 1)
