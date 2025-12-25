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


class VideoDownsample(BaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)
    self.videos = []
    self.downsampling_rates = []
    self.default.update({"CRF": 20, "downsampling-rates": [10, 20]})

  def init_videos(self, frame, media):
    for downsampling_rate in self["downsampling-rates"]:
      h, w = frame.shape[0], frame.shape[1]
      dsr = f"DSR{downsampling_rate}"
      video_local_path = self.add_suffix_to_filename(self.local_path, dsr)
      self.downsampling_rates.append(downsampling_rate)
      self.videos.append(VideoWriterFFMPEG.new(video_local_path, crf=str(self["CRF"])))
      self.next_content(media, dsr, video_local_path, w=w, h=h)

  def process(self, media):
    self.local_path = media["local_path"]

    self.cap = cv2.VideoCapture(self.local_path)
    n_frame = 0
    while(self.cap.isOpened()):
      n_frame += 1
      ret, frame = self.cap.read()
      if not ret:
        break

      if n_frame == 1:
        self.init_videos(frame, media)

      for i, video in enumerate(self.videos):
        if n_frame % self.downsampling_rates[i] == 0:
          try:
            video.write(frame)
          except Exception as e:
            exception(e, i, self.downsampling_rates[i])

    self.cap.release()
    for video in self.videos:
      video.close()

    return media

  def content_type(self):
    return "video"

  def name(self):
    return "video-downsample"
