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

import cv2
import numpy as np

from sciveo.tools.common import *
from sciveo.media.pipelines.processors.base import *


class MotionVideoWriter(VideoWriterFFMPEG):
  def write(self, frame):
    self.out.writeFrame(frame[:,::-1])


class VideoMotionDetector(BaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)

    self.default.update({"CRF": 40, "frame_rate": 1})

    # TODO: Place md-related options into config
    self.fgbg = cv2.createBackgroundSubtractorMOG2(history=50, varThreshold=20, detectShadows=False)

  def init_video(self, frame):
    tag = "MOTION"
    video_local_path = self.add_suffix_to_filename(self.local_path, tag)
    self.next_content(self.media, tag, video_local_path, w=frame.shape[1], h=frame.shape[0])
    self.md_video = MotionVideoWriter(video_local_path, crf=str(self["CRF"]))

  def process(self, media):
    self.media = media
    self.local_path = media["local_path"]

    frame_rate = self["frame_rate"]

    cap = cv2.VideoCapture(self.local_path)
    ret, frame = cap.read()
    self.init_video(frame)

    n_frame = 0
    while(cap.isOpened()):
      n_frame += 1
      ret, frame = cap.read()
      if not ret:
        break

      try:
        if n_frame % frame_rate == 0:
          md_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
          md_frame = cv2.blur(src=md_frame, ksize=(10,10))
          md_frame = self.fgbg.apply(md_frame)
          self.md_video.write(md_frame)
      except Exception as e:
        exception(e)

    cap.release()
    self.md_video.close()
    return self.media

  def content_type(self):
    return "video"

  def name(self):
    return "video-motion-detector"
