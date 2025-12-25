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
import json
import threading

from sciveo.tools.logger import *


class GlobalConfiguration:
  config = None
  lock_config = threading.Lock()

  def __init__(self, name) -> None:
    home = os.path.expanduser('~')
    self.name = name.lower()
    self.base_path = os.path.join(home, f'.{self.name}')
    self.data = {}

    self.default = {
      "api_base_url": "https://sciveo.com",
      "log_min_level": "DEBUG"
    }

    try:
      self.read_local_files()
      self.read_environment()
    except Exception as e:
      exception(e)

  @staticmethod
  def get(name='sciveo', reload=False):
    with GlobalConfiguration.lock_config:
      if GlobalConfiguration.config is None or reload:
        GlobalConfiguration.config = GlobalConfiguration(name)
      return GlobalConfiguration.config

  @staticmethod
  def set(k, v):
    with GlobalConfiguration.lock_config:
      GlobalConfiguration.config.data[k] = v

  def __getitem__(self, key):
    key = key.lower()
    return self.data.get(key, self.default.get(key, None))

  def save_kv(self, key, value):
    key = key.strip().lower().replace(f"{self.name}_", "")
    value = value.strip()
    self.data[key] = value

  def read_environment(self):
    for k, v in os.environ.items():
      self.save_kv(k, v)

  def read_file(self, path):
    with open(path, 'r') as fp:
      lines = fp.readlines()
      for line in lines:
        parts = line.strip().split('=')
        if len(parts) == 2:
          self.save_kv(parts[0], parts[1])

  def read_json(self, path):
    data_json = {}
    with open(path, 'r') as fp:
      data_json = json.load(fp)
    for key, value in data_json.items():
      self.save_kv(key, value)

  def read_local_files(self):
    if os.path.exists(self.base_path):
      for path, _, files in os.walk(self.base_path):
        for file_name in files:
          file_path = os.path.join(path, file_name)
          _, file_extension = os.path.splitext(file_name)
          if file_extension == ".json":
            self.read_json(file_path)
          else:
            self.read_file(file_path)


class ConfigurationArguments:
  def __init__(self, default, **kwargs) -> None:
    self.default = default
    self.arguments = {}
    for k, v in self.default.items():
      self.arguments[k] = kwargs.get(k, v)

  def __getitem__(self, key):
    return self.arguments[key]

  def __len__(self):
    return len(self.arguments)

  def __repr__(self):
    return self.arguments