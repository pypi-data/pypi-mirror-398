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

import tensorflow as tf
from tensorflow import keras

from sciveo.tools.logger import *
from sciveo.tools.array import *
from sciveo.media.ml.encoders.normalizer import *
from sciveo.media.ml.time_series.window_generator import *
from sciveo.media.ml.base import BaseDataSet


class TimeSeriesDataSet(BaseDataSet):
  def __init__(self, data, time_col, format='%Y-%m-%d %H24:%M:%S', columns=None, new_period_columns=True):
    super().__init__(data, columns)

    debug(f"time_col [{time_col}] format[{format}]")
    debug("columns", self.data.columns)

    self.time_col = time_col
    if "datetime" not in str(self.data[time_col].dtype):
      self.data[time_col] = pd.to_datetime(self.data[time_col], format=format)
    self.data = self.data.set_index(time_col).sort_index()
    self.date_time = self.data.index

    if new_period_columns:
      timestamp_s = self.date_time.map(pd.Timestamp.timestamp)
      hour = 60 * 60
      day = 24 * hour
      periods = [
        hour,
        day,
        91.310625 * day,
        365.2425 * day
      ]
      for period in periods:
        self.data[f"period-sin-{period / day}"] = np.sin(timestamp_s * (2 * np.pi / period))
        # self.data[f"period-cos-{period / day}"] = np.cos(timestamp_s * (2 * np.pi / period))

    self.columns = self.data.columns

    self.normalizer.fit(self.data)

  def plots(self, max_columns=3, max_points=120):
    plot_cols = list(self.data.columns)[:max_columns]
    plot_features = self.data[plot_cols]
    plot_features.index = self.date_time
    _ = plot_features.plot(subplots=True)

    plot_features = self.data[plot_cols][:max_points]
    plot_features.index = self.date_time[:max_points]
    _ = plot_features.plot(subplots=True)
