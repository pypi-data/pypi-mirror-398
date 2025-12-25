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
import re
import datetime

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

from sciveo.tools.logger import *
from sciveo.tools.common import *
from sciveo.media.pipelines.processors.base import *
from sciveo.media.pipelines.queues import MediaJobState
from sciveo.media.pipelines.base import ApiContent


class MediaInfo(BaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)
    self.api = ApiContent()
    self.default = {}

  def update(self, media, info):
    data = {"data": {"info": info}}

    if "datetime" in info:
      try:
        data["created_at"] = datetime.datetime.strptime(info["datetime"], '%Y:%m:%d %H:%M:%S')
      except Exception:
        pass

    debug("update", media, data)
    self.api.update(media, data)

  def fix_value(self, value):
    if isinstance(value, bytes):
      try:
        value = value.decode('utf-8')
      except Exception:
        value = ""
    if isinstance(value, str):
      value = re.sub(r'[\x00-\x1f\x7f-\xff]', '', value)
    if isinstance(value, tuple):
      value = list(value)
    if isinstance(value, list):
      result = []
      for v in value:
        result.append(self.fix_value(v))
      value = result
    if isinstance(value, dict):
      result = {}
      for k, v in value.items():
        result[k] = self.fix_value(v)
      value = result
    return value

  def run(self, job, input):
    if len(input) == 0:
      return []

    images = []
    videos = []

    for i, media in enumerate(input):
      if media["content_type"] == "image":
        images.append(media)
      if media["content_type"] == "video":
        videos.append(media)

    progress_per_media = self.max_progress / (len(images) + len(videos))
    debug("run", job["id"], progress_per_media)

    for media in images:
      try:
        info = { "size": os.path.getsize(media["local_path"]) }

        with Image.open(media["local_path"]) as img:
          info["width"] = img.width
          info["height"] = img.height
          info["format"] = img.format
          info["layers"] = img.layers
          info["mode"] = img.mode

          if "dpi" in img.info:
            info["dpi"] = list(img.info["dpi"])

          exif = img._getexif()
          if exif:
            info["exif"] = {}
            for tag, value in exif.items():
              decoded_tag = str(TAGS.get(tag, tag))

              if decoded_tag == "GPSInfo":
                gps_data = {}
                for t, v in value.items():
                  sub_decoded = GPSTAGS.get(t, t)
                  gps_data[sub_decoded] = v
                value = gps_data

              value = self.fix_value(value)

              info["exif"][decoded_tag] = value

            for k in ["DateTime", "DateTimeOriginal", "DateTimeDigitized"]:
              if k in info["exif"]:
                info["datetime"] = info["exif"][k]
                break

        self.update(media, info)
        MediaJobState.queue().inc_progress(job["id"], progress_per_media)
      except Exception as e:
        exception(e)

    for media in videos:
      try:
        info = { "size": os.path.getsize(media["local_path"]) }

        cap = cv2.VideoCapture(media["local_path"])
        frames_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))

        info["frames_count"] = frames_count
        info["fps"] = fps
        info["vls"] = frames_count / fps

        ret, frame = cap.read()
        if ret:
          info["width"] = frame.shape[1]
          info["height"] = frame.shape[0]

        cap.release()

        self.update(media, info)
        MediaJobState.queue().inc_progress(job["id"], progress_per_media)
      except Exception as e:
        exception(e)

    return []

  def content_type(self):
    return "media"

  def name(self):
    return "media-info"
