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
from sciveo.media.pipelines.processors.base import *


class S3MediaDownload(BaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)
    self.s3 = boto3.client('s3')
    self.default.update({"output": False, "append-content": False, "update-content": False})

  def process(self, media):
    try:
      # debug("process", media)
      if "bucket" in media:
        remote_path = f"{media['owner']}/{media['key']}"
        local_path = os.path.join(self.base_tmp_path, remote_path.replace("/", "-"))
        if os.path.isfile(local_path):
          debug("SKIP", local_path)
        else:
          debug("process_job content, AWS S3 DWN", media["bucket"], remote_path, local_path)
          self.s3.download_file(media["bucket"], remote_path, local_path)

        self.next_content(media, local_path=local_path)
    except Exception as e:
      exception(e, media)
    return media

  def content_type(self):
    return None

  def name(self):
    return "s3-download"

  def is_append_processor(self):
    return False
