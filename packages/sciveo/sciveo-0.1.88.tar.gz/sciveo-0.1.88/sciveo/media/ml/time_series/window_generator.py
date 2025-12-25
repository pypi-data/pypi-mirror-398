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
from sciveo.media.ml.encoders.normalizer import *


class WindowGenerator():
  def __init__(self, input_width, label_width, shift):
    self.input_width = input_width
    self.label_width = label_width
    self.shift = shift

    self.total_window_size = input_width + shift

    self.input_slice = slice(0, input_width)
    self.input_indices = np.arange(self.total_window_size)[self.input_slice]

    self.label_start = self.total_window_size - self.label_width
    self.labels_slice = slice(self.label_start, None)
    self.label_indices = np.arange(self.total_window_size)[self.labels_slice]

  def split_window(self, features):
    X = features[:, self.input_slice, :]
    Y_label = features[:, self.labels_slice, :]

    X.set_shape([None, self.input_width, None])
    Y_label.set_shape([None, self.label_width, None])

    return X, Y_label

  def transform(self, data):
    data = np.array(data, dtype=np.float32)
    ds = tf.keras.utils.timeseries_dataset_from_array(
      data=data,
      targets=None,
      sequence_length=self.total_window_size,
      sequence_stride=1,
      shuffle=True,
      batch_size=32,
    )
    ds = ds.map(self.split_window)
    return ds

  def __repr__(self):
    return '\n'.join([
        f'Total window size: {self.total_window_size}',
        f'Input indices: {self.input_indices}',
        f'Label indices: {self.label_indices}',
    ])

  def data(self, df=None, normalizer=None):
    result = getattr(self, 'data_', None)
    if result is None and df is not None:
      result = next(iter(self.transform(df)))
      self.data_ = result
    if normalizer is not None:
      self.normalizer_ = normalizer
    return result

  def predictions(self, model, X=None, Y_label=None):
    if X is None or Y_label is None:
      X, Y_label = self.data()
    self.predictions_ = model(X)

  def plot(self, plot_col, plot_col_index, X=None, Y_label=None, predictions=None, normalizer=None, max_subplots=10):
    if normalizer is None:
      normalizer = self.normalizer_
    if X is None or Y_label is None:
      X, Y_label = self.data()
    if predictions is None and getattr(self, 'predictions_', None) is not None:
      predictions = self.predictions_

    X_denorm = normalizer.inverse(X)
    Y_label_denorm = normalizer.inverse(Y_label)

    plt.figure(figsize=(12, 8))
    max_n = min(max_subplots, len(X))
    for n in range(max_n):
      plt.subplot(max_n, 1, n+1)
      plt.ylabel(f'{plot_col}')

      plt.plot(
        self.input_indices, X_denorm[n, :, plot_col_index],
        label='X', marker='.', zorder=-10
      )

      plt.scatter(
        self.label_indices, Y_label_denorm[n, :, plot_col_index],
        edgecolors='k', label='Y_label', c='#2ca02c', s=64
      )

      if predictions is not None:
        predictions_denorm = normalizer.inverse(predictions)
        plt.scatter(
          self.label_indices, predictions_denorm[n, :, plot_col_index],
          marker='X', edgecolors='k', label='Predictions',
          c='#ff7f0e', s=64
        )

      if n == 0:
        plt.legend()

    plt.xlabel("time")
