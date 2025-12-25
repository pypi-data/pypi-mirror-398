#
# Pavlin Georgiev, Softel Labs
#
# This is a proprietary file and may not be copied,
# distributed, or modified without express permission
# from the owner. For licensing inquiries, please
# contact pavlin@softel.bg.
#
# 2024
#

import time
import numpy as np
import cv2
from picamera2 import Picamera2

from sciveo.tools.logger import *
from sciveo.media.capture.cam import CameraDaemon
from sciveo.media.capture.gst_server import CamFactory


class RPICamera(CameraDaemon):
  def __init__(self, cam_id=0, width=640, height=480, period=0):
    self.width = width
    self.height = height
    super().__init__(cam_id=cam_id, period=period)

  def init_cam(self):
    debug(self.src, "starting...")

    self.picam2 = Picamera2()
    config = self.picam2.create_video_configuration(
      main={
        "size": (self.width, self.height),
        "format": "RGB888"
      },
      buffer_count=4
    )
    self.picam2.configure(config)
    self.picam2.start()

    time.sleep(1)
    debug(self.src, "started")

  def close(self):
    self.picam2.stop()

  def read_frame(self):
    try:
      frame = self.picam2.capture_array()
      cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
      with self.lock_frame:
        self.frame = frame
    except Exception as e:
      exception(e, "CAM frame read FAIL")


class RPICameraFactory(CamFactory):
  def init_cam(self):
    self.cam = RPICamera(cam_id=self.cam_id, width=self.width, height=self.height)
