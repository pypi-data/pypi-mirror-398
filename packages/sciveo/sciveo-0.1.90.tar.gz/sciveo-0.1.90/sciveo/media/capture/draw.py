#
# Pavlin Georgiev, Softel Labs
#
# This is a proprietary file and may not be copied,
# distributed, or modified without express permission
# from the owner. For licensing inquiries, please
# contact pavlin@softel.bg.
#
# 2025
#

import cv2
import numpy as np
from datetime import datetime
from sciveo.tools.logger import *


class DrawNone:
  def __call__(self, frame, configuration):
    return frame

class DrawDateTime:
  def __init__(self, position=(10, 10), color=(255, 255, 255), thickness=3, font_scale_factor=0.001, font=cv2.FONT_HERSHEY_SIMPLEX):
    """
    position: tuple (x, y) displacement from top-left
    color: BGR tuple
    thickness: line thickness
    font_scale_factor: relative to frame height (0.0015 is reasonable)
    font: cv2 font
    """
    self.position = position
    self.color = color
    self.thickness = thickness
    self.font = font
    self.font_scale_factor = font_scale_factor

  def __call__(self, frame, configuration):
    """
    Draws date/time (or custom text) on the frame.

    frame: np.ndarray
    text: optional text to draw; if None, current date/time is used
    position, color, thickness: optional overrides
    """
    if frame is None or len(frame.shape) < 2:
      return frame  # invalid frame

    tag = configuration.get("tag", "")

    h, w = frame.shape[:2]

    font_scale = configuration.get("font_scale", max(0.2, h * self.font_scale_factor))
    color = configuration.get("color", self.color)
    thickness = configuration.get("thickness", self.thickness)

    date_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    draw_text = f"{tag} {date_text}"

    # Adjust position to avoid going out of frame
    x = min(max(self.position[0], 0), w - 1)
    y = min(max(self.position[1] + int(font_scale * 20), int(font_scale * 20)), h - 1)

    cv2.putText(frame, draw_text, (x, y), self.font, font_scale, color, thickness, cv2.LINE_AA)
    return frame



if __name__ == "__main__":

  cap = cv2.VideoCapture(0)
  drawer = DrawDateTime(tag="test cam", position=(10, 10))

  while True:
    ret, frame = cap.read()
    if not ret:
      break

    frame = drawer(frame)

    cv2.imshow("Frame", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
      break

  cap.release()
  cv2.destroyAllWindows()