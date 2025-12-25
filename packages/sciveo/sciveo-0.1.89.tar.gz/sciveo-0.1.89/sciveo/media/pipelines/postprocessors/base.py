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
from sciveo.media.pipelines.base import BaseContentProcessor


class BasePostprocessor(BaseContentProcessor):
  def __init__(self, job, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)
    self.job = job
    self.default = {}

  def run(self):
    pass