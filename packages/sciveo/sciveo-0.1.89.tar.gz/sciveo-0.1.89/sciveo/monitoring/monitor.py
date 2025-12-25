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
import subprocess
import time
import json
import datetime
import socket
import psutil
import platform
import re
import uuid
import numpy as np

from sciveo.tools.logger import *
from sciveo.tools.daemon import DaemonBase
from sciveo.tools.hardware import *
from sciveo.tools.formating import format_memory_size
from sciveo.api.base import APIRemoteClient


class MonitorTools:
  @staticmethod
  def serial():
    machine_serial = ""
    s = "-"
    list_uid_calls = [socket.gethostname, psutil.cpu_count, platform.processor]
    for uid_call in list_uid_calls:
      try:
        machine_serial += f"{uid_call()}{s}"
        s = ""
      except Exception:
        pass
    return re.sub(r'[\s,]', '', machine_serial)


class BaseMonitor(DaemonBase):
  def __init__(self, period=5, output_path=None):
    super().__init__(period=period)
    self.output_path = output_path
    if self.output_path is not None and os.path.isdir(self.output_path):
      self.output_path = os.path.join(self.output_path, "sciveo_monitor.json")

    self.data = {
      "CPU": {},
      "RAM": {},
      "DISK": {},
      "NET": {},
      "TEMP": {},
      "LOG": {},
      "INFO": {},
    }
    self.data["INFO"] = HardwareInfo()()
    self.data["INFO"].setdefault("CPU", {})
    self.list_logs = []

    self.api = APIRemoteClient()

    # Warmup the psutil
    psutil.cpu_percent(interval=0.3, percpu=True)
    initial_cpu_usage = psutil.cpu_percent(interval=None, percpu=True)
    self.previous_io_counters = {
      "DISK": psutil.disk_io_counters(perdisk=False),
      "NET": psutil.net_io_counters(pernic=False)
    }
    self.previous_time = {"DISK": time.time(), "NET": time.time()}
    time.sleep(1)

    self.data["serial"] = MonitorTools.serial()

    debug(f"init monitor with period={period}", self.data["serial"], "initial_cpu_usage", initial_cpu_usage)

  def __call__(self):
    return self.data

  def output_write(self):
    if os.path.isfile(self.output_path):
      with open(self.output_path, "rb+") as fp:
        fp.seek(-2, 2)
        fp.truncate()
      with open(self.output_path, "a") as fp:
        fp.write(f", {json.dumps(self.data)}]\n")
    else:
      with open(self.output_path, "w") as fp:
        fp.write(json.dumps([self.data]) + "\n")

  def loop(self):
    self.get_cpu_usage()
    self.get_temperatures()
    self.get_memory()
    self.get_gpu()
    self.get_disk()
    self.get_network()

    self.tail_logs()
    self.data["local_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    api_result = self.api.POST_SCI("monitor", {"data": self.data})

    try:
      if self.output_path is not None:
        self.output_write()
    except Exception as e:
      error(e, "writing failed for", self.output_path)

    debug(self(), "api_result", api_result)

  def tail_logs(self):
    for log_name, log_path in self.list_logs:
      self.data["LOG"][log_name] = self.tail_file(log_path)[-3:]

  def get_cpu_usage(self):
    try:
      usage_per_core = psutil.cpu_percent(interval=None, percpu=True)
      self.data["CPU"]["usage per core"] = usage_per_core
      self.data["CPU"]["usage"] = float(np.array(usage_per_core).mean())
    except Exception:
      pass

  def get_temperatures(self):
    try:
      temperatures = psutil.sensors_temperatures()
      for k, v in temperatures.items():
        self.data["TEMP"][k] = [t.current for t in v]
    except Exception as e:
      pass

  def get_memory(self):
    try:
      memory = psutil.virtual_memory()
      self.data["RAM"]["used"] = memory.used
      self.data["RAM"]["total"] = memory.total
      self.data["RAM"]["free"] = memory.free
      # self.data["RAM"]["installed"] = format_memory_size(memory.total)
      self.data["INFO"]["RAM"] = f"total: {format_memory_size(memory.total)} used: {format_memory_size(memory.used)}"
    except Exception:
      pass

  def tail_file(self, file_path, block_size=1024):
    result = ["EMPTY"]
    try:
      with open(file_path,'rb') as fp:
        fp.seek(-block_size, os.SEEK_END)
        result = str(fp.read(block_size).rstrip()).split("\\n")
    except Exception as e:
      error(e, "tail_file", file_path)
    return result

  # Currently simple nvidia-smi wrapper impl
  def get_gpu(self):
    try:
      result = subprocess.run(
        [
          'nvidia-smi',
          '--query-gpu=gpu_uuid,gpu_name,index,power.draw,fan.speed,memory.total,memory.used,memory.free,utilization.gpu,utilization.memory,temperature.gpu',
          '--format=csv,nounits'
        ],
        capture_output=True, text=True, check=True
      )

      lines = result.stdout.strip().split('\n')
      self.data["GPU"] = {
        "raw_lines": lines[:7] # TODO: FIX this! Due to aws timestream constraints.
      }
    except Exception as e:
      pass

  def get_disk(self):
    try:
      list_metrics = ["read bytes", "write bytes", "read count", "write count", "read time", "write time"]
      disk_io_counters = psutil.disk_io_counters(perdisk=False)
      self.get_io_metrics("DISK", list_metrics, disk_io_counters)

      disk_usage = psutil.disk_usage('/')._asdict()
      self.data["INFO"]["DISK"] = f"{disk_usage['percent']}% ({round(disk_usage['used'] / (1024 * 1024 * 1024), 1)} GB / {round(disk_usage['total'] / (1024 * 1024 * 1024), 1)} GB)"
    except Exception as e:
      pass

  def get_network(self):
    try:
      list_metrics = ["bytes sent", "bytes recv", "packets sent", "packets recv"]
      net_io_counters = psutil.net_io_counters(pernic=False)
      self.get_io_metrics("NET", list_metrics, net_io_counters)
    except Exception as e:
      pass

  def get_io_metrics(self, name, list_metrics, io_counters):
    counters = io_counters._asdict()
    prev_io_counters = self.previous_io_counters[name]._asdict()
    time_diff = time.time() - self.previous_time[name]
    for metric_name in list_metrics:
      metric_key = metric_name.replace(' ', '_')
      self.data[name][metric_name] = counters[metric_key] - prev_io_counters[metric_key]

      if "bytes" in metric_name:
        speed_metric = metric_name.replace("bytes", "speed")
        self.data[name][speed_metric] = self.data[name][metric_name] / time_diff
    self.previous_time[name] = time.time()
    self.previous_io_counters[name] = io_counters

if __name__ == "__main__":
  debug(MonitorTools.serial())

  mon = BaseMonitor(period=10)
  mon.start()

  while(True):
    time.sleep(30)