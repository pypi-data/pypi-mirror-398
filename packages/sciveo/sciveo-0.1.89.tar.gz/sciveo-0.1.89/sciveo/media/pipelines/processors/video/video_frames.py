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


class VideoFramesExtract(BaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)
    self.frames_idx = []
    self.default.update({"JPEG_QUALITY": 100, "frames-count": 10})

  def init_frames_idx_list(self, cap):
    frames_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    self.frames_idx = np.linspace(0, frames_count - 1, self["frames-count"], dtype=int) # TODO: make the policy configurable

  def process(self, media):
    self.media = media

    cap = cv2.VideoCapture(media["local_path"])
    self.init_frames_idx_list(cap)
    debug("process::frames_idx", self.frames_idx)

    for frame_idx in self.frames_idx:
      cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
      ret, frame = cap.read()
      if not ret:
        break

      local_path = self.add_suffix_to_filename(media["local_path"], frame_idx)
      local_path = self.replace_ext(local_path, ".jpg")
      remote_path = f"{frame_idx}/{self.media['key']}"
      remote_path = self.replace_ext(remote_path, ".jpg")

      cv2.imwrite(local_path, frame, [cv2.IMWRITE_JPEG_QUALITY, self["JPEG_QUALITY"]])
      self.next_content(self.media, frame_idx, local_path, content_type="image", key=remote_path, w=frame.shape[1], h=frame.shape[0])

    cap.release()

    return self.media

  def content_type(self):
    return "video"

  def name(self):
    return "video-frames-extract"
