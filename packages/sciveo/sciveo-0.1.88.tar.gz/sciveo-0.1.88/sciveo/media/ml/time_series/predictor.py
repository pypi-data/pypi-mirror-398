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
import joblib

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
from sciveo.media.ml.time_series.dataset import *


class TimeSeriesPredictor:
  def __init__(self, model_path):
    self.model_path = model_path

    self.model_data = joblib.load(self.model_path)

    self.window_generator = WindowGenerator(
      input_width=self.model_data["window"]["input_width"],
      label_width=0,
      shift=self.model_data["window"]["shift"]
    )

  def predict(self, df, x_expand_factor=2):
    normalizer = self.model_data["normalizer"]
    L = self.model_data["window"]["input_width"]
    F = len(self.model_data["columns"])
    predict_df = df[-L:][self.model_data["columns"]]
    predict_df.index = pd.to_datetime(predict_df.index)

    x_plot = list(predict_df.index)
    x_plot = self.expand_dates(x_plot, x_expand_factor)

    predict_df = normalizer.transform(predict_df)

    X = predict_df.values.reshape((1, L, F)).astype('float32')
    X = tf.convert_to_tensor(X)

    predictions = self.model_data["model"](X)
    predictions = normalizer.inverse(predictions)
    X = normalizer.inverse(X)
    debug(f"predict {L} shapes: predict_df[{predict_df.shape}] x_plot[{len(x_plot)}] X[{X.shape}] predictions[{predictions.shape}]")
    return predictions, X, x_plot

  def expand_dates(self, list_dates, expand_factor):
    n = len(list_dates) * expand_factor
    delta = (list_dates[1] - list_dates[0]) # TODO: create more robust delta computation, currently assume equidistant
    expanded_dates = [list_dates[0] + i * delta for i in range(n)]
    return expanded_dates

  def plot(self, predictions, X, x_plot, plot_col_index, labels=None, image_local_path=None, dpi=100, width=640, height=480):
    L = X.shape[1]
    plot_col = self.model_data["columns"][plot_col_index]
    plt.figure(figsize=(12, 8), dpi=dpi)

    plt.subplot(1, 1, 1)
    plt.ylabel(f'{plot_col}')

    plt.plot(
      x_plot[:L], X[0, :, plot_col_index],
      label='X', marker='.', zorder=-10
    )

    plt.scatter(
      x_plot[L:], predictions[0, :, plot_col_index],
      marker='X', edgecolors='k', label='Predictions',
      c='#ff7f0e', s=64
    )

    if labels is not None:
      plt.scatter(
        x_plot[L:], labels[0, :, plot_col_index],
        edgecolors='k', label='Labels', c='#2ca02c', s=64
      )

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.legend(title=plot_col, loc='upper left')
    plt.xlabel("date time")

    if image_local_path is not None:
      plt.savefig(image_local_path, format='png', dpi=dpi, bbox_inches='tight', pad_inches=0)
      debug("plot savefig", image_local_path)
    else:
      plt.show()
    plt.close()