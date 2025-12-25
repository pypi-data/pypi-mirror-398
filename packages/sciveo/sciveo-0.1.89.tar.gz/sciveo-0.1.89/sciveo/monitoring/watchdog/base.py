#
# Pavlin Georgiev, Softel Labs
#
# This is a proprietary file and may not be copied,
# distributed, or modified without express permission
# from the owner. For licensing inquiries, please
# contact pavlin@softel.bg.
#
# 2025
#


import psutil
import subprocess

from sciveo.tools.daemon import *
from sciveo.tools.logger import *
from sciveo.tools.simple_counter import RunCounter


class BaseWatchDogDaemon(DaemonBase):
  def __init__(self, threshold_percent=90, period=5, command="echo '⚠️'", monitored="none", monitor_value="usage"):
    super().__init__(period=period)
    self.threshold_percent = threshold_percent
    self.command = command
    self.used_percent = 0
    self.monitored = monitored
    self.monitor_value = monitor_value
    self.printer = RunCounter(60, lambda: debug(f"{self.monitored} {self.monitor_value}: {self.used_percent}%", f"threshold: {self.threshold_percent}%"))

  def value(self):
    return {"percent": 0.0}

  def loop(self):
    current_value = self.value()
    self.used_percent = current_value["percent"]
    self.printer.run()
    if self.used_percent > self.threshold_percent:
      warning(f"⚠️ {self.monitored} {self.monitor_value} {self.used_percent}% exceeded {self.threshold_percent}%, executing command: {self.command}")
      subprocess.run(self.command, shell=True)


class MemoryWatchDogDaemon(BaseWatchDogDaemon):
  def __init__(self, threshold_percent=90, period=5, command="echo '⚠️ Low Memory!'"):
    super().__init__(threshold_percent=threshold_percent, period=period, command=command, monitored="Memory")

  def value(self):
    return psutil.virtual_memory()._asdict()

class DiskWatchDogDaemon(BaseWatchDogDaemon):
  def __init__(self, path, threshold_percent=90, period=5, command="echo '⚠️ Low Disk space!'"):
    self.path = path
    super().__init__(threshold_percent=threshold_percent, period=period, command=command, monitored=f"Disk [{self.path}] space")

  def value(self):
    return psutil.disk_usage(self.path)._asdict()
