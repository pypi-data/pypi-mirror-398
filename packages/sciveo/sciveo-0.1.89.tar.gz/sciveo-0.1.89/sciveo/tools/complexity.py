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

import math

from sciveo.tools.logger import *


"""
  Simple complexity evaluation
  Evaluate against few well known complexities, could add more in self.list_complexity
"""
class ComplexityEval:
  def __init__(self, samples, printer=print):
    if isinstance(samples, int):
      self.size = samples
    elif isinstance(samples, list) or isinstance(samples, dict):
      self.size = len(samples)
    else:
      self.size = int(samples)

    self.printer = printer

    self.list_complexity = [
      ("logN", round(math.log2(self.size), 2)),
      ("N", self.size),
      ("NlogN", round(self.size * math.log2(self.size))),
      ("N^2", self.size ** 2),
      ("N^3", self.size ** 3),
    ]

    self.complexity_str = ""
    for c in self.list_complexity:
      self.complexity_str += f"{c[0]}={c[1]} "
    self.complexity_str = self.complexity_str.strip()

  def calc_power(self, iterations):
    return math.log(iterations) / math.log(self.size)

  def evaluate(self, iterations):
    this_power = self.calc_power(iterations)
    this_complexity = None

    for i in range(0, len(self.list_complexity)):
      if iterations <= self.list_complexity[i][1]:
        if i == 0:
          this_complexity = self.list_complexity[i]
          break
        else:
          if this_power <= (self.calc_power(self.list_complexity[i][1]) + self.calc_power(self.list_complexity[i - 1][1])) / 2:
            this_complexity = self.list_complexity[i - 1]
          else:
            this_complexity = self.list_complexity[i]
        break
    if this_complexity is None:
      this_complexity = self.list_complexity[-1]

    return this_complexity

  def __call__(self, iterations):
    return self.evaluate(iterations)

  def print(self, iterations):
    this_complexity = self.evaluate(iterations)
    this_power = self.calc_power(iterations)
    self.printer("size", self.size, "iterations", iterations, f"(N^{this_power:.2f})({this_complexity[1]})", f"[{self.complexity_str}]")
    self.printer(f"O(N) = {this_complexity[0]}")
