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

import os
import time
import cv2
import numpy as np

from sciveo.tools.logger import *


class MapContoursUI:
  def __init__(self, image_path):
    self.image_path = image_path
    self.image = cv2.imread(image_path)
    if self.image is None:
      raise ValueError(f"Image not found: {image_path}")
    self.contours = []
    self.current_contour = []
    self.current_mouse_pos = (0, 0)
    self.drawing = False
    self.display = self.image.copy()

  def _mouse_callback(self, event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE:
      self.current_mouse_pos = (x, y)

  def draw(self):
    cv2.namedWindow("Contour Drawing")
    cv2.setMouseCallback("Contour Drawing", self._mouse_callback)

    print("\nControls:\n"
          "  c - Start new contour\n"
          "  v - Add point\n"
          "  x - Finalize contour\n"
          "  u - Undo last contour\n"
          "  z - Finish & show areas\n")

    while True:
      frame = self.display.copy()

      for cnt in self.contours:
        cv2.polylines(frame, [cnt], isClosed=True, color=(255, 0, 255), thickness=2)

      if self.current_contour:
        pts = self.current_contour + [self.current_mouse_pos]
        for i in range(1, len(pts)):
          cv2.line(frame, pts[i - 1], pts[i], (0, 255, 255), 1)

      cv2.circle(frame, self.current_mouse_pos, 5, (0, 255, 0), -1)

      self.draw_contour_indexes(frame)
      self.draw_contour_lengths(frame)

      cv2.imshow("Contour Drawing", frame)
      key = cv2.waitKey(1) & 0xFF

      if key == ord('c'):  # Start new contour
        self.current_contour = []
        self.drawing = True
        print("Started new contour.")

      elif key == ord('v') and self.drawing:  # Add point
        self.current_contour.append(self.current_mouse_pos)
        print(f"Added point: {self.current_mouse_pos}")

      elif key == ord('x') and self.drawing:  # Finalize
        if len(self.current_contour) >= 3:
          self.contours.append(np.array(self.current_contour, dtype=np.int32))
          print("Contour finalized.")
        else:
          print("Contour discarded (not enough points).")
        self.current_contour = []
        self.drawing = False

      elif key == ord('u') and self.contours:  # Undo
        self.contours.pop()
        print("Last contour removed.")

      elif key == ord('z'):  # Finish
        cv2.destroyWindow("Contour Drawing")
        break

    self.print_area_summary()
    time.sleep(5)
    cv2.destroyAllWindows()

  def draw_contour_indexes(self, frame):
    for idx, cnt in enumerate(self.contours):
      M = cv2.moments(cnt)
      if M["m00"] != 0:
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        cv2.putText(frame, str(idx + 1), (cx - 10, cy + 10), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

  def draw_contour_lengths(self, frame):
    for cnt in self.contours:
      points = cnt.reshape(-1, 2)
      for i in range(len(points)):
        p1 = points[i]
        p2 = points[(i + 1) % len(points)]
        dist = int(np.linalg.norm(p1 - p2))
        mid = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)
        cv2.putText(frame, f"{dist}px", mid, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

    if self.current_contour:
      pts = self.current_contour + [self.current_mouse_pos]
      for i in range(len(pts) - 1):
        cv2.line(frame, pts[i], pts[i + 1], (0, 255, 0), 1)

        dist = int(np.linalg.norm(np.array(pts[i]) - np.array(pts[i + 1])))
        mid = ((pts[i][0] + pts[i + 1][0]) // 2, (pts[i][1] + pts[i + 1][1]) // 2)
        cv2.putText(frame, f"{dist}px", mid, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

  def print_area_summary(self):
    info("🧮 Contour Areas")
    for i, cnt in enumerate(self.contours):
      area = cv2.contourArea(cnt)
      info(f"Contour {i+1}: Area = {area:.2f}")

  def save(self, path):
    np.save(path, np.array(self.contours, dtype=object))
    info(f"Contours saved to: {path}")

  def load(self, path):
    if os.path.exists(path):
      loaded = np.load(path, allow_pickle=True)
      self.contours = list(loaded)
      info(f"Contours loaded from: {path}")
      self.print_area_summary()
    else:
      info(f"File not found: {path}")


if __name__ == "__main__":
  ui = MapContoursUI(os.environ["PATH_IMAGE"])
  ui.load(os.environ["PATH_SAVE_CONTOURS"])
  ui.draw()
  ui.save(os.environ["PATH_SAVE_CONTOURS"])