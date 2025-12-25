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

from sciveo.tools.logger import *
from sciveo.tools.http import *


class BaseLayout:
  def post(self, url, data):
    headers = {
      "Auth-Token": os.environ['MEDIA_API_AUTH_TOKEN']
    }
    response = POST(url, data=data, headers=headers)
    debug("post response", response)
    return response