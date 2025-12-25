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
import boto3

from sciveo.tools.logger import *
from sciveo.tools.array import copy_dict_values
from sciveo.tools.os import *
from sciveo.tools.http import *
from sciveo.media.pipelines.pipeline import *
from sciveo.media.pipelines.queues import MediaJobState
from sciveo.media.pipelines.postprocessors.base import *
from sciveo.media.pipelines.base import ApiContent


class S3UploadPostprocessor(BasePostprocessor):
  def __init__(self, job, config, max_progress) -> None:
    super().__init__(job, config, max_progress)
    self.s3 = boto3.client('s3')

  def run(self):
    progress_per_iteration = self.max_progress / max(len(self.job["output"]), 1)
    for content_output in self.job["output"]:
      try:
        remote_path = f"{content_output['owner']}/{content_output['key']}"
        debug("AWS S3 UPD", content_output["local_path"], "=>", content_output["bucket"], remote_path)
        self.s3.upload_file(content_output["local_path"], content_output["bucket"], remote_path)
        # TODO: Create tmp path cleaning with some frequency (let say 1 day) daemon instead, this will work as a s3 cache
        # rm_file(content_output["local_path"])
      except Exception as e:
        exception(e, "file error", content_output)
      MediaJobState.queue().inc_progress(self.job["id"], progress_per_iteration)

  def name(self):
    return "s3-upload"


class AppendContentPostprocessor(BasePostprocessor):
  def __init__(self, job, config, max_progress) -> None:
    super().__init__(job, config, max_progress)
    self.api = ApiContent()

  def run(self):
    progress_per_iteration = self.max_progress / max(len(self.job[self.name()]), 1)
    for content_output in self.job[self.name()]:
      w, h = (content_output.get("w", 320), content_output.get("h", 240))
      content_output.setdefault("width", w)
      content_output.setdefault("height", h)
      content_output.setdefault("name", f"{content_output['processor']} {content_output['content_type']} {w}x{h} ")

      content_output["is_public"] = self.job["is_public"]
      content_output["access_level"] = self.job["access_level"]

      content_output.setdefault("data", {})
      copy_dict_values(content_output, content_output["data"], ["bucket", "key", "layout", "processor", "processors", "description"])

      self.api.create(content_output)
      MediaJobState.queue().inc_progress(self.job["id"], progress_per_iteration)

  def name(self):
    return "append-content"


class ResizedResolutionsPostprocessor(BasePostprocessor):
  def __init__(self, job, config, max_progress) -> None:
    super().__init__(job, config, max_progress)
    self.api = ApiContent()

  def run(self):
    if self.name() not in self.job or len(self.job[self.name()]) == 0:
      return

    contents = []
    for media in self.job[self.name()]:
      content = {}
      copy_dict_values(media, content, ["guid", "heights", "content_type", "owner"])
      contents.append(content)

    data = {
      "owner": self.job["owner"],
      "contents": contents
    }

    self.api.resolution(data)

  def name(self):
    return "resized-resolutions"


class UpdateContentDataPostprocessor(BasePostprocessor):
  def __init__(self, job, config, max_progress) -> None:
    super().__init__(job, config, max_progress)
    self.api = ApiContent()

  def run(self):
    media_list = {}
    for media in self.job[self.name()]:
      media_list[media["guid"]] = media

    progress_per_iteration = self.max_progress / max(len(media_list), 1)

    for guid, media in media_list.items():
      if "data" in media:
        data = {"data": media["data"]}
        self.api.update(media, data)
      MediaJobState.queue().inc_progress(self.job["id"], progress_per_iteration)

  def name(self):
    return "update-content-data"


class ChannelCreateSimplePostprocessor(BasePostprocessor):
  def __init__(self, job, config, max_progress) -> None:
    super().__init__(job, config, max_progress)
    self.api = ApiContent()

  def run(self):
    children = []
    child_idx = 0
    for content_output in self.job["output"]:
      child_idx += 1
      child = {}
      # debug("content_output", content_output)
      copy_dict_values(content_output, child, ["content_type", "owner", "bucket", "key", "layout", "processor", "processors"])
      child["width"] = content_output["w"]
      child["height"] = content_output["h"]
      child["name"] = f"{child_idx} {content_output['content_type']} {content_output['w']}x{content_output['h']} "
      children.append(child)

    channel_name = ""
    # for c in self.job["configuration"]:
    #   channel_name += f"{c['name']}->"
    channel_name += f" {self.job['content_name']}"

    data = {
      "parent": self.job["content_id"],
      "owner": self.job["owner"],
      "content_type": "channel",
      "name": channel_name,
      "is_public": self.job["is_public"],
      "children": children
    }
    self.api.create(data)

  def name(self):
    return "channel-create-simple"
