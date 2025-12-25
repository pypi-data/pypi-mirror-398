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
from sciveo.tools.daemon import __upload_content__ as UPLOAD
from sciveo.tools.formating import format_elapsed_time
from sciveo.tools.hardware import HardwareInfo
from sciveo.common.configuration import Configuration
from sciveo.common.model import ModelInfo
from sciveo.content.dataset import Dataset
from sciveo.api.base import APIRemoteClient


class Experiment:
  def __init__(self, project_name, project_guid, config):
    self.project_name = project_name
    self.project_guid = project_guid
    self.config = config
    self.guid = None

    self.default_score = -1e100 # TODO: It will be best to have None for default score and loss
    self.default_loss = 1e100

    self.start_at = time.time()

    self.data = {
      "experiment": {
        "log": [],
        "config": self.config(),
        "eval": {
          "score": self.default_score,
          "loss": self.default_loss,
        },
        "compute": HardwareInfo()(),
        "plots": {},
        "start_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      }
    }

    # TODO: Consider better experiment naming
    # perhaps include some eval
    self.name = self.config.name
    debug("init", self.name)

  def on_guid(self, guid):
    self.guid = guid

  def close(self):
    self.end_at = time.time()
    self.elapsed = self.end_at - self.start_at

    self.data["experiment"]["end_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    self.data["experiment"]["elapsed"] = format_elapsed_time(self.elapsed)
    self.data["experiment"]["dataset"] = Dataset.get().info
    debug("close", self.name)

  def append(self, d):
    self.data["experiment"]["log"].append(d)

  # EVAL API
  def eval(self, key, value, **kwargs):
    self.data["experiment"]["eval"][key] = value
    for k, v in kwargs.items():
      self.data["experiment"]["eval"][k] = v
  # Score value (no matter of its true meaning) which is used for experiments sorting.
  def score(self, value):
    score_value =  1 / (1 + np.exp(-value)) # [0.0;1.0]
    self.eval("score", score_value)
    self.eval("loss", (1.0 / score_value) - 1.0)
  # Loss value (inverse of the score in general meaning) loss=[0.0;1.0]
  def loss(self, value):
    self.eval("loss", value)
    self.score(1.0 / (1.0 + value))

  # Model API
  def model(self, m):
    self.data["experiment"]["model"] = ModelInfo(m).any()
  def model_keras(self, m):
    self.data["experiment"]["model"] = ModelInfo(m).keras()
  def model_torch(self, m):
    self.data["experiment"]["model"] = ModelInfo(m).torch()

  # LOG API
  def log(self, data, val=None, *args, **kwargs):
    if isinstance(data, dict):
      self.log_dict(data)
    else:
      self.log_any(data, val, *args, **kwargs)
  def log_dict(self, data):
    self.append(data)
  def log_any(self, data, val=None, *args, **kwargs):
    if val is None:
      self.append(data)
    else:
      self.append({data: val})
    for a in args:
      self.append(a)
    for k, v in kwargs.items():
      self.append({k: v})

  # Charts and Plots API
  def plot(self, name, data, render=None):
    # if isinstance(data, pd.DataFrame):
    #   self.data["experiment"]["plots"][name] = {"df": data.to_dict(orient='split')}
    if isinstance(data, dict):
      self.data["experiment"]["plots"][name] = {"dict": self.check_plot_x(data)}
    elif isinstance(data, list):
      # TODO: Append X as sequence if just Y is provided
      self.data["experiment"]["plots"][name] = {"list": {data[0][0]: data[0][1], data[1][0]: data[1][1]}}

    if render:
      self.data["experiment"]["plots"][name]["render"] = render

  def check_plot_x(self, data):
    # if "X" in data:
    #   if isinstance(data["X"][0], pd.Timestamp):
    #     data["X"] = [ts.strftime('%Y-%m-%d %H:%M:%S') for ts in data["X"]]
    return data

  # Datasets API
  def dataset(self, d):
    return Dataset.get(d)


class RemoteExperiment(Experiment):
  def __init__(self, project_name, project_guid, config):
    super().__init__(project_name, project_guid, config)

    self.api = APIRemoteClient()
    self.uploader = None

    remote_data = {
      "name": self.name,
      "data": self.data
    }
    if self.project_guid is not None:
      remote_data["project_guid"] = self.project_guid
    else:
      remote_data["project_name"] = self.project_name
    result = self.api.POST_SCI("experiment", remote_data)
    debug("init", self.name, "api", result)
    if result and "error" not in result:
      if result["name"] == self.name:
        self.on_guid(result["guid"])
      else:
        error("Project name mismatch", result, self.name)
    else:
      error("init", self.name, "api", result)

  def close(self):
    super().close()
    remote_data = {
      "guid": self.guid,
      "project_guid": self.project_guid,
      "data": self.data
    }
    result = self.api.POST_SCI("experiment", remote_data)
    debug("close", self.name, "api", result)

  def on_guid(self, guid):
    super().on_guid(guid)

  # UPLOAD API
  def upload(self, content_type, local_path):
    if self.guid is not None:
      UPLOAD(content_type, local_path, self.guid)
    else:
      error("upload", local_path)
  def upload_image(self, local_path):
    self.upload("image", local_path)
  def upload_file(self, local_path):
    self.upload("file", local_path)
  def upload_dataset(self, local_path):
    self.upload("dataset", local_path)
