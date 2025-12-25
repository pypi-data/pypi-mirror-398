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

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import numpy as np
import pandas as pd

from sciveo.tools.logger import *
from sciveo.tools.array import *
from sciveo.media.ml.encoders.normalizer import *


class BaseDataSet:
  def __init__(self, data, columns=None):
    self.data = data
    self.normalizer = Normalizer()

    if columns is not None:
      self.data = self.data[columns]
    self.columns = self.data.columns

  def normalize(self):
    self.data = self.normalizer.transform(self.data)
  def denormalize(self, key):
    self.dataset[key] = self.normalizer.inverse(self.dataset[key])

  # Split dataset
  def split(self, ratios=[["train", 0.85], ["val", 0.10], ["test", 0.05]]):
    self.ratios = ratios
    self.dataset = {}
    prev_idx = 0
    for k, v in ratios:
      next_idx = prev_idx + int(self.data.shape[0] * v)
      self.dataset[k] = self.data[prev_idx:next_idx]
      prev_idx = next_idx

  def summary(self):
    return self.data.describe().transpose()[["count", "min", "max", "mean", "std", "25%", "50%", "75%"]]
