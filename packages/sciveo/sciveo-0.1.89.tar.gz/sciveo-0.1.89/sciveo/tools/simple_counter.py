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

import time
import sys
from datetime import datetime


class SimpleCounter:
  def __init__(self, count):
    self.counter = 0
    self.current_count = 0
    self.count = count

  def run(self):
    self.counter += 1
    self.current_count += 1
    if self.current_count >= self.count:
      self.current_count = 0

    return self.current_count == 0

  def reset(self):
    self.current_count = 0


class RunCounter(SimpleCounter):
  def __init__(self, count, fn):
    super().__init__(count)
    self.fn = fn

  def run(self):
    if super().run():
      self.fn()


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


class TimerDateTime:
  def __init__(self):
    self.start()

  def start(self):
    self.start_at = datetime.now()

  def stop(self):
    self.end_at = datetime.now()
    return self.elapsed()

  def elapsed(self):
    return (self.end_at - self.start_at).total_seconds()


class TimerExpire(Timer):
  def __init__(self, expiry_period):
    super().__init__()
    self.expiry_period = expiry_period

  def finished(self):
    return self.stop() > self.expiry_period


class SimpleStat:
  def __init__(self):
    self.stat = {"min": sys.float_info.max, "max": - sys.float_info.max, "sum": 0, "count": 0, "mean": 0}

  def __dict__(self):
    return self.stat

  def __str__(self):
    return "{}".format(self.stat)

  def __repr__(self):
    return self.__str__()

  def set(self, val):
    if self.stat["min"] > val:
      self.stat["min"] = val
    if self.stat["max"] < val:
      self.stat["max"] = val
    self.stat["sum"] += val
    self.stat["count"] += 1
    self.stat["mean"] = self.stat["sum"] / self.stat["count"]


class ProcessedStatTimer(Timer):
  def __call__(self, num_processed):
    elapsed = self.stop()
    pps = round(num_processed / elapsed, 1)
    elapsed = round(elapsed, 1)
    return elapsed, pps