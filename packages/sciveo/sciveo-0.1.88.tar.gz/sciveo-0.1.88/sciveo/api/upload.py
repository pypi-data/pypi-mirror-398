#
# Pavlin Georgiev, Softel Labs
#
# This is a proprietary file and may not be copied,
# distributed, or modified without express permission
# from the owner. For licensing inquiries, please
# contact pavlin@softel.bg.
#
# 2023
#

import os
import json
from urllib import request, parse
from urllib.error import HTTPError
import requests

from sciveo.tools.logger import *
from sciveo.api.base import *


class APIFileUploader:
  api = None

  def __init__(self, content_type, local_path, parent_guid):
    self.content_type = content_type
    self.local_path = local_path
    self.parent_guid = parent_guid
    if APIFileUploader.api is None:
      APIFileUploader.api = APIRemoteClient()

  def __call__(self):
    file_name = self.local_path.split("/")[-1]
    url_presigned_post = f"aws/s3/presigned_post/?content_type={self.content_type}&file_name={file_name}"
    presigned_post = APIFileUploader.api.GET(url_presigned_post)
    debug("upload presigned_post", url_presigned_post, "=>", presigned_post)
    if "fields" in presigned_post:
      response = None
      with open(self.local_path, 'rb') as fh:
        files = { 'file': (presigned_post['fields']['key'], fh) }
        response = requests.post(presigned_post['url'], data=presigned_post['fields'], files=files)
      if response.status_code == 204:
        debug(self.content_type, self.local_path, "uploaded")
        url_append = f"content/append/?content_type={self.content_type}&name={file_name}&key={presigned_post['fields']['key']}&parent_id={self.parent_guid}"
        result = APIFileUploader.api.GET(url_append)
        debug("upload", url_append, result, "appended")
      else:
        error("upload", self.content_type, self.local_path, "FAIL")

