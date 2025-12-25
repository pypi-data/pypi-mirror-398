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

import json

from sciveo.tools.logger import *


list_hyperparameters = list(set([
  # KERAS params
    'num_layers',
    'neurons_per_layer',
    'activation_function',
    'learning_rate',
    'loss_function',
    'optimizer',
    'batch_size',
    'num_epochs',
    'dropout_rate',
    'regularization_type',
    'kernel_initializer',
    'bias_initializer',
    'number_of_parameters',
    'model_type',
    'input_shape',
    'output_activation',

  # SciKit params
    'random_state',
    'n_jobs',
    'max_depth',
    'min_samples_split',
    'min_samples_leaf',
    'max_features',
    'C',
    'kernel',
    'gamma',
    'n_estimators',
    'max_samples',
    'n_neighbors',
    'weights',
    'algorithm',
    'learning_rate',
    'alpha',
    'lambda',
    'cv',
    'n_estimators',
    'n_clusters',
    'init',
    'n_components',
    'hidden_layer_sizes',
    'activation',
    'solver',
    'learning_rate_init',
]))

class Configuration:
  def __init__(self, configuration={}, predefined_attr=False):
    self.configuration = configuration
    self.name = ""

    if predefined_attr:
      for c in list_hyperparameters:
        setattr(self, c, None)
    for k, v in configuration.items():
      setattr(self, k, v)
    debug("init", configuration)

  def set(self, key, value):
    self.configuration[key] = value

  def get(self, key=None):
    if key:
      return self.configuration[key]
    else:
      return self.configuration

  def __call__(self, key=None):
    return self.get(key)

  def __getitem__(self, idx):
    return self.configuration[idx]

  def __str__(self):
    return json.dumps(self.configuration)

  def set_name(self, tag):
    self.name = tag
    for k, v in self.configuration.items():
      self.name += f" {k}={v}"
    return self.name
