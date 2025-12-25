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

import time
import cv2

from sciveo.tools.timers import FPSCounter
from sciveo.tools.logger import *


class RTSPVideoPlayer:
  def __init__(self, rtsp_url, name=None):
    self.rtsp_url = rtsp_url
    if name is None:
      name = rtsp_url
    self.name = name
    self.cap = None
    self.is_running = False
    self.fps = FPSCounter(period=10, tag=f"{name}", printer=info, round_value=1)

  def open(self):
    info("Opening...", self.rtsp_url)
    self.cap = cv2.VideoCapture(self.rtsp_url)
    if not self.cap.isOpened():
      error("Failed to open RTSP URL", self.rtsp_url)
      self.cap = None
    else:
      info("Opened", self.rtsp_url)

  def close(self):
    if self.cap:
      info("Closing RTSP", self.rtsp_url)
      try:
        self.cap.release()
      except:
        pass
      self.cap = None
    try:
      cv2.destroyWindow(self.window_name)
    except:
      pass

  def run(self):
    self.is_running = True
    while(self.is_running):
      self.loop()

  def loop(self):
    if self.cap is None:
      self.open()
      if self.cap is None:
        time.sleep(1)
        return

    ret, frame = self.cap.read()
    if not ret or frame is None:
      error("Failed to read frame, reconnecting...")
      self.close()
      time.sleep(1)
      return

    cv2.imshow(self.name, frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
      info("Quit key pressed, stopping player")
      self.close()
      self.is_running = False
    self.fps.update()

  def finalise(self):
    self.close()


if __name__ == '__main__':

  player = RTSPVideoPlayer("rtsp://192.168.10.118:8554/test")
  # player = RTSPVideoPlayer("rtsp://192.168.10.118:8554/camera")
  player.run()
