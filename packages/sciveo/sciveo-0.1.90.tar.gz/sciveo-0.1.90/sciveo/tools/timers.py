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

import time

from sciveo.tools.logger import *


class FPSDelay:
  def __init__(self, fps):
    self.fps = fps
    if fps > 0:
      self.delay = 1.0 / fps
    else:
      self.delay = 0

  def start(self):
    self.from_time = time.time()

  def wait(self):
    current_time = time.time()
    elapsed_time = current_time - self.from_time
    time_to_wait = self.delay - elapsed_time
    if time_to_wait > 0:
      time.sleep(time_to_wait)


class FPSCounter:
  def __init__(self, period=1, tag="", print_period=1, printer=debug, round_value=2):
    self.period = period
    self.print_period = print_period
    self.printer = printer
    self.print_n = 0
    self.tag = tag
    self.n = 0
    self.t1 = time.time()
    self.value = 0
    self.round_value = round_value

  def print(self):
    self.print_n += 1
    if self.print_n > self.print_period:
      self.printer(self.tag, "FPS", self.value)
      self.print_n = 0

  def update(self):
    self.n += 1
    t2 = time.time()
    if t2 - self.t1 > self.period:
      self.value = self.n / (t2 - self.t1)
      if self.round_value is not None:
        self.value = round(self.value, self.round_value)
      self.n = 0
      self.t1 = time.time()
      self.print()

  def reset(self):
    self.n = 0
    self.t1 = time.time()
    self.value = 0


class TimerExec:
  def __init__(self, fn, period=1.0):
    self.fn = fn
    self.period = period
    self.t1 = time.time()

  def run(self):
    t2 = time.time()
    if t2 - self.t1 > self.period:
      self.fn()
      self.t1 = time.time()


class Timer:
  def __init__(self):
    self.start()

  def start(self):
    self.start_at = time.time()

  def stop(self):
    self.end_at = time.time()
    return self.elapsed()

  def elapsed(self):
    return self.end_at - self.start_at
