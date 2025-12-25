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
import time

from sciveo.tools.logger import *
from sciveo.tools.configuration import ConfigurationArguments
from sciveo.monitoring.monitor import BaseMonitor


class MonitorStart:
  def __init__(self, **kwargs):
    self.arguments = ConfigurationArguments({
      "period": 120,
      "block": True,
      "fork": False,
      "fork_type": 0,
      "output_path": None,
    }, **kwargs)

    if len(kwargs) == 0:
      info("sciveo monitoring default options", self.arguments)

  def __call__(self):
    if self.arguments["fork"] and self.arguments["block"]:
      self.fork()
    self.start()

  def start_multiprocessing(self):
    self.start()
  def start_fork(self):
    os.setsid()
    self.start()
  def fork(self):
    if self.arguments["fork_type"] == 0:
      import multiprocessing
      background_process = multiprocessing.Process(target=self.start_multiprocessing)
      background_process.daemon = True
      background_process.start()
      info("monitoring service started with", self.arguments)
      exit()
    else:
      pid = os.fork()
      if pid == 0:
        self.start_fork()
      else:
        info("sciveo monitor service started with pid", pid, self.arguments)
        exit()

  def start(self):
    period = max(self.arguments["period"], 5)
    mon = BaseMonitor(period=period, output_path=self.arguments["output_path"])
    mon.start()
    mon.join()

    if self.arguments["block"]:
      while(True):
        time.sleep(60)
