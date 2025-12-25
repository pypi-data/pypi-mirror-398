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


class ImageResize(BaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)
    self.default.update({"heights": [720, 480, 320], "JPEG_QUALITY": 100})

  def process(self, media):
    local_path = media["local_path"]

    frame = cv2.imread(local_path)

    for h in self["heights"]:
      try:
        h, w = get_frame_resolution(frame, h)

        tag = f"resized-{h}"
        resized_local_path = self.add_suffix_to_filename(local_path, tag)

        frame_resized = cv2.resize(frame, (w, h), interpolation=cv2.INTER_AREA)
        cv2.imwrite(resized_local_path, frame_resized, [cv2.IMWRITE_JPEG_QUALITY, self["JPEG_QUALITY"]])

        self.next_content(media, tag, resized_local_path, w=w, h=h)
      except Exception as e:
        exception(e, h)

    return media

  def is_resizer(self):
    return True

  def content_type(self):
    return "image"

  def name(self):
    return "image-resize"
