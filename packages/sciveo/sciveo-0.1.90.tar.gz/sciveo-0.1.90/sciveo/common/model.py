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
import datetime

import numpy as np

from sciveo.tools.logger import *


class ModelInfo:
  def __init__(self, model):
    self.model = model
    self.info = {}

  def any(self):
    try:
      from tensorflow import keras
      import torch
      from sklearn.base import BaseEstimator

      if isinstance(self.model, keras.models.Model):
        return self.keras()
      elif isinstance(self.model, torch.nn.Module):
        return self.torch()
      elif isinstance(self.model, BaseEstimator):
        return self.scikit_info()
      else:
        return self.info
    except Exception as e:
      error(e)
    return self.info

  def keras(self):
    try:
      model_summary_list = []
      self.model.summary(print_fn=lambda x: model_summary_list.append(x))
      self.info = {
        "summary": self.html_from_list(model_summary_list[3:-1]),
      }
    except Exception as e:
      error(e)
    return self.info

  def scikit(self):
    try:
      for key, value in self.model.get_params().items():
        self.info[key] = value
    except Exception as e:
      error(e)
    return self.info

  def torch(self):
    return self.info

  def html_from_list(self, list_lines):
    html = ""
    for line in list_lines:
      html += f"<div>{line}</div>"
    return html

  def __call__(self):
    return self.info
