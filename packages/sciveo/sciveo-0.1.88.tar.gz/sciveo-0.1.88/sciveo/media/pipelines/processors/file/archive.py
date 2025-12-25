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
import zipfile
import boto3

from sciveo.tools.logger import *
from sciveo.media.pipelines.processors.base import *


class FileArchiveZIP(BaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)
    self.s3 = boto3.client('s3')

  def upload(self, content_output):
    zip_remote_path = f"{content_output['owner']}/{content_output['key']}"
    debug("AWS S3 UPD", content_output["local_path"], "=>", content_output["bucket"], zip_remote_path)
    self.s3.upload_file(content_output["local_path"], content_output["bucket"], zip_remote_path)
    os.remove(content_output["local_path"])
    debug("RM", content_output["local_path"])

  def run(self, job, input):
    zip_file_name = f"{job['content_id']}.zip"
    zip_key = zip_file_name
    zip_path = os.path.join(self.base_tmp_path, zip_file_name)
    progress_per_media = self.max_progress / max(1, len(input))
    debug("run", job["id"], progress_per_media, "input", input)
    try:
      with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for i, media in enumerate(input):
          if self.is_content_type(media) and zip_key != media['key']:
            try:
              if "bucket" in media:
                remote_path = f"{media['owner']}/{media['key']}"
                file_name = remote_path.replace("/", "-")
                local_path = os.path.join(self.base_tmp_path, file_name)
                if os.path.isfile(local_path):
                  debug("SKIP", local_path)
                else:
                  debug("process_job content, AWS S3 DWN", media["bucket"], remote_path, local_path)
                  self.s3.download_file(media["bucket"], remote_path, local_path)
                zipf.write(local_path, arcname=file_name)
            except Exception as e:
              exception(e, media)
          else:
            debug("Media SKIP", media)
          MediaJobState.queue().inc_progress(job["id"], progress_per_media)

      content_output = {
        "name": f"ZIP {job['content_name']}",
        "guid": f"zip-{job['content_id']}",
        "content_type": "file",
        "local_path": zip_path,
        "key": zip_key,
        "bucket": "smiveo-file",
        "owner": job["owner"],
        "parent": job['content_id'],
        "processor": self.name(),
        "layout": {"name": self.name(), **self["layout"]},
        "data": {
          "info": {
            "size": os.path.getsize(zip_path)
          }
        }
      }

      self.upload(content_output)
      # job["output"] += content_output

      job["append-content"].append(content_output)

    except Exception as e:
      exception(e, zip_path)
    return []

  def content_type(self):
    return None

  def name(self):
    return "archive-zip"
