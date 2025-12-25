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
from sciveo.api.base import *
from sciveo.common.configuration import Configuration
from sciveo.content.experiment import Experiment, RemoteExperiment
from sciveo.content.dataset import Dataset


class ProjectBase:
  def __init__(self, project_name):
    self.project_name = project_name
    self.guid = None
    self.list_content_size = 0
    self.config = Configuration()

    self.list_experiments = []

    self.project_data = {
      "name": project_name,
      "project": {
        "experiments": [],
        "sort": {
          "experiment": "score"
        },
      }
    }

    debug("init", self.project_name)

  def open(self):
    debug("open", self.project_name)
    self.current_experiment = Experiment(self.project_name, self.guid, self.config)
    return self.current_experiment

  def close(self):
    debug("close", self.project_name)
    self.project_data["project"]["dataset"] = Dataset.get().info
    self.current_experiment.close()
    self.list_experiments.append(self.current_experiment)

  def __enter__(self):
    return self.open()

  def __exit__(self, exc_type, exc_value, traceback):
    self.close()

  def dataset(self, d):
    return Dataset.get(d)


class RemoteProject(ProjectBase):
  def __init__(self, project_name, parent_id=None):
    super().__init__(project_name)

    self.api = APIRemoteClient()

    remote_data = {
      "name": project_name,
      "data": self.project_data
    }
    if parent_id is not None:
      remote_data["parent_id"] = parent_id
    result = self.api.POST_SCI("project", remote_data)
    debug("init api", result)
    if result and "error" not in result:
      if result["name"] == project_name:
        self.guid = result["guid"]
        self.list_content_size = result["list_content_size"]
      else:
        error("Project name mismatch", result, project_name)
    else:
      error("api", remote_data, result)

  def open(self):
    debug("open", self.project_name)
    self.current_experiment = RemoteExperiment(self.project_name, self.guid, self.config)
    return self.current_experiment

  def close(self):
    self.project_data["project"]["experiments"].append(self.current_experiment.name)
    super().close()

    remote_data = {
      "name": self.project_name,
      "guid": self.guid,
      "data": self.project_data
    }
    result = self.api.POST_SCI("project", remote_data)
    debug("close", self.project_name, "api", result)


class LocalProject(ProjectBase):
  def __init__(self, project_name):
    super().__init__(project_name)

  def close(self):
    self.project_data["project"]["experiments"].append(self.current_experiment.data)
    super().close()