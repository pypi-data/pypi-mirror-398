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

from itertools import product
import numpy as np

from sciveo.tools.logger import *
from sciveo.common.configuration import Configuration
from sciveo.common.optimizers import BaseOptimizer, AdamOptimizer


class BaseSampler:
  """
    Base sampler iterator. Should be used as base for sampling components like random/grid/auto samplers.

    Args:
    configuration:          Dict with config params like {"lr": (0.0001, 0.01), "batch_size": [4, 8, 16]}
  """
  def __init__(self, configuration, **kwargs):
    self.configuration = configuration
    self.kwargs = kwargs
    self.idx = 0

    self.arguments = {}

  def get(self, a):
    return self.kwargs.get(a, self.arguments[a])

  def describe(self):
    return {
      "name": type(self).__name__,
      "arguments": self.arguments,
      "configuration": self.configuration
    }

  def sample_min_max(self, min_value, max_value):
    return None

  def sample_list(self, list_values):
    return None

  # TODO: Need to refine dtypes, currently int/floats only supported.
  def minmax_dtype(self, min_value, max_value):
    if isinstance(min_value, int) and isinstance(max_value, int):
      return int
    elif isinstance(min_value, float) or isinstance(max_value, float):
      return float
    return float

  def sample_field(self, field):
    if isinstance(field, dict):
      if "values" in field:
        return self.sample_list(field["values"])
      elif "min" in field and "max" in field:
        return self.sample_min_max(field["min"], field["max"])
      elif "value" in field:
        return field["value"]
      elif "seq" in field:
        return field["seq"] * self.idx
      else:
        return None
    elif isinstance(field, list):
      return self.sample_list(field)
    elif isinstance(field, tuple) and len(field) >= 2:
      return self.sample_min_max(field[0], field[1])
    else:
      return field

  def __next__(self):
    sample = {}
    for k, v in self.configuration.items():
      sample[k] = self.sample_field(v)
    self.idx += 1
    # debug("next", sample)
    return Configuration(sample)

  def __call__(self):
    return next(self)

  def __iter__(self):
    return self


class RandomSampler(BaseSampler):
  def __init__(self, configuration, **kwargs):
    super().__init__(configuration, **kwargs)

  def sample_min_max(self, min_value, max_value):
    val = np.random.uniform(min_value, max_value)
    val = self.minmax_dtype(min_value, max_value)(val)
    return val

  def sample_list(self, list_values):
    return list_values[np.random.randint(0, len(list_values))]


class GridSampler(BaseSampler):
  def __init__(self, configuration, **kwargs):
    super().__init__(configuration, **kwargs)
    self.configuration_to_lists()
    self.sample_iterator = product(*self.configuration_lists.values())

  def configuration_field_to_list(self, field):
    if isinstance(field, dict):
      if "values" in field:
        return field["values"]
      elif "min" in field and "max" in field:
        default_num = 10
        if self.minmax_dtype(field["min"], field["max"]) == int:
          default_num = field["max"] - field["min"] + 1
        result = np.linspace(field["min"], field["max"], field.get("num", default_num))
        if self.minmax_dtype(field["min"], field["max"]) == int:
          result = result.astype(int)
        return result.tolist()
      elif "value" in field:
        return [field["value"]]
      else:
        return list(field.values())
    elif isinstance(field, list):
      return field
    elif isinstance(field, tuple) and len(field) >= 2:
      if len(field) >= 3:
        num = field[2]
      else:
        num = 10
        if self.minmax_dtype(field[0], field[1]) == int:
          num = field[1] - field[0] + 1
      result = np.linspace(field[0], field[1], num)
      if self.minmax_dtype(field[0], field[1]) == int:
        result = result.astype(int)
      return result.tolist()
    else:
      return [field]

  def configuration_to_lists(self):
    self.configuration_lists = {}
    for k, v in self.configuration.items():
      self.configuration_lists[k] = self.configuration_field_to_list(v)

  def __next__(self):
    sample = next(self.sample_iterator)
    self.idx += 1
    sample = dict(zip(self.configuration_lists.keys(), sample))
    # debug("next", sample)
    return Configuration(sample)


class AutoSampler(BaseSampler):
  """
    Auto sampling using a combination of random samplig, gradient-based optimizator sampling.
    The configuration could have different types of continuous and non-continuous parameters,
    so using gradient-based optimization only continuous parameters (others are not changed in the gradient-based optimization).
    TODO: The auto sampling should handle different types of configurations...

    Args:
    configuration:          Dict with config params like {"lr": (0.0001, 0.01), "batch_size": [4, 8, 16]}
    project:                Project object which manage the project-related objects like experiments, datasets, models etc.
    num_random_samples=10:  Number of random samples which is the initial sampling
    next_sample_ratio=0.95: Next random sample ratio which will create a close sample, suitable for next gradient-based samples.
    min_delta_score=0.01:   Min delta score which is used to determing when to stop gradient-based sampling.
                            When new gradient optimized sample is calculated, also delta score is returned.
                            This delta score is used to determine how far to the (local) optimum.
    optimizer="base":       Optimizer name, currently base simple gradient descent and adam optimizers available.
    learning_rate=0.01:     Optimizer learning rate
    learning_rate_decay:    Learning rate decay
  """
  def __init__(self, configuration, project, **kwargs):
    super().__init__(configuration, **kwargs)
    self.arguments.update({
      "project": "Project object which manage the project-related objects like experiments, datasets, models etc.",
      "optimizer": "base",
      "min_delta_score": 1e-5,
      "num_random_samples": 10,
      "next_sample_ratio": 0.95,
      "learning_rate": 0.1,
      "learning_rate_decay": 0.01
    })

    optimizer = self.get('optimizer')

    self.min_delta_score = self.get('min_delta_score')
    self.num_random_samples = self.get('num_random_samples')
    self.next_sample_ratio = self.get('next_sample_ratio')
    self.learning_rate = self.get('learning_rate')
    self.learning_rate_decay = self.get('learning_rate_decay')

    self.project = project
    self.optimize_limits, self.optimize_keys = self.config_grad_keys()

    self.random_sampler = RandomSampler(configuration)

    self.best_random_experiment = None
    self.sample_x1 = None
    self.sample_y1 = None
    self.sample_x2 = None
    self.sample_y2 = None

    self.optimizers = {
      "base": BaseOptimizer,
      "adam": AdamOptimizer
    }
    self.optimizer = self.optimizers.get(optimizer, "base")(
      self.configuration.keys(), self.optimize_keys,
      learning_rate=self.learning_rate, learning_rate_decay=self.learning_rate_decay
    )

  def config_grad_keys(self):
    keys = []
    limits = {}
    for k, field in self.configuration.items():
      if isinstance(field, dict):
        if "min" in field and "max" in field:
          if isinstance(field["min"], float) or isinstance(field["max"], float):
            keys.append(k)
            limits[k] = [field["min"], field["max"]]
      elif isinstance(field, tuple) and len(field) >= 2:
        if isinstance(field[0], float) or isinstance(field[1], float):
          keys.append(k)
          limits[k] = [field[0], field[1]]
    return limits, keys

  def __next__(self):
    self.idx += 1
    if len(self.project.list_experiments) < self.num_random_samples:
      debug("next random sample from", type(self.random_sampler).__name__, len(self.project.list_experiments), "from", self.num_random_samples)
      return next(self.random_sampler)
    else:
      # Find highest score experiment. Run with close to this current best experiment so to be able to calc gradient.
      if self.best_random_experiment is None:
        max_score = -1
        for E in self.project.list_experiments:
          if E.data["experiment"]["eval"]["score"] > max_score:
            max_score = E.data["experiment"]["eval"]["score"]
            self.best_random_experiment = E
        debug("next best experiment", E.name, E.data["experiment"]["config"])
        new_params = {}
        for k, v in E.data["experiment"]["config"].items():
          if k in self.optimize_keys:
            new_params[k] = v * self.next_sample_ratio
          else:
            new_params[k] = v
        debug("next sample with ratio", self.next_sample_ratio, new_params)
        return Configuration(new_params)
      else:
        # Already have best random experiment and its close experiment
        self.sample_x1 = self.project.list_experiments[-1].data["experiment"]["config"]
        self.sample_y1 = self.project.list_experiments[-1].data["experiment"]["eval"]["score"]
        # When first optimiziation step then initialize the previous sample with the best experiment.
        if self.sample_x2 is None:
          self.sample_x2 = self.best_random_experiment.data["experiment"]["config"]
          self.sample_y2 = self.best_random_experiment.data["experiment"]["eval"]["score"]

        delta_score, new_params = self.optimizer.update(
          self.sample_x1, self.sample_y1,
          self.sample_x2, self.sample_y2
        )

        self.sample_x2, self.sample_y2 = self.sample_x1, self.sample_y1

        for k, v in self.optimize_limits.items():
          if new_params[k] < v[0] or new_params[k] > v[1]:
            debug("next out of limits", k, new_params[k], v)
            raise StopIteration

        if np.linalg.norm(delta_score) > self.min_delta_score:
          debug("next", type(self.optimizer).__name__, new_params, [delta_score, self.min_delta_score])
          return Configuration(new_params)
        else:
          debug("next small improvement", new_params, "delta", delta_score)
          raise StopIteration
