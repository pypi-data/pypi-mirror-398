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
from sciveo.media.pipelines.queues import MediaJobState


class VideoAlbum(BaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)
    self.default.update({
      "CRF": 20,
      "image-period": 10,
      "video-frames-count": 10,
      "height": 480, "width": 640,
      "bucket": "smiveo-video",
    })

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

    image_period = self["image-period"]
    video_frames_count = self["video-frames-count"]
    height = self["height"]
    width = self["width"]

    parent_guid = job['content_id']
    guid = f"{self.name()}-{parent_guid}"
    key = f"{guid}.mp4"
    bucket = self["bucket"]

    video_local_path = os.path.join(self.base_tmp_path, f"{guid}.mp4")
    video = VideoWriterFFMPEG.new(video_local_path, crf=str(self["CRF"]))

    for media in images:
      try:
        frame = cv2.imread(media["local_path"])
        frame_resized = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
        for i in range(image_period):
          video.write(frame_resized)
      except Exception as e:
        exception(e)
      MediaJobState.queue().inc_progress(job["id"], progress_per_media)

    for media in videos:
      try:
        cap = cv2.VideoCapture(media["local_path"])
        frames_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frames_idx = np.linspace(0, frames_count - 1, video_frames_count, dtype=int)

        for frame_idx in frames_idx:
          cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
          ret, frame = cap.read()
          if not ret:
            break

          frame_resized = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
          video.write(frame_resized)

        cap.release()
      except Exception as e:
        exception(e)
      MediaJobState.queue().inc_progress(job["id"], progress_per_media)

    video.close()

    media = {
      "guid": guid,
      "parent": parent_guid,
      "content_type": "video",
      "owner": job["owner"],
      "local_path": video_local_path,
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
    return ["video", "image"]

  def name(self):
    return "video-album"

  def is_append_processor(self):
    return False