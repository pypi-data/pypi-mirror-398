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
import math
import numpy as np

from sciveo.tools.logger import *
from sciveo.tools.common import *
from sciveo.media.pipelines.processors.base import *
from sciveo.media.pipelines.queues import MediaJobState


class AlbumInImage(BaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)
    self.default.update({
      "max_col": 10,
      "width": 640,
      "height": 640,
      "bucket": "smiveo-video"
    })

  def create_album_image(self, images, width, height, max_col=10):
    num_images = len(images)
    num_cols = min(max_col, math.ceil(np.sqrt(num_images)))
    num_rows = (num_images + num_cols - 1) // num_cols
    w = width // num_cols
    h = height // num_rows
    debug("create_album_image", "num_images", num_images, "num_cols", num_cols, "num_rows", num_rows, "WH", (w, h))
    resized_images = [cv2.resize(image, (w, h), interpolation=cv2.INTER_AREA) for image in images]
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    for i, image in enumerate(resized_images):
      x = (i % num_cols) * w
      y = (i // num_cols) * h
      canvas[y:y + image.shape[0], x:x + image.shape[1], :] = image
    return canvas

  def run(self, job, input):
    if len(input) == 0:
      return []

    progress_per_media = self.max_progress / len(input)
    debug("run", job["id"], progress_per_media)

    images = []
    videos = []

    # TODO: Handle different resolutions and aspect ratios
    for i, media in enumerate(input):
      if media["content_type"] == "image":
        images.append(media)
      if media["content_type"] == "video":
        videos.append(media)

    max_col = self["max_col"]
    width = self["width"]
    height = self["height"]

    list_frames = []

    for media in images:
      try:
        frame = cv2.imread(media["local_path"])
        list_frames.append(frame)
      except Exception as e:
        exception(e)

    for media in videos:
      try:
        cap = cv2.VideoCapture(media["local_path"])
        frames_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_idx = frames_count // 2
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if ret:
          list_frames.append(frame)
        cap.release()
      except Exception as e:
        exception(e)
      MediaJobState.queue().inc_progress(job["id"], progress_per_media)

    parent_guid = job['content_id']
    guid = f"{self.name()}-{parent_guid}"
    key = f"{guid}.jpg"
    bucket = self["bucket"]

    album_image = self.create_album_image(list_frames, width, height, max_col=max_col)
    album_image_local_path = os.path.join(self.base_tmp_path, key)
    cv2.imwrite(album_image_local_path, album_image, [cv2.IMWRITE_JPEG_QUALITY, 100])

    media = {
      "guid": guid,
      "parent": parent_guid,
      "content_type": "image",
      "owner": job["owner"],
      "local_path": album_image_local_path,
      "w": width, "h": height,
      "height": height,
      "key": key,
      "bucket": bucket,
      "processor": self.name(),
      "layout": {"name": self.name(), "height": height, **self["layout"]}
    }

    if self["output"]:
      job["output"].append(media)
    if self["append-content"]:
      job["append-content"].append(media)
    return [media]

  def content_type(self):
    return "image"

  def name(self):
    return "album-in-image"

  def is_append_processor(self):
    return False