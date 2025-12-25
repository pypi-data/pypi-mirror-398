#
# Stanislav Georgiev, Softel Labs
#
# This is a proprietary file and may not be copied,
# distributed, or modified without express permission
# from the owner. For licensing inquiries, please
# contact s.georgiev@softel.bg.
#
# 2025
#

import os
import json
import datetime
import time
from pymodbus.client import ModbusTcpClient
from sciveo.tools.logger import *
from sciveo.tools.daemon import DaemonBase
# from sciveo.api.base import APIRemoteClient
from sciveo.monitoring.power.tools import *


class PowerEMS300(DaemonBase):
  def __init__(self, serial, host, port=502, device_id=247, delay=0.01, period=30, output_path=None):
    super().__init__(period=period)
    self.serial = serial
    self.host = host
    self.port = port
    self.device_id = device_id
    self.delay = delay
    self.client = None

    if output_path is not None and os.path.isdir(output_path):
      self.output_path = os.path.join(output_path, f"{self.serial}.json")
    else:
      self.output_path = output_path

    # self.api = APIRemoteClient()
    self.client = ModbusTcpClient(host=self.host, port=self.port)

  def connect(self):
    if not self.client.connected:
      if self.client.connect():
        info(type(self.client).__name__, "connected", (self.host, self.port))
      else:
        error("Connect FAIL", (self.host, self.port))
    return self.client.connected

  def send(self, data):
    api_result = self.api.POST_SCI("monitor", {"data": data})
    debug(data, "api_result", api_result)

  def output_write(self, data):
    if os.path.isfile(self.output_path):
      with open(self.output_path, "rb+") as fp:
        fp.seek(-2, 2)
        fp.truncate()
      with open(self.output_path, "a") as fp:
        fp.write(f", {json.dumps(data)}]\n")
    else:
      with open(self.output_path, "w") as fp:
        fp.write(json.dumps([data]) + "\n")

  def save(self, data):
    try:
      if self.output_path is not None:
        info("save", self.output_path, data)
        self.output_write(data)
    except Exception as e:
      error(e, "writing failed for", self.output_path)

  def loop(self):
    if not self.connect():
      warning("Not connected", (self.host, self.port))
      return

    try:
      data = {
        "local_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "serial": self.serial,
      }

      current_info = [8026, 8044, 8060, 8776, 8778, 10101, 10103, 10105, 10713, 10715, 10716, 10945]
      for addr in current_info:
        result = read_input_registers(self.client, EMS300_REG_MAP, addr, self.device_id)
        if result is not None:
          value, name, dtype = result
          debug(f"{name}: {value}")
          data[name] = value
        time.sleep(self.delay)

      # self.send(data)
      self.save(data)
    except Exception as e:
      exception(e)

  def close(self):
    self.client.close()


if __name__ == "__main__":

  mon = PowerEMS300(serial="EMS300-1", host="192.168.86.184", port=502, period=30, output_path="ems300.json")
  mon.start()

  while(True):
    time.sleep(30)
