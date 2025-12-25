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

import uuid
import datetime

from sciveo.tools.logger import *
from sciveo.tools.http import *


class BaseContentProcessor:
  def __init__(self, processor_config, max_progress) -> None:
    self.processor_config = processor_config
    self.max_progress = max_progress
    self.default = {
      "output": True, "append-content": True, "update-content": True,
      "force_processing": False, "layout": {}
    }

  def new_guid(self):
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S") + "-" + str(uuid.uuid4()).replace("-", "")

  def replace_ext(self, k, e=".aac"):
    k = k.replace(".mp4", e)
    k = k.replace(".MP4", e)
    k = k.replace(".mov", e)
    k = k.replace(".MOV", e)
    return k

  def next_content(self, media, tag=None, local_path=None, content_type=None, key=None, w=100, h=100, name="", args={}):
    if content_type is None:
      content_type = media['content_type']
    if key is None:
      key = media['key']

    if tag is None:
      guid = media['guid']
      parent_guid = None
    else:
      key = f"{tag}/{key}"
      guid = f"{tag}-{media['guid']}"
      if len(guid) > 128:
        guid = f"{tag}-{self.new_guid()}"
      parent_guid = media['guid']

    media.setdefault("next", [])

    media["next"].append(dict({
      "guid": guid,
      "content_type": content_type,
      "name": name,
      "description": name,
      "w": w, "h": h,
      "local_path": local_path,
      "key": key,
      "bucket": media["bucket"],
      "owner": media["owner"],
      "parent": parent_guid,
      "processor": self.name(),
      "processors": media["processors"],
      "layout": {"name": self.name(), **self["layout"]}
    }, **args))

  def content_type(self):
    return "media"

  def is_content_type(self, media):
    content_type = media["content_type"]
    if self.content_type() is None:
      return True
    elif isinstance(self.content_type(), list):
      return content_type in self.content_type()
    else:
      return self.content_type() == content_type

  def is_processor_run(self, job, media):
    return self.is_content_type(media) and (job["configuration"].get("force_processing", False) or self["force_processing"] or (self.append_name() not in media.get("processors", "")))

  def is_processor_output(self):
    return self["output"] or self["append-content"] or self["update-content"]

  def append_processor(self, media):
    media.setdefault("data", {})
    media["data"].setdefault("processors", "")
    media["data"]["processors"] += f" {self.append_name()}"
    media["data"]["processors"] = media["data"]["processors"].strip(' ')

  def is_append_processor(self):
    return True

  def name(self):
    return "media"

  def append_name(self):
    return self.name()

  def describe(self):
    return { "name": self.name(), "input_type": self.content_type(), "config": self.default }

  def __getitem__(self, name):
    return self.processor_config.get(name, self.default[name])

  def get(self, name, min_val=None, max_val=None):
    r = self[name]
    if min_val is not None:
      r = max(min_val, r)
    if max_val is not None:
      r = min(max_val, r)
    return r


class ApiContent:
  def __init__(self):
    self.headers = { "Auth-Token": os.environ['MEDIA_API_AUTH_TOKEN'] }
    self.url = f"{os.environ['MEDIA_API_BASE_URL']}/api/v1/content/"

  def read(self, url_postfix, limit=10, timeout=60):
    data = []
    page = 1
    pagination = None
    while(pagination is None or page <= pagination["total_pages"]):
      url = f"{self.url}?limit={limit}&page={page}&{url_postfix}"
      result = GET(url, headers=self.headers, timeout=timeout)
      if result and "pagination" in result:
        pagination = result["pagination"]
        data += result["data"]
      else:
        warning("reading finished too early", limit, page, result)
        break
      page += 1
      debug("read", result["pagination"], "data", len(data))
    return data

  def create(self, content):
    try:
      response = POST(self.url, data=content, headers=self.headers)
      # debug("create content response", response)
      return response
    except Exception as e:
      exception(e,  "create content", content)

  def update(self, media, content_data):
    try:
      content_id = media['guid']
      response = POST(f"{self.url}{content_id}/", data=content_data, headers=self.headers)
      # debug("update content response", response)
      return response
    except Exception as e:
      exception(e,  "update content", content_id, content_data)

  def resolution(self, data):
    try:
      response = POST(f"{self.url}resolution/", data=data, headers=self.headers)
      # debug("resolution response", response)
      return response
    except Exception as e:
      exception(e,  "resolution data", data)
