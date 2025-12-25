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

import struct
import math
from sciveo.tools.logger import *


def to_u16(regs):
  return regs[0] & 0xFFFF

def to_s16(regs):
  v = regs[0] & 0xFFFF
  return v - 0x10000 if v & 0x8000 else v

def to_u32_le_words(regs):
  # device transmits U32 double-word as little-endian word order:
  # Example in doc: 0x01020304 transmitted as 03,04,01,02 => regs[0]=0x0304, regs[1]=0x0102
  return ((regs[1] & 0xFFFF) << 16) | (regs[0] & 0xFFFF)

def to_s32_le_words(regs):
  v = to_u32_le_words(regs)
  return v - 0x100000000 if v & 0x80000000 else v

def to_u64_be(regs):
  # U64 big-endian: regs[0] = highest word
  return ((regs[0] & 0xFFFF) << 48) | ((regs[1] & 0xFFFF) << 32) | ((regs[2] & 0xFFFF) << 16) | (regs[3] & 0xFFFF)

def to_s64_be(regs):
  v = to_u64_be(regs)
  return v - 0x10000000000000000 if v & (1 << 63) else v

def float_from_words_be(regs):
  # regs[0] = high word, regs[1] = low word -> bytes: [hi_hi, hi_lo, lo_hi, lo_lo]
  b = (int(regs[0]) & 0xFFFF).to_bytes(2, "big") + (int(regs[1]) & 0xFFFF).to_bytes(2, "big")
  return struct.unpack(">f", b)[0]

def float_from_words_le(regs):
  # little-endian word order: regs[0] = low word, regs[1] = high word
  # reconstruct big-endian 4 bytes by swapping words
  b = (int(regs[1]) & 0xFFFF).to_bytes(2, "big") + (int(regs[0]) & 0xFFFF).to_bytes(2, "big")
  return struct.unpack(">f", b)[0]

def to_float_best(regs):
  """
  Try decoding FLOAT taking into account vendor word-order quirks.
  Prefer little-endian word order (as documented for U32), but fall back
  to big-endian word order if the result looks more reasonable.
  """
  try:
    val_le = float_from_words_le(regs)
  except Exception:
    val_le = None
  try:
    val_be = float_from_words_be(regs)
  except Exception:
    val_be = None

  def good(v):
    return v is not None and math.isfinite(v)

  if good(val_le) and not good(val_be):
    return val_le
  if good(val_be) and not good(val_le):
    return val_be
  if good(val_le) and good(val_be):
    if abs(val_le) < abs(val_be):
      return val_le
    return val_be
  return None

# Known register map (protocol addresses as in documentation). Format: addr: (type, factor, name)
EMS300_REG_MAP = {
  8018: ("U32", 1, "LC Total Number"),
  8020: ("U32", 1, "Total Number of Available LC"),
  8022: ("FLOAT", 1000, "Total Rated Power of Energy Storage"),
  8026: ("U32", 0.1, "Actual SOC"),
  8038: ("S32", 1, "Energy Storage Power"),
  8040: ("U32", 1, "Available Time for Maximum Power Discharging"),
  8042: ("U32", 1, "Available Time for Maximum Power Charging"),
  8044: ("S32", 1, "Plant Active Power"),
  8046: ("U32", 0.001, "Grid Frequency"),
  8048: ("S32", 1, "Plant Reactive Power"),
  8050: ("U32", 1, "BusVoltage"),
  8052: ("S32", 0.001, "Power Factor"),
  8056: ("S32", 1, "Photovoltaic Power Rating"),
  8058: ("S32", 1, "PV Available Reactive Power"),
  8060: ("S32", 1, "PV Active Power"),
  8062: ("S32", 1, "PV Reactive Power"),
  8064: ("U32", 1, "PV Subarray Number"),
  8070: ("U32", 1, "SOC Upper Limit Level 1 Protection"),
  8072: ("U32", 1, "SOC Lower Limit Level 1 Protection"),
  8074: ("U32", 1, "Total Field Charge Capacity"),
  8076: ("U32", 1, "Total Field Discharge Capacity"),
  8092: ("U32", 1, "Available Time of Real-time Charging"),
  8094: ("U32", 1, "Available Time of Real-time Discharging"),
  8098: ("U16", 1, "Charging Complete"),
  8099: ("U16", 1, "Discharge Completed"),
  8100: ("U16", 1, "Charge Locked"),
  8101: ("U16", 1, "Discharge Locked"),
  8297: ("U16", 1, "Plant Stop in Running Status"),
  8298: ("U16", 1, "Plant Standby in Running Status"),
  8299: ("U16", 1, "Plant Discharge in Running Status"),
  8300: ("U16", 1, "Plant Charge in Running Status"),
  8301: ("U16", 1, "Plant Fault in Running Status"),
  8485: ("FLOAT", 1, "Residual Capacity of Energy Storage"),
  8487: ("U16", 0.1, "Battery Voltage"),
  8488: ("FLOAT", 1000, "Active Load"),
  8490: ("FLOAT", 1000, "Rated Capacity of Energy Storage"),
  8492: ("U16", 1, "System Operating Status"),
  8493: ("U64", 1, "Start and Stop Process Status Word"),
  8638: ("FLOAT", 1, "Total DC Side Power of ESS"),
  8726: ("U16", 1, "Number of On-grid Devices"),
  8727: ("U16", 1, "Number of Off-grid Devices"),
  8728: ("FLOAT", 1, "Energy Storage SOC"),
  8733: ("FLOAT", 1, "Total Active Power of Chargers in the Plant"),
  8735: ("FLOAT", 1, "Total Energy Delivered by Chargers in the Plant"),
  8752: ("FLOAT", 1, "Upper Limit of Available Active Power of Plant"),
  8754: ("FLOAT", 1, "Lower Limit of Available Active Power of Plant"),
  8756: ("FLOAT", 1, "Available Plant Reactive Power"),
  8758: ("FLOAT", 0.1, "Active Power of Energy Storage"),
  8760: ("FLOAT", 0.1, "Reactive Power of Energy Storage"),
  8762: ("U32", 0.1, "Maximum SOC"),
  8766: ("U32", 0.1, "Minimum SOC"),
  8768: ("U32", 0.1, "Maximum Charging Power Allowed"),
  8770: ("U32", 0.1, "Maximum Discharging Power"),
  8772: ("U32", 0.1, "ESS Daily Charge"),
  8774: ("U32", 0.1, "ESS Daily Discharge"),
  8776: ("U32", 0.1, "System Dischargeable Energy"),
  8778: ("U32", 0.1, "System Chargeable Capacity"),
  9082: ("FLOAT", 1, "Dynamic Allowable Charging Power"),
  9084: ("FLOAT", 1, "Dynamic Allowable Discharging Power"),
  9086: ("U16", 1, "ESS Operating Status"),
  9087: ("FLOAT", 1, "ESS Power Factor"),
  9089: ("FLOAT", 1, "ESS SOH"),
  9115: ("FLOAT", 1, "ESS Grid-Connection Point Meter Total Daily Charge"),
  9117: ("FLOAT", 1, "ESS Grid-Connection Point Meter Total Daily Discharge"),
  9119: ("U16", 1, "ESS Fault"),
  9120: ("U16", 1, "Energy Storage Alarm"),
  9121: ("U16", 1, "ESS Communication Failure"),
  9122: ("U16", 1, "ESS HVAC Fault"),
  9424: ("U16", 1, "Active Power Limit Ratio"),
  8102: ("U16", 1, "Communication Status"),
  8302: ("U16", 1, "Device Alarm"),
  8303: ("U16", 1, "Device Fault"),
  8347: ("U16", 1, "Device Model"),
  8341: ("FLOAT", 1, "Daily Yield, kWh"),
  8379: ("U16", 1, "SN Code"),
  8389: ("U16", 1, "ETH1 mac"),
  8421: ("U16", 1, "ETH2 mac"),
  8453: ("U16", 1, "ETH3 mac"),
  8730: ("U16", 1, "Serial Port Communication Interrupted"),
  8731: ("U16", 1, "TCP Communication Interrupted"),
  8732: ("U16", 1, "Host EMS Communication Fault"),
  10601: ("U16", 1, "DI1 Value"),
  8554: ("U16", 1, "Host and Client Status"),
  8555: ("U16", 1, "Cascading"),
  8700: ("U16", 1, "Debugging Mode"),
  8711: ("U16", 1, "ESS Connection Point"),
  8712: ("U16", 1, "PV Connection Point"),
  8682: ("FLOAT", 1, "Replacement Percentage"),
  8713: ("U16", 1, "Energy Storage Data Source"),
  9826: ("U16", 1, "Select Power Distribution Strategy"),
  8570: ("U16", 1, "Mode selection"),
  8780: ("U16", 1, "Time-of-Use Power Period 1 Time Type"),
  8781: ("U16", 1, "Start Time of Time of Use Power Period 1"),
  8782: ("U16", 1, "End Time of Time of Use Power Period 1"),
  8783: ("FLOAT", 1, "Power Setting of Time of Use Power Period 1"),
  8785: ("U16", 1, "Time-of-Use Power Period 1 Charging/Discharging Status"),
  8894: ("U16", 1, "Time-of-Use Power Period 20 Time Type"),
  8895: ("U16", 1, "Start Time of Time of Use Power Period 20"),
  8896: ("U16", 1, "End Time of Time of Use Power Period 20"),
  8897: ("FLOAT", 1, "Power Setting of Time of Use Power Period 20"),
  8899: ("U16", 1, "Time-of-Use Power Period 20 Charging/Discharging Status"),
  9425: ("U16", 1, "Time-of-Use Power Minute/Second Mode"),
  9426: ("U16", 1, "Time-of-Use Power Second-Mode Period 1 Time Type"),
  9427: ("U32", 1, "Time-of-Use Power Second-Mode Period 1 Start Time"),
  9429: ("U32", 1, "Time-of-Use Power Second-Mode Period 1 End Time"),
  9431: ("FLOAT", 1, "Time-of-Use Power Second-Mode Period 1 Power"),
  9433: ("U16", 1, "Time-of-Use Power Second-Mode Period 1 Charging/Discharging Status"),
  9578: ("U16", 1, "Time-of-Use Power Second-Mode Period 20 Time Type"),
  9579: ("U32", 1, "Time-of-Use Power Second-Mode Period 20 Start Time"),
  9581: ("U32", 1, "Time-of-Use Power Second-Mode Period 20 End Time"),
  9583: ("FLOAT", 1, "Time-of-Use Power Second-Mode Period 20 Power"),
  9585: ("U16", 1, "Time-of-Use Power Second-Mode Period 20 Charging/Discharging Status"),
  9123: ("FLOAT", 1, "Remotely Set Time-of-Use Power Period 1 Start Time"),
  9125: ("FLOAT", 1, "Remotely Set Time-of-Use Power Period 1 End Time"),
  9127: ("FLOAT", 1, "Remotely Set Time-of-Use Power Period 1 Power"),
  9417: ("FLOAT", 1, "Remotely Set Time-of-Use Power Period 50 Start Time"),
  9419: ("FLOAT", 1, "Remotely Set Time-of-Use Power Period 50 End Time"),
  9421: ("FLOAT", 1, "Remotely Set Time-of-Use Power Period 50 Power"),
  8103: ("U16", 1, "Active Power Control Running Status"),
  8547: ("FLOAT", 1000, "Setting Feedback Value of Active Power"),
  8560: ("FLOAT", 1, "Active Power Control Dead Zone"),
  8710: ("U16", 1, "Scheduled Object"),
  9423: ("U16", 1, "Control Priority"),
  8714: ("U16", 1, "Operation Mode upon Communication Interruption"),
  8565: ("U32", 1, "Communication Interruption Time"),
  8567: ("U32", 1, "Communication Interruption Counting Period"),
  8569: ("U16", 1, "Communication Interruption Counts"),
  8105: ("U32", 1, "AGC_PLAN_001"),
  8107: ("U32", 1, "AGC_PLAN_002"),
  8293: ("U32", 1, "AGC_PLAN_095"),
  8295: ("U32", 1, "AGC_PLAN_096"),
  8304: ("U16", 1, "AGC Allow Control"),
  8305: ("U16", 1, "AGC Remote/Local Status"),
  8306: ("U16", 1, "AVC Turn Up Lock"),
  8307: ("U16", 1, "AVC Turn Down Lock"),
  8308: ("U16", 1, "AVC Allow Control"),
  8309: ("U16", 1, "AVC Remote/Local Status"),
  8104: ("U16", 1, "Reactive Power Control Running Status"),
  8549: ("FLOAT", 1000, "Setting Feedback Value of Reactive Power"),
  8562: ("FLOAT", 1, "Reactive Power Control Dead Zone"),
  8090: ("S32", 0.001, "Local Power Factor Set Value"),
  8689: ("U16", 1, "Execute Strategy Only When ESS is Discharging"),
  8693: ("FLOAT", 1, "Charge Step Factor"),
  8695: ("FLOAT", 1, "Discharge Step Factor"),
  8697: ("U16", 1, "Adjustment Period"),
  8698: ("FLOAT", 1, "System Discharge Threshold"),
  8706: ("FLOAT", 1, "PV Active Power Ratio K1"),
  8708: ("FLOAT", 1, "PV Active Power Ratio K2"),
  9827: ("FLOAT", 1, "Regular Load Power"),
  9829: ("FLOAT", 1, "SOC Threshold to Stop Supplying Power to Charger"),
  9831: ("FLOAT", 1, "Proportion of Stable Loads"),
  9836: ("U16", 1, "VSG Parameter Management"),
  9837: ("FLOAT", 1, "Output Voltage Setpoint"),
  9839: ("FLOAT", 1, "Output Voltage Setpoint (Hz)"),
  9841: ("FLOAT", 1, "Active Power-Frequency Droop Coefficient"),
  9843: ("FLOAT", 1, "Reactive Power-Voltage Droop Coefficient"),
  9845: ("FLOAT", 1, "Sent Active Power Setpoint"),
  9847: ("FLOAT", 1, "Sent Reactive Power Setpoint"),
  8640: ("U16", 1, "Frequency Droop Control Enable/Disable"),
  8642: ("U16", 1, "Frequency Response Type"),
  8310: ("U16", 1, "Frequency Control Running Flag"),
  8311: ("U32", 1, "Primary Frequency Regulation Control"),
  8313: ("U16", 1, "Primary Frequency Regulation Exit Signal"),
  8314: ("U16", 1, "Number of FM Algorithm Segments"),
  8315: ("U32", 0.001, "Rated Frequency of Grid-connection Point"),
  8317: ("U32", 0.01, "Frequency Regulation Coefficient"),
  8319: ("U32", 0.001, "Frequency Regulation Dead Zone"),
  8321: ("U32", 0.001, "Maximum Active Power Output"),
  8323: ("U32", 0.001, "Maximum Active Power Absorbed"),
  8325: ("U32", 0.001, "Lower Limit of Active Power Limit Coefficient"),
  8327: ("U32", 0.001, "Upper Limit of Active Power Limit Coefficient"),
  8329: ("U32", 0.01, "Frequency Regulation II Regulation Coefficient"),
  8331: ("U32", 0.001, "Frequency Regulation II Dead Zone"),
  8333: ("U32", 0.01, "Active Power Before Primary Frequency Regulation"),
  8335: ("U32", 0.01, "Active Power After Primary Frequency Regulation"),
  8645: ("FLOAT", 1, "Contingency FCAS Action Deadband fd"),
  8647: ("FLOAT", 1, "Contingency FCAS Maximum Output Active Power PA"),
  8649: ("FLOAT", 1, "Contingency FCAS Maximum Absorption Active Power PB"),
  8651: ("FLOAT", 1, "Contingency FCAS Frequency Deviation Threshold for Full-Scale Response"),
  8655: ("U16", 1, "Demand Control"),
  8656: ("U16", 1, "Select Strategy"),
  8657: ("U16", 1, "Allow ESS to Discharge or Not"),
  8658: ("FLOAT", 1, "Max. Allowable Demand"),
  8660: ("FLOAT", 1, "Lower Limit for Demand Control"),
  8662: ("U16", 1, "Reverse Power Protection"),
  8663: ("U16", 1, "Allow ESS charging during reverse power flow"),
  8664: ("FLOAT", 1, "Target Active Power of Reverse Power Protection"),
  8337: ("U32", 1, "Transformer Capacity"),
  8339: ("FLOAT", 1, "Active Power Conversion Coefficient"),
  8653: ("U16", 1, "Overload Protection"),
  8654: ("U16", 1, "Dynamic Capacity Expansion"),
  8666: ("U16", 1, "Power Backup"),
  8679: ("FLOAT", 1, "Recharging Power"),
  9833: ("FLOAT", 1, "K Value When Prioritizing ESS Charge"),
  8066: ("U32", 1, "SOC Upper Limit"),
  8068: ("U32", 1, "SOC Lower Limit"),
  8690: ("U32", 1, "SOC Balancing"),
  8667: ("FLOAT", 1, "SOC Upper Limit Level 1 Protection"),
  8669: ("FLOAT", 1, "SOC Upper Limit Level 1 Recovery"),
  8671: ("FLOAT", 1, "SOC Lower Limit Level 1 Recovery"),
  8673: ("FLOAT", 1, "SOC Lower Limit Level 1 Protection"),
  8675: ("FLOAT", 1, "SOC Lower Limit Level 2 Recovery"),
  8677: ("FLOAT", 1, "SOC Lower Limit Level 2 Protection"),
  8553: ("U16", 1, "Grid-connected/Off-grid Startup"),
  8715: ("U16", 1, "Inverter Operating Mode"),
  8718: ("FLOAT", 1, "Black Start SOC Threshold"),
  8720: ("U16", 1, "Minimum Number of Running Units"),
  8721: ("FLOAT", 1, "Load Rated Power"),
  8723: ("U16", 1, "System Waiting time"),
  8724: ("U16", 1, "System Timeout"),
   8725: ("U16", 1, "Charging Initialization Mode"),
  9855: ("U16", 1, "Auto-start on Recovery from System Fault"),
  9854: ("U16", 1, "Function Mode"),
  10001: ("U16", 1, "Total Number of Connected Devices"),
  10002: ("U16", 1, "Total Number of Fault Count"),
  10101: ("S32", 0.01, "Total Active Power"),
  10103: ("S32", 0.01, "Gateway Meter Active Power"),
  10105: ("S32", 0.01, "Load Power"),
  10107: ("U32", 0.1, "Gateway Meter Import Energy"),
  10109: ("U32", 0.1, "Gateway Meter Export Energy"),
  10501: ("U16", 1, "Device Type Code"),
  10502: ("U32", 1, "Protocol No."),
  10504: ("U32", 1, "Protocol Version No."),
  10506: ("U32", 1, "DI Status"),
  10701: ("U32", 0.1, "Max. Total Rated Active Power"),
  10703: ("U32", 0.1, "Total Battery Rated Capacity"),
  10705: ("U32", 0.1, "Battery Charge/Discharge Maximum Description"),
  10707: ("U16", 0.1, "Maximum Battery Charge Power"),
  10708: ("U16", 0.1, "Minimum Battery Charge Power"),
  10709: ("U16", 0.1, "Maximum Battery Discharge Power"),
  10710: ("U16", 0.1, "Minimum Battery Discharge Power"),
  10713: ("S32", 0.01, "Battery Power"),
  10715: ("U16", 0.1, "Battery level (SOC)"),
  10716: ("U32", 0.1, "Daily Battery Charging Energy"),
  10718: ("U32", 0.1, "Daily Battery Discharging Energy"),
  10720: ("U64", 0.1, "Total Battery Charging Energy"),
  10724: ("U64", 0.1, "Total battery discharge"),
  10901: ("U16", 1, "Maximum Total PV Rated Active Power"),
  10902: ("U16", 1, "Minimum Total PV Rated Active Power"),
  10903: ("U16", 1, "Maximum Total PV Rated Reactive Power"),
  10904: ("S16", 1, "Minimum Total PV Rated Reactive Power"),
  10905: ("U16", 1, "Set Total Inverter Active Power"),
  10906: ("S16", 1, "Set Total Inverter Reactive Power"),
  10909: ("S64", 1, "P-total-PV"),
  10913: ("U32", 0.1, "Daily PV yield"),
  10915: ("S64", 1, "Q-total-PV"),
  10919: ("U64", 0.1, "Total PV Yield"),
  10923: ("U32", 0.1, "PV Min. adjustable active power"),
  10925: ("U32", 0.1, "PV Max. adjustable active power"),
  10927: ("S32", 0.1, "PV Min. Adjustable Reactive Power"),
  10929: ("S32", 0.1, "PV Max. Adjustable Reactive Power"),
  10931: ("S32", 0.1, "PV Rated Active Power"),
  10933: ("S32", 0.1, "PV Rated Reactive Power"),
  10935: ("U16", 1, "Total Grid-Connected Inverter Devices"),
  10936: ("U16", 1, "Total Off-Grid Inverter Devices"),
  10937: ("U64", 0.1, "Monthly PV Yield"),
  10941: ("U64", 0.1, "PV Annual Yield"),
  10945: ("U64", 1, "PV Apparent Power"),
  10949: ("U16", 0.1, "PV Active Power Dispatching Ratio"),
  11804: ("U16", 1, "2030.5 Feed-in Control Method"),
  11805: ("S32", 0.01, "2030.5 Feed-in Limitation Value"),
  11807: ("S16", 0.1, "2030.5 Feed-in Limitation Ratio"),
}

def count_for_type(t):
  return {"U16": 1, "S16": 1, "U32": 2, "S32": 2, "U64": 4, "S64": 4, "FLOAT": 2}.get(t, 1)

def decode_registers(regs, dtype):
  if dtype == "U16":
    return to_u16(regs)
  if dtype == "S16":
    return to_s16(regs)
  if dtype == "U32":
    return to_u32_le_words(regs)
  if dtype == "S32":
    return to_s32_le_words(regs)
  if dtype == "U64":
    return to_u64_be(regs)
  if dtype == "S64":
    return to_s64_be(regs)
  if dtype == "FLOAT":
    return to_float_best(regs)
  return None

def read_input_registers(client, REG_MAP, addr, device_id):
  try:
    dtype, factor, name = REG_MAP[addr]
    count = count_for_type(dtype)
    protocol_addr = addr - 1
    rr = client.read_input_registers(address=protocol_addr, count=count, device_id=device_id)
    if rr is None:
      warning(f"No response for {addr} ({name})")
      return None
    if hasattr(rr, "isError") and rr.isError():
      warning(f"Modbus exception at {addr} ({name}): {rr}")
      return None
    regs = getattr(rr, "registers", None)
    if not regs or len(regs) < count:
      warning(f"Incomplete registers at {addr} ({name}): {regs}")
      return None
    val_raw = decode_registers(regs, dtype)
    if val_raw is None:
      warning(f"Unable to decode {addr} ({name}) regs={regs}")
      return None
    value = val_raw * factor
    # format integer-looking floats without trailing .0
    if isinstance(value, float) and value.is_integer():
      value = int(value)
    debug(f"{addr} {name}: raw={regs} -> {value} (factor={factor}, type={dtype})")
  except Exception as e:
    exception(e, f"read_input_registers::reading {addr} ({name})")
    return None
  return value, name, dtype
