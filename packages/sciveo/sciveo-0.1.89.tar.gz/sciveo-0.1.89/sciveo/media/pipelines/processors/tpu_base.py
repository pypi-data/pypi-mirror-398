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

import gc
import torch
from sciveo.tools.logger import *
from sciveo.media.pipelines.processors.base import *


class TPUBaseProcessor(BaseProcessor):
  def post_process(self):
    try:
      del self.model
    except:
      pass
    try:
      del self.pipe
    except:
      pass
    self.clear()

  def clear(self):
    debug("clear, cuda available", torch.cuda.is_available())
    if torch.cuda.is_available():
      gc.collect()
      torch.cuda.empty_cache()
      torch.cuda.ipc_collect()
      debug("torch.cuda cleared")
