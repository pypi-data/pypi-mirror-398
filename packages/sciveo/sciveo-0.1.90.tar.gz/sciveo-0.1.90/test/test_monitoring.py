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
from sciveo.monitoring.monitor import *


class TestMonitoring(unittest.TestCase):
  def test_cpu(self):
    m = BaseMonitor()
    m.get_cpu_usage()
    print(m.data)

    self.assertTrue("usage per core" in m.data["CPU"])
    self.assertTrue("usage" in m.data["CPU"])

  def test_gpu(self):
    data = {
      "GPU": {
        "raw_lines": [
          "uuid, name, index, power.draw [W], fan.speed [%], memory.total [MiB], memory.used [MiB], memory.free [MiB], utilization.gpu [%], utilization.memory [%], temperature.gpu",
          "GPU-41e0e872-f8d5-95fb-6fd7-8c143c0db7c9, NVIDIA GeForce RTX 3060, 0, 11.57, 0, 12053, 13, 12040, 0, 0, 38",
          "GPU-f7a1d225-58db-e209-aa84-574996d070cd, NVIDIA GeForce RTX 3060, 1, 12.08, 0, 12045, 477, 11568, 0, 39, 36"
        ]
      }
    }
    sample = {}
    config = {
      "CPU": {
        "usage":              {"ratio": 1.0, "metric": "%", "ylim": [0.0, 105.0]},
        "usage per core":     {"ratio": 1.0, "metric": "%", "ylim": [0.0, 105.0]},
      },
      "RAM": {
        "used":               {"ratio": 1.0 / (1024 * 1024 * 1024), "metric": "GB"},
      },
      "GPU": {
        "fan.speed":          {"ratio": 1.0, "metric": "%", "ylim": [0.0, 105.0]},
        "power.draw":         {"ratio": 1.0, "metric": "W", "ylim": [0.0, 250.0]},
        "memory.free":        {"ratio": 1.0 / 1024, "metric": "GB"},
        "memory.used":        {"ratio": 1.0 / 1024, "metric": "GB"},
        "temperature.gpu":    {"ratio": 1.0, "metric": "°C", "ylim": [10, 110]},
        "utilization.gpu":    {"ratio": 1.0, "metric": "%", "ylim": [0.0, 105.0]},
        "utilization.memory": {"ratio": 1.0, "metric": "%", "ylim": [0.0, 105.0]},
      }
    }

    try:
      lines = data["GPU"]["raw_lines"]
      header = lines[0].split(", ")

      keys = []
      gpu_keys = []
      for k in header:
        k_split = k.split(' ')
        key = k_split[0]
        keys.append(key)
        gpu_keys.append(f"GPU {key}")

      for i, k in enumerate(keys):
        if k in config["GPU"]:
          sample[gpu_keys[i]] = []
        else:
          data["GPU"][keys[i]] = []

      for i in range(1, len(lines)):
        line_values = lines[i].split(", ")
        for j, value in enumerate(line_values):
          try:
            value = float(value)
          except ValueError:
            pass
          if keys[j] in config["GPU"]:
            sample[gpu_keys[j]].append(value)
          else:
            data["GPU"][keys[j]].append(value)

      if "memory.total" in data["GPU"]:
        print("memory.total", data["GPU"]["memory.total"])
        for k in ["memory.used", "memory.free"]:
          config["GPU"][k]["ylim"] = [0, max(data["GPU"]["memory.total"]) * config["GPU"][k]["ratio"]]
          print("ylim", config["GPU"][k]["ylim"])
    except Exception as e:
      print("Exception", e)

    print("memory.used", config["GPU"]["memory.used"])
    print("free", config["GPU"]["memory.free"])