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

import unittest
import numpy as np

from sciveo.tools.logger import *
from sciveo.common.sampling import RandomSampler, GridSampler, AutoSampler
from sciveo.content.project import RemoteProject, LocalProject
from sciveo.common.optimizers import AdamOptimizer, BaseOptimizer


class TestSampling(unittest.TestCase):
  def check_sampling_names(self, class_name):
    config = {
        "booster": {
            "values": ["gbtree", "gblinear"]
        },
        "booster2": ["gbtree", "gblinear"],
        "learning_rate": {
          "min": 0.001,
          "max": 1.0,
          "num": 100
        },
        "gamma": {
          "min": 0.001,
          "max": 1.0,
          "num": 1000
        },
        "max_depth": {
            "values": [3, 5, 7]
        },
        "min_child_weight": {
          "min": 1,
          "max": 150,
          "num": 150
        },
        "early_stopping_rounds": {
          "values" : [10, 20, 30, 40]
        },
    }

    sampler = class_name(config)
    s = next(sampler)
    for k in s.configuration.keys():
      self.assertTrue(k in config.keys())

  def check_config_fields(self, class_name):
    config = {
        "C1": {
          "values": ["gbtree", "gblinear"]
        },
        "C2": ["gbtree", "gblinear"],
        "C3": {
          "min": 0.001, "max": 1.0
        },
        "C4": {
          "values" : [10, 20, 30, 40]
        },
        "C5": 1.23,
        "C6": {
          "min": 1, "max": 10
        },
        "C7": (1.0, 2.2),
        "C8": (1, 10),

        "C9": {
          "min": 11, "max": 20
        },
        "C10": (11, 20),
        "C11": (0.01, 1.0, 100),
        "C12": {
          "min": 0.01, "max": 1.0, "num": 100
        }
    }

    sampler = class_name(config)
    c = sampler()

    self.assertTrue(c("C5") == config["C5"])

    # Test in values list
    for k in ["C1", "C4"]:
      self.assertTrue(c(k) in config[k]["values"])
    # Test in list
    for k in ["C2"]:
      self.assertTrue(c(k) in config[k])
    # Test tuples numbers in the range
    for k in ["C7", "C8", "C10", "C11"]:
      self.assertTrue(config[k][0] <= c(k) and c(k) <= config[k][1])
    # Test min/max numbers in the range
    for k in ["C3", "C6", "C9", "C12"]:
      self.assertTrue(config[k]["min"] <= c(k) and c(k) <= config[k]["max"])
    # Test for int
    for k in ["C4", "C6", "C8", "C9", "C10"]:
      self.assertTrue(isinstance(c(k), int))
    # Test for float
    for k in ["C3", "C5", "C7", "C11", "C12"]:
      self.assertTrue(isinstance(c(k), float))
    # Test for string
    for k in ["C1", "C2"]:
      self.assertTrue(isinstance(c(k), str))

  def test_samplers(self):
    for class_name in [RandomSampler, GridSampler]:
      self.check_sampling_names(class_name)
      self.check_config_fields(class_name)


class TestBaseOptimizer(unittest.TestCase):
  def optimize(self, params, prev_params, fn_score, optimizer, n=10000, max_delta_score=1e-10):
    score = fn_score(params)
    prev_score = fn_score(prev_params)

    for i in range(n):
      # print(params, prev_params)
      delta_score, new_params = optimizer.update(
        params, score,
        prev_params, prev_score
      )
      prev_params, prev_score = params, score
      params, score = new_params, fn_score(new_params)
      if np.linalg.norm(delta_score) < max_delta_score:
        break
    print(i, params, score)
    return i, params, score

  def test_sin_max(self):
    fn_score = lambda params: np.sin(params['x1']) + np.sin(2 * params['x1'])

    list_maxmin = [0.93593, 2.573, 3.71, 5.3475, 7.2175]
    max_x = list_maxmin[0]
    max_y = fn_score({"x1": max_x})

    keys = ["x1"]
    use_keys = ["x1"]

    # High precision, high number of steps
    for optimizer in [BaseOptimizer(keys, use_keys, learning_rate=0.03), AdamOptimizer(keys, use_keys, learning_rate=0.01)]:
      for x1 in [0.1, 2.0]:
        i, params, score = self.optimize({"x1": x1}, {"x1": x1 * 0.99}, fn_score, optimizer, max_delta_score=1e-5)
        # print(type(optimizer).__name__, params['x1'], score)
        # print(type(optimizer).__name__, np.abs(params['x1'] - max_x), np.abs(score - max_y))
        self.assertTrue(np.abs(params['x1'] - max_x) < 0.01)
        self.assertTrue(np.abs(score - max_y) < 0.01)

    # Normal precision (1% - 5%) low number of steps
    for optimizer in [BaseOptimizer(keys, use_keys, learning_rate=0.05), AdamOptimizer(keys, use_keys, learning_rate=0.05)]:
      for x1 in [0.1, 2.0]:
        i, params, score = self.optimize({"x1": x1}, {"x1": x1 * 0.99}, fn_score, optimizer, n=100, max_delta_score=1e-5)
        print(type(optimizer).__name__, "X", params['x1'], "Y", score)
        print(type(optimizer).__name__, np.abs(params['x1'] - max_x), np.abs(score - max_y))
        self.assertTrue(np.abs(params['x1'] - max_x) < 0.03)
        self.assertTrue(np.abs(score - max_y) < 0.001)

    # There is a small local maximum and testing the escape capability to find the bigger maximum.
    # for x1 in [4.2]:
    #   i, params, score = self.optimize({"x1": x1}, {"x1": x1 * 0.99}, fn_score, AdamOptimizer(keys, use_keys, learning_rate=0.7, beta1=0.5, beta2=0.5), n=1000)
    #   self.assertTrue(np.abs(params['x1'] - max_x) < 1e-2)
    #   self.assertTrue(np.abs(score - max_y) < 1e-2)

  def test_learning_rate_decay(self):
    fn_score = lambda params: np.sin(params['x1']) + np.sin(2 * params['x1'])
    list_maxmin = [0.93593, 2.573, 3.71, 5.3475, 7.2175]
    max_x = list_maxmin[0]
    max_y = fn_score({"x1": max_x})

    keys = ["x1"]
    use_keys = ["x1"]

    for optimizer in [BaseOptimizer(keys, use_keys, learning_rate=0.1, learning_rate_decay=0.01)]:
      for x1 in [0.1, 2.0]:
        i, params, score = self.optimize({"x1": x1}, {"x1": x1 * 0.99}, fn_score, optimizer, n=50, max_delta_score=1e-5)
        print(type(optimizer).__name__, "X", params['x1'], "Y", score)
        print(type(optimizer).__name__, np.abs(params['x1'] - max_x), np.abs(score - max_y))
        self.assertTrue(np.abs(params['x1'] - max_x) < 0.005)
        self.assertTrue(np.abs(score - max_y) < 0.0001)
        self.assertTrue(i < 50)

  def test_sin_4(self):
    fn_score = lambda params: np.sin(params['x1']) + np.sin(2*params['x1']) + np.sin(3*params['x1']) + np.sin(4*params['x1'])
    max_y = 3.22

    for optimizer in [BaseOptimizer(["x1"], ["x1"], learning_rate=0.03), AdamOptimizer(["x1"], ["x1"], learning_rate=0.01)]:
      for x1 in [0.1, 1.0]:
        i, params, score = self.optimize({"x1": x1}, {"x1": x1 * 0.99}, fn_score, optimizer, max_delta_score=1e-5)
        self.assertTrue(np.abs(score - max_y) < 0.1)

    # Adam escape 3 local and try to find the 4-th maxima
    # for x1 in [2, 3, 4, 5.5]:
    #   i, params, score = self.optimize(
    #     {"x1": x1}, {"x1": x1 * 0.99}, fn_score,
    #     AdamOptimizer(["x1"], ["x1"], learning_rate=0.01, beta1=0.9, beta2=0.999),
    #     max_delta_score=1e-5
    #   )
    #   print("adam", x1, params, score)
    #   self.assertTrue(np.abs(score - max_y) < 0.1)

  def test_non_continuous(self):
    fn_score = lambda params: np.sin(params['x1']) + np.sin(2 * params['x1'])

    max_x = 0.93593

    config = {
      "x1": max_x,
      "batch_size": 8
    }

    max_y = fn_score(config)

    use_keys = ["x1"]

    for optimizer in [BaseOptimizer(config.keys(), use_keys, learning_rate=0.01), AdamOptimizer(config.keys(), use_keys, learning_rate=0.01)]:
      for x1 in [0.1, 2.0]:
        current_sample = config.copy()
        current_sample["x1"] = x1
        prev_sample = config.copy()
        prev_sample["x1"] = x1 * 0.99

        i, params, score = self.optimize(current_sample, prev_sample, fn_score, optimizer, n=1000, max_delta_score=1e-5)
        self.assertTrue(np.abs(params['x1'] - max_x) < 0.05)
        self.assertTrue(np.abs(score - max_y) < 0.05)


class TestSamplerAuto(unittest.TestCase):
  def test_sampling(self):
    config = {
      "lr": (0.0001, 0.1, 10),
      "gamma": (0.01, 1.0),
      "batch_size": [4, 8, 16, 32]
    }

    project = LocalProject("test")
    sampler = AutoSampler(config, project, num_random_samples=3)

    for i, configuration_sample in enumerate(sampler):
      project.config = configuration_sample
      E = project.open()
      E.score(i * 0.0001)
      E.name = f"E[{i}]"
      project.close()
      # debug(i, configuration_sample.configuration)
      if i > 5:
        break


class TestSamplerGrid(unittest.TestCase):
  def test_count_samples(self):
    config = {
        "lr": (0.01, 0.1, 11),
        "gamma": (0.01, 1.0, 11),
        "batch_size": [4, 8, 16, 32]
    }
    num_samples = 11 * 11 * 4

    sampler = GridSampler(config)
    for i, configuration_sample in enumerate(sampler):
      pass
    self.assertTrue(i + 1 == num_samples)
    self.assertTrue(sampler.idx == num_samples)