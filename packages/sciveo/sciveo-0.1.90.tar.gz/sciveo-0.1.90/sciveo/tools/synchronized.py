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

import threading
import uuid
import copy
import json
import datetime

from sciveo.tools.logger import *


class BaseSynchronized:
  def __init__(self, tag=""):
    self.lock_data = threading.Lock()
    if tag:
      tag += "-"
    self._guid = "guid-{}{}-{}".format(tag, datetime.datetime.now().strftime("%Y-%m-%d"), str(uuid.uuid4()).replace("-", ""))

  def guid(self):
    with self.lock_data:
      return self._guid


class ListQueue(BaseSynchronized):
  def __init__(self, tag=""):
    super().__init__(tag)
    self.cv = threading.Condition()
    self.data = []

  def size(self):
    with self.cv:
      return len(self.data)

  def get_data(self):
    with self.cv:
      return copy.deepcopy(self.data)

  def push(self, data):
    with self.cv:
      self.data.append(data)
      self.cv.notify()

  def pop(self, timeout=None):
    with self.cv:
      self.cv.wait_for(predicate=lambda: len(self.data) > 0, timeout=timeout)
      if len(self.data) > 0:
        return self.data.pop(0)
      else:
        raise Exception(f"{type(self).__name__}::POP empty after timeout {timeout}")


class CounterSynchronized(BaseSynchronized):
  def __init__(self, tag=""):
    super().__init__(tag)
    self.data_sync = {}

  def inc(self, k):
    with self.lock_data:
      self.data_sync.setdefault(k, 0)
      self.data_sync[k] += 1

  def dec(self, k):
    with self.lock_data:
      self.data_sync.setdefault(k, 0)
      self.data_sync[k] -= 1

  def data(self):
    with self.lock_data:
      return copy.deepcopy(self.data_sync)


class CallbackSynchronized(BaseSynchronized):
  def __init__(self, tag=""):
    super().__init__(tag)
    self.callbacks = {}

  def hook(self, name, action):
    with self.lock_data:
      self.callbacks.setdefault(name, []).append(action)
      debug(self._guid, "hooked", name, action, self.callbacks)

  def __call__(self, name, data):
    with self.lock_data:
      for callback in self.callbacks.setdefault(name, []):
        try:
          callback(data)
        except Exception as e:
          exception([self], e, name, callback, data)


class DataSynchronized(BaseSynchronized):
  def __init__(self, tag=""):
    super().__init__(tag)
    self.data_sync = {}

  def size(self):
    with self.lock_data:
      return len(self.data_sync)

  def set_one(self, key, value):
    with self.lock_data:
      self.data_sync[key] = value

  def set(self, data):
    with self.lock_data:
      for k, v in data.items():
        self.data_sync[k] = v

  def setdefault(self, data):
    with self.lock_data:
      for k, v in data.items():
        self.data_sync.setdefault(k, v)

  def get(self, key):
    with self.lock_data:
      return self.data_sync.get(key, None)

  def pop(self, key):
    result = None
    with self.lock_data:
      try:
        result = self.data_sync.pop(key)
      except Exception as e:
        result = None
    return result

  def keys(self):
    with self.lock_data:
      return self.data_sync.keys()

  def data(self):
    with self.lock_data:
      return copy.deepcopy(self.data_sync)

  @staticmethod
  def fix_dict(data, list_to_json=[]):
    fixed_data = {}
    for k, v in data.items():
      if type(v) == str:
        v = v.replace("+", " ")
      if k in list_to_json:
        v = v.replace("\'", "\"")
        v = json.loads(v)
      fixed_data[k] = v
    return fixed_data

  @staticmethod
  def data2json(data, keys):
    for key in keys:
      if key in data:
        data[key] = json.loads(data[key].replace("+", " ").replace("\'", "\"").replace("True", "true").replace("False", "false"))
