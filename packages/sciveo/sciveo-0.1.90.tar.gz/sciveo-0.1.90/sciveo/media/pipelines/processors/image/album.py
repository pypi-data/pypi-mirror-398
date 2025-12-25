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

import os
import cv2
import datetime

from sciveo.tools.logger import *
from sciveo.media.pipelines.base import ApiContent
from sciveo.media.pipelines.processors.base import BaseProcessor


class Album(BaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)
    self.children = []
    self.api = ApiContent()
    self.default.update({
      "wsize": 8,
      "height": 32,
      "JPEG_QUALITY": 100,
      "channel": False
    })

    self.wsize = self["wsize"]
    self.height = self["height"]
    self.jpeg_quality = self["JPEG_QUALITY"]

  def next_content(self, media, tag, local_path):
    key = f"{tag}/{media['key']}"
    guid = f"{tag}-{media['guid']}"
    media.setdefault("next", [])
    media_next = {
      "guid": guid,
      "content_type": media['content_type'],
      "w": self.height, "h": self.height,
      "local_path": local_path,
      "key": key,
      "name": f"album {media['content_type']} {tag}",
      "bucket": media["bucket"],
      "owner": media["owner"],
      "parent": media['guid'],
      "processor": self.name(),
      "layout": {"name": self.name(), "height": self.height, **self["layout"]}
    }
    media["next"].append(media_next)
    self.children.append(media_next)

  def process(self, media):
    try:
      local_path = media["local_path"]
      frame = cv2.imread(local_path)

      tag = f"resized-{self.height}"
      resized_local_path = self.add_suffix_to_filename(local_path, tag)

      frame_resized = cv2.resize(frame, (self.height, self.height), interpolation=cv2.INTER_AREA)
      cv2.imwrite(resized_local_path, frame_resized, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])

      self.next_content(media, tag, resized_local_path)
    except Exception as e:
      exception(e, self.wsize, self.height)
    return media

  def append(self, job, parent=None):
    if parent is None:
      parent = job["content_id"]

    album = {
      "guid": f"{self.name()}-{parent}",
      "parent": parent,
      "owner": job["owner"],
      "content_type": "album",
      "name": f"Album {datetime.datetime.now().strftime('%Y-%m-%d')}",
      "is_public": job["is_public"],
      "layout": {"name": self.name(), "wsize": self.wsize, "height": self.height, **self["layout"]},
      "wsize": self.wsize,
      "height": self.height,
      "children": self.children
    }
    response = self.api.create(album)
    return response

  def new_channel(self, job):
    channel = {
      "parent": job["content_id"],
      "owner": job["owner"],
      "is_public": job["is_public"],
      "content_type": "channel",
      "name": f"Album {datetime.datetime.now().strftime('%Y-%m-%d')}",
    }
    response = self.api.create(channel)

    if "error" in response:
      error("new channel failed", channel, response)
    else:
      response = self.append(job, parent=response["guid"])

    return response

  def run(self, job, input):
    next_media = super().run(job, input)

    if self["channel"]:
      self.new_channel(job)
    else:
      self.append(job)

    return next_media

  def is_resizer(self):
    return True

  def content_type(self):
    return "image"

  def name(self):
    return "image-album"

  def is_append_processor(self):
    return False
