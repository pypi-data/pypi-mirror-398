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

import numpy as np
import time
import cv2

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GObject, GstRtspServer, GLib
Gst.init(None)

from sciveo.tools.logger import *
from sciveo.tools.daemon import DaemonBase
from sciveo.tools.timers import FPSCounter
from sciveo.media.capture.draw import *
from sciveo.media.capture.cam import CameraDaemon


class RTSPFactoryBase(GstRtspServer.RTSPMediaFactory):
  def __init__(self, width, height, fps, appsrc_name="rtspvideo", display=None):
    super().__init__()
    self.width = width
    self.height = height
    self.fps = fps
    self.frame = None
    self.appsrc_name = appsrc_name
    self.display = display
    self.set_shared(True)
    self.fps_next_frame = FPSCounter(period=10, tag=f"{appsrc_name} ({self.width}x{self.height}@{self.fps})", round_value=1)

  def do_create_element(self, url):
    pipeline_str = (
      f"appsrc name={self.appsrc_name} is-live=true block=true format=time "
      f"caps=video/x-raw,format=BGR,width={self.width},height={self.height},framerate={self.fps}/1 "
      "! videoconvert "
      "! video/x-raw,format=I420 "
      "! x264enc tune=zerolatency speed-preset=ultrafast key-int-max=30 "
      "! rtph264pay config-interval=1 name=pay0 pt=96"
    )
    info("GST Pipeline", pipeline_str)
    return Gst.parse_launch(pipeline_str)

  def do_configure(self, rtsp_media):
    self.appsrc = rtsp_media.get_element().get_child_by_name(self.appsrc_name)
    self.appsrc.connect("need-data", self.on_need_data)
    self.timestamp = 0

  def on_need_data(self, src, length):
    self.frame = self.next_frame()
    self.frame = np.ascontiguousarray(self.frame, dtype=np.uint8)

    data = self.frame.tobytes()
    buf = Gst.Buffer.new_allocate(None, len(data), None)
    buf.fill(0, data)

    buf.duration = Gst.SECOND // self.fps
    buf.pts = buf.dts = self.timestamp
    self.timestamp += buf.duration

    src.emit("push-buffer", buf)

  def next_frame(self):
    return np.zeros((self.height, self.width, 3), dtype=np.uint8)

  def play_imshow(self):
    if self.frame is not None:
      cv2.imshow(f"{self.appsrc_name} {self.frame.shape}", self.frame)
      cv2.waitKey(1)
    return True

  def serve(self, host="0.0.0.0", port=8554, stream="test"):
    rtsp_url = f"rtsp://{host}:{port}/{stream}"
    server = GstRtspServer.RTSPServer()
    server.set_address(host)
    server.set_service(str(port))

    mount_points = server.get_mount_points()
    mount_points.add_factory(f"/{stream}", self)

    server.attach(None)

    if self.display is not None:
      # Consider more display options along with current cv2.imshow()
      if self.display == 0:
        GLib.idle_add(self.play_imshow)
      else:
        GLib.idle_add(self.play_imshow)

    info(f"RTSP server {type(self).__name__} running at {rtsp_url}")
    GLib.MainLoop().run()


"""
  RTSP TV-like Color Bars Test Generator
"""
class ColorBarsGenerator:
  """
  Generates standard vertical color bars (SMPTE/EBU-like) for testing.
  """
  def __init__(self, width=640, height=480):
    self.width = width
    self.height = height
    self.colors = [
      (255, 255, 255),  # White
      (0, 255, 255),    # Yellow
      (255, 255, 0),    # Cyan
      (0, 255, 0),      # Green
      (255, 0, 255),    # Magenta
      (0, 0, 255),      # Red
      (255, 0, 0),      # Blue
      (0, 0, 0)         # Black
    ]
    self.n_colors = len(self.colors)

  def next_frame(self):
    frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
    bar_width = self.width // self.n_colors

    for i, color in enumerate(self.colors):
      start_x = i * bar_width
      end_x = start_x + bar_width if i < self.n_colors - 1 else self.width
      frame[:, start_x:end_x] = color

    return frame


class ColorBarFactory(RTSPFactoryBase):
  def __init__(self, width, height, fps, appsrc_name="colorbar", display=None):
    super().__init__(width, height, fps, appsrc_name=appsrc_name, display=display)
    self.gen = ColorBarsGenerator(width=width, height=height)

  def next_frame(self):
    self.fps_next_frame.update()
    return self.gen.next_frame()


class CamFactory(ColorBarFactory):
  def __init__(self, cam_id, width, height, fps, configuration={}, display=None):
    super().__init__(width, height, fps, appsrc_name=f"cam{cam_id}", display=display)
    self.cam_id = cam_id
    self.configuration = configuration
    self.list_draw_processors = {
      "none": DrawNone(),
      "dt": DrawDateTime(),
    }

    self.init_cam()
    self.cam.start()

  def init_cam(self):
    if "RPI" in self.configuration:
      from sciveo.media.capture.rpi import RPICamera
      self.cam = RPICamera(cam_id=self.cam_id, width=self.width, height=self.height)
    else:
      self.cam = CameraDaemon(cam_id=self.cam_id)

  def read_cam_frame(self):
    try:
      frame = self.cam.read()
    except Exception as e:
      exception(e, "CAM frame read FAIL")
      frame = None
    return frame

  def next_frame(self):
    frame = self.read_cam_frame()

    if frame is None:
      frame = super().next_frame()

    try:
      for k, v in self.configuration.get("draw", {}).items():
        self.list_draw_processors.get(k, DrawNone())(frame, v)
    except Exception as e:
      exception(e, "DRAW FAIL")

    self.fps_next_frame.update()

    return frame


if __name__ == "__main__":

    # server = ColorBarFactory(640, 480, 10)
    # server.serve(host="0.0.0.0", port=8554, stream="test")

    server = CamFactory(0, 640, 480, 30, list_draw={"dt": "cam-test"}, display=0)
    server.serve(host="0.0.0.0", port=8554, stream="camera")
