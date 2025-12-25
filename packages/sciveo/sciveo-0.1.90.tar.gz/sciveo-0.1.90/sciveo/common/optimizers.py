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

import numpy as np

from sciveo.tools.logger import *


class BaseOptimizer:
  def __init__(self, keys, use_keys, learning_rate=0.01, learning_rate_decay=0.001):
    # Negative learning rate, Y is loss and will optimize for minimum
    # Positive learning rate, Y is score and optimize for maximium
    self.learning_rate = learning_rate
    self.initial_learning_rate = learning_rate
    self.learning_rate_decay = 1 - learning_rate_decay
    # Gradient based optimisation needs continuous parameters only.
    # So use keys list represents continuous params only. Remain keys list represents the non-continuous params list.
    self.keys = set(keys)
    self.use_keys = set(use_keys)
    self.remain_keys = self.keys - self.use_keys
    self.iteration = 0
    debug("init", self.use_keys, learning_rate, learning_rate_decay)

  def x_to_list(self, x1, x2):
    list_x1 = []
    list_x2 = []
    for k in self.use_keys:
      list_x1.append(x1[k])
      list_x2.append(x2[k])
    return np.array(list_x1), np.array(list_x2)

  def list_to_x(self, x1, x2):
    dict_x = {}
    for k in self.remain_keys:
      dict_x[k] = x1[k]
    for i, k in enumerate(self.use_keys):
      dict_x[k] = x2[i]
    return dict_x

  def gradients(self, x1, y1, x2, y2, max_gradient_norm=1.0):
    delta_x = x1 - x2
    delta_y = y1 - y2
    result = delta_y / (delta_x + 1e-10)
    return np.clip(result, -max_gradient_norm, max_gradient_norm), delta_x, delta_y

  def on_iteration(self):
    self.learning_rate *= self.learning_rate_decay
    self.iteration += 1

  def update(self, x, y, x_prev, y_prev):
    x1, x_prev1 = self.x_to_list(x, x_prev)
    grads, delta_x, delta_y = self.gradients(x1, y, x_prev1, y_prev)

    x_new = x1 * (1 + self.learning_rate * grads)

    self.on_iteration()
    # debug(self.iteration, "update", [x1.tolist(), y], "x_new", x_new.tolist(), "grads", grads.tolist(), "lr", self.learning_rate)

    return delta_y, self.list_to_x(x, x_new)


class HistoryGradientOptimizer(BaseOptimizer):
  def __init__(self, keys, use_keys, learning_rate=0.01, learning_rate_decay=0.001):
    super().__init__(keys, use_keys, learning_rate, learning_rate_decay)

  def update(self, list_samples):
    for i in range(len(list_samples) - 1):
      x1, y1 = list_samples[i]
      x2, y2 = list_samples[i + 1]

      x11, x22 = self.x_to_list(x1, x2)
      grads, delta_x, delta_y = self.gradients(x11, y1, x22, y2)


class AdamOptimizer(BaseOptimizer):
  def __init__(self, keys, use_keys, learning_rate=0.01, learning_rate_decay=0.001, beta1=0.9, beta2=0.999, epsilon=1e-8):
    super().__init__(keys, use_keys, learning_rate, learning_rate_decay)
    self.beta1 = beta1
    self.beta2 = beta2
    self.epsilon = epsilon
    self.t = 0
    self.m = None
    self.v = None

  def update(self, x, y, x_prev, y_prev):
    x1, x_prev1 = self.x_to_list(x, x_prev)
    grads, delta_x, delta_y = self.gradients(x1, y, x_prev1, y_prev)

    if self.m is None:
      self.m = np.zeros_like(x1)
      self.v = np.zeros_like(x1)

    self.t += 1

    self.m = self.beta1 * self.m + (1 - self.beta1) * grads
    self.v = self.beta2 * self.v + (1 - self.beta2) * (grads ** 2)

    m_hat = self.m / (1 - self.beta1 ** self.t)
    v_hat = self.v / (1 - self.beta2 ** self.t)

    x_new = x1 + self.learning_rate * m_hat / (np.sqrt(v_hat) + self.epsilon)

    self.on_iteration()
    # debug(self.iteration, "update", [x1.tolist(), y], "x_new", x_new.tolist(), "grads", grads.tolist(), "lr", self.learning_rate)

    return delta_y, self.list_to_x(x, x_new)
