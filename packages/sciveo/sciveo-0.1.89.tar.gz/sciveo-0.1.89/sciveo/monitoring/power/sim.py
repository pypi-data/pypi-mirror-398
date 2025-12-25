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

import time
import threading
import time
from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusServerContext, ModbusSparseDataBlock
from threading import Thread
from sciveo.tools.logger import *
from sciveo.tools.daemon import DaemonBase


# Example read-only registers
# INITIAL_REGISTERS = {
#     8044: 12500,   # Plant Active Power
#     8060: 8200,    # PV Active Power
#     8038: -1500,   # Storage Power
#     8048: 600,     # Reactive Power
#     9082: 3000,    # Dynamic Allowable Charge Power
#     9084: 3500,    # Dynamic Allowable Discharge Power
# }
INITIAL_REGISTERS = {
  8060: 8200,    # PV Active Power
}

class SimulatorEMS300(DaemonBase):
  def __init__(self, host="127.0.0.1", port=5020, period=1):
    super().__init__(num_threads=1, period=period)
    self.host = host
    self.port = port

    # Only input registers
    self.ir_block = ModbusSparseDataBlock(INITIAL_REGISTERS.copy())

    self.context = ModbusServerContext(
      { 247: {  # unit_id -> datastore dict
          'di': ModbusSparseDataBlock({}),   # discrete inputs
          'co': ModbusSparseDataBlock({}),   # coils
          'hr': ModbusSparseDataBlock({}),   # holding registers
          'ir': self.ir_block                # input registers
        }
      },
      single=False  # multiple units not used here, keep False
    )

  def loop(self):
    # Slowly vary PV Active Power
    pv = self.ir_block.getValues(8060, count=1)[0]
    pv = (pv + 50) % 15000
    self.ir_block.setValues(8060, [pv])
    info(f"Simulated PV Active Power: {pv}")

  def start_server(self):
    StartTcpServer(self.context, address=(self.host, self.port))


if __name__ == "__main__":
    sim = SimulatorEMS300(host="127.0.0.1", port=1502)
    sim.start()
    sim.start_server()
    while True:
      time.sleep(10)
