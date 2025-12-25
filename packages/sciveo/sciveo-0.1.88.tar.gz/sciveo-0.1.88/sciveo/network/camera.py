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
import threading
import cv2
import numpy as np
from scapy.all import sniff, IP, TCP, UDP

from sciveo.tools.logger import *
from sciveo.tools.timers import FPSCounter
from sciveo.network.tools import StreamSniffer


class RTSPStreamSniffer(StreamSniffer):
  def __init__(self, iface=None, port=554):
    super().__init__(iface)
    self.port = port

  def on_packet(self, packet):
    if self.is_rtsp_packet(packet):
      self.append_ip_packet(packet)

  def is_rtsp_packet(self, packet):
    return IP in packet and TCP in packet and (packet[TCP].dport == self.port or packet[TCP].sport == self.port)
    # return IP in packet and ( (TCP in packet and (packet[TCP].dport == self.port or packet[TCP].sport == self.port)) or (UDP in packet and (packet[UDP].dport == self.port or packet[UDP].sport == self.port)) )

  def get_rtsp_frames(self, ip_src):
    frames = []
    current_packets = self.get_ip_stream(ip_src)
    for packet in current_packets:
      frame = self.packet_to_frame(packet)
      if frame is not None:
        frames.append(frame)
    return frames

  def packet_to_frame(self, packet):
    payload = bytes(packet[TCP].payload)
    nparr = np.frombuffer(payload, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return frame

  def play(self, ip_src):
    fps = FPSCounter(tag=f"play {ip_src}")
    while True:
      frames = self.get_rtsp_frames(ip_src)
      for frame in frames:
        fps.update()
        cv2.imshow(f'RTSP Stream from {ip_src}', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
          return

  def play_cams(self, list_cams):
    threads = []
    for ip in list_cams:
      t = threading.Thread(target=self.play, args=(ip,))
      t.start()
      threads.append(t)

    self.start()

    try:
      while True:
        time.sleep(1)
    except KeyboardInterrupt:
      self.stop()
      for t in threads:
        t.join()
      cv2.destroyAllWindows()


if __name__ == '__main__':
  sniffer = RTSPStreamSniffer(iface="en0", port=554)
  sniffer.play_cams([])
