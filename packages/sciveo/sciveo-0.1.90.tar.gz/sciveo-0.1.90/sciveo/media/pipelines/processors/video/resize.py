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

from sciveo.tools.common import *
from sciveo.media.pipelines.processors.base import *


class VideoResize(BaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)
    self.current_heights = {}
    self.default.update({
      "CRF": 20, "heights": [720, 480],
      "downsampling_rate": 1,
    })

  def init_low_videos(self, frame):
    self.current_heights = {}
    for h in self["heights"]:
      h, w = get_frame_resolution(frame, h)
      if h in self.current_heights:
        continue
      self.current_heights[h] = [w, h]

      tag = f"resized-{h}"
      resized_local_path = self.add_suffix_to_filename(self.local_path, tag)
      self.low_resolutions.append((w, h))
      self.low_videos.append(VideoWriterFFMPEG.new(resized_local_path, w=w, crf=str(self["CRF"])))
      self.next_content(self.media, tag, resized_local_path, w=w, h=h)

  def process(self, media):
    self.media = media
    self.local_path = media["local_path"]

    self.low_videos = []
    self.low_resolutions = []

    self.cap = cv2.VideoCapture(self.local_path)
    n_frame = 0
    while(self.cap.isOpened()):
      n_frame += 1
      ret, frame = self.cap.read()
      if not ret:
        break

      if n_frame == 1:
        self.init_low_videos(frame)

      for i, low_video in enumerate(self.low_videos):
        if n_frame % self["downsampling_rate"] == 0:
          frame_resized = cv2.resize(frame, self.low_resolutions[i], interpolation=cv2.INTER_AREA)
          low_video.write(frame_resized)

    self.cap.release()
    for low_video in self.low_videos:
      low_video.close()

    return self.media

  def is_resizer(self):
    return True

  def content_type(self):
    return "video"

  def name(self):
    return "video-resize"
