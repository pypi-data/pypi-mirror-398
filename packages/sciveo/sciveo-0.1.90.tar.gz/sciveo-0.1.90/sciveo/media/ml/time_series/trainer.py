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

import numpy as np
import pandas as pd

import tensorflow as tf
from tensorflow import keras

from sciveo.tools.logger import *
from sciveo.tools.array import *
from sciveo.media.ml.encoders.normalizer import *
from sciveo.media.ml.time_series.window_generator import *
from sciveo.media.ml.time_series.dataset import *


class TimeSeriesTrainer:
  def __init__(self, dataset, input_width, label_width, shift):
    self.dataset = dataset

    self.input_width = input_width
    self.label_width = label_width
    self.shift = shift

    self.window_generator = WindowGenerator(
      input_width=self.input_width,
      label_width=self.label_width,
      shift=self.shift
    )

    self.columns = self.dataset.columns
    self.window = {}
    for k, v in self.dataset.dataset.items():
      self.window[k] = self.window_generator.transform(v)

  def build_conv(self):
    num_features = self.dataset.data.shape[1]
    input_layer = tf.keras.layers.Input(shape=(None, num_features))
    x = tf.keras.layers.Lambda(lambda x: x[:, -3:, :])(input_layer)
    x = tf.keras.layers.Conv1D(256, activation='relu', kernel_size=(3))(x)
    x = tf.keras.layers.Dense(self.input_width * num_features, kernel_initializer=tf.initializers.zeros())(x)
    x = tf.keras.layers.Reshape([self.input_width, num_features])(x)

    model = tf.keras.Model(inputs=input_layer, outputs=x)
    debug("model", model.summary())
    return model

  def create(self):
    self.model = self.build_conv()
    self.model.compile(
      loss=tf.keras.losses.MeanSquaredError(),
      optimizer=tf.keras.optimizers.Adam(),
      metrics=[tf.keras.metrics.MeanAbsoluteError()]
    )

  def train(self, max_epochs=20, patience=2, progress_callback=None):
    callbacks=[
        tf.keras.callbacks.EarlyStopping(
          monitor='val_loss',
          patience=patience,
          mode='min'
        )
    ]

    if progress_callback is not None:
      callbacks.append(progress_callback)

    history = self.model.fit(
      self.window["train"],
      validation_data=self.window["val"],
      epochs=max_epochs,
      callbacks=callbacks
    )

    return history

  def save(self, base_model_path, tag):
    model_name = f"model-{self.input_width}-{tag}.timeseries"
    self.model_data = {
      "model": self.model,
      "name": model_name,
      "normalizer": self.dataset.normalizer,
      "columns": self.columns,
      "window": {
          "input_width": self.input_width,
          "label_width": self.label_width,
          "shift": self.shift
      }
    }

    model_path = f"{base_model_path}/{model_name}"
    joblib.dump(self.model_data, model_path)
    debug("saved", model_path)
    return model_name, model_path

  def evaluate(self):
    result = {}
    for k in ["val", "test"]:
      result[k] = self.model.evaluate(self.window["val"], verbose=0)
    return result

  @staticmethod
  def load(dataset, model_path):
    self.model_data = joblib.load(model_path)
    trainer = TimeSeriesTrainer(
      dataset,
      self.model_data["window"]["input_width"],
      self.model_data["window"]["label_width"],
      self.model_data["window"]["shift"]
    )

    trainer.model = self.model_data["model"]
    trainer.normalizer = self.model_data["normalizer"]

    return trainer
