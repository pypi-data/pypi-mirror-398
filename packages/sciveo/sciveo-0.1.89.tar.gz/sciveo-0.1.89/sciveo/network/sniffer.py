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

import socket
import threading
from scapy.all import sniff, IP, TCP

from sciveo.tools.logger import *
from sciveo.tools.timers import Timer


class StreamSniffer:
  def __init__(self, iface=None):
    self.iface = iface
    self.running = False
    self.lock = threading.Lock()
    self.streams = {}

  def start(self):
    self.running = True
    self.sniff_thread = threading.Thread(target=self.sniff_packets)
    self.sniff_thread.start()

  def stop(self):
    debug("stopping...")
    self.running = False
    self.sniff_thread.join()

  def sniff_packets(self):
    debug("start sniffing on", self.iface)
    sniff(iface=self.iface, prn=self.on_packet, stop_filter=self.should_stop)

  def on_packet(self, packet):
    if IP in packet:
      self.append_ip_packet(packet)

  def should_stop(self, packet):
    return not self.running

  def append_ip_packet(self, packet):
    ip_src = packet[IP].src
    with self.lock:
      self.streams.setdefault(ip_src, [])
      self.streams[ip_src].append(packet)

  def get_ip_stream(self, ip):
    current_packets = []
    with self.lock:
      if ip in self.streams:
        current_packets = self.streams[ip][:]
        self.streams[ip] = []
    return current_packets

  def keys(self):
    with self.lock:
      return list(self.streams.keys())


if __name__ == "__main__":
  # debug(NetworkTools(timeout=1.0, localhost=False).scan_port(port=9901))

  import time
  sniffer = StreamSniffer(iface="en0")
  sniffer.start()
  time.sleep(5)
  sniffer.stop()
  debug(sniffer.keys())