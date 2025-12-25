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
import time

import numpy as np

from sciveo.tools.logger import *


class Dataset:
  current = None

  def __init__(self):
    self.info = {}

  def __call__(self, d):
    if isinstance(d, dict):
      self.update(d)
    else:
      for attr in ["shape", "columns"]:
        if hasattr(d, attr):
          self.update({
            attr: list(getattr(d, attr)),
          })

  def update(self, d):
    self.info.update(d)

  @staticmethod
  def get(info={}):
    if Dataset.current is None:
      Dataset.current = Dataset()
    Dataset.current(info)
    return Dataset.current