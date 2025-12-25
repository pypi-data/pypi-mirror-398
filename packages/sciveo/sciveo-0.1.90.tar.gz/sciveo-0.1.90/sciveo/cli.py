#!/usr/bin/env python
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
import json
import argparse

from sciveo.version import __version__
from sciveo.tools.logger import *
from sciveo.tools.configuration import GlobalConfiguration


def main():
  config = GlobalConfiguration.get()

  parser = argparse.ArgumentParser(description=f'{config.name} CLI')
  parser.add_argument(
    'command',
    choices=[
      'init', 'monitor', 'scan',
      'nvr', 'rtsp', 'capture',
      'predictors-server', 'media-server', 'media-run',
      'watchdog',
    ],
    help='Command to execute')

  parser.add_argument('--period', type=int, default=120, help='Period in seconds')
  parser.add_argument('--block', type=bool, default=True, help='Block flag')
  parser.add_argument('--auth', type=str, default=config['secret_access_key'], help='Auth secret access key')
  parser.add_argument('--timeout', type=float, default=1.0, help='Timeout')
  parser.add_argument('--net', type=str, default=None, help='Network like 192.168.10.0/24')
  parser.add_argument('--url', type=str, default=None, help='URL')
  parser.add_argument('--host', type=str, default=None, help='Host ip or name')
  parser.add_argument('--port', type=int, default=22, help='Host port number, used for network ops')
  parser.add_argument('--ports', type=str, default="[]", help='Host ports list')
  parser.add_argument('--localhost', type=bool, default=False, help='Add localhost to list of hosts')
  parser.add_argument('--input-path', type=str, default=None, help='Input Path')
  parser.add_argument('--output-path', type=str, default=None, help='Output Path')
  parser.add_argument('--width', type=int, default=None, help='width')
  parser.add_argument('--height', type=int, default=None, help='height')
  parser.add_argument('--fps', type=int, help='FPS')
  parser.add_argument('--stream', type=str, default=None, help='Stream')
  parser.add_argument('--rate', type=int, help='Rate number')
  parser.add_argument('--processor', type=str, help='Processor name')
  parser.add_argument('--src', type=str, default=None, help='Source')
  parser.add_argument('--src-id', type=int, default=None, help='Source Id')
  parser.add_argument('--dst', type=str, default=None, help='Destination')
  parser.add_argument('--value', type=float, help='Value')
  parser.add_argument('--threshold', type=float, default=None, help='Threshold')
  parser.add_argument('--execute', type=str, default=None, help='Execute command')
  parser.add_argument('--pid', type=int, default=None, help='Process PID')
  parser.add_argument('--serial', type=str, default=None, help='Serial Name')
  parser.add_argument('--data-json', type=str, default="{}", help='Json Data')
  parser.add_argument('--display', type=int, default=None, help='Display number')

  args = parser.parse_args()

  if args.command == 'monitor':
    if args.src is None:
      from sciveo.monitoring.start import MonitorStart
      MonitorStart(period=args.period, block=args.block, output_path=args.output_path)()
    elif args.src.startswith("power"):
      from sciveo.monitoring.power.ems300 import PowerEMS300
      mon = PowerEMS300(serial=args.serial, host=args.host, port=args.port, period=args.period, output_path=args.output_path)
      mon.start()
      while(True):
        time.sleep(3600)
  elif args.command == 'scan':
    from sciveo.network.tools import NetworkTools
    host=args.host
    if host is None:
      NetworkTools(timeout=args.timeout, localhost=args.localhost).scan_port(port=args.port, network=args.net)
    else:
      NetworkTools(timeout=args.timeout, ports=json.loads(args.ports)).scan_host(host)
  elif args.command == 'init':
    info(f"init {config.name} ver {__version__}")
    home = os.path.expanduser('~')
    base_path = os.path.join(home, f'.{config.name}')
    if not os.path.exists(base_path):
      os.makedirs(base_path)
      default_lines = [
        "secret_access_key=<your secret access key>",
        f"api_base_url=https://{config.name}.com",
        "sci_log_level=DEBUG"
      ]
      with open(os.path.join(base_path, "default"), 'w') as fp:
        for line in default_lines:
          fp.write(line + '\n')
    else:
      info(f"init, [{base_path}] already there")
  elif args.command == 'nvr':
    from sciveo.media.capture.nvr import VideoRecorder
    VideoRecorder(args.input_path).start()
  elif args.command == 'rtsp':
    if args.src is None and args.src_id is None:
      from sciveo.media.capture.nvr import RTSPVideoPlayer
      if args.url is not None:
        url = args.url
      elif args.host is not None and args.stream is not None:
        url = f"rtsp://{args.host}:{args.port}/{args.stream}"
      else:
        warning("Invalid URL")
        return
      player = RTSPVideoPlayer(url)
      player.run()
    else:
      from sciveo.media.capture.gst_server import CamFactory, ColorBarFactory
      data = json.loads(args.data_json)
      if args.src_id is not None:
        server = CamFactory(args.src_id, args.width, args.height, args.fps, configuration=data, display=args.display)
      elif args.src is not None:
        if "color" in args.src:
          server = ColorBarFactory(args.width, args.height, args.fps, display=args.display)
        else:
          # warning("RTSP src", args.src, "not recognised")
          server = CamFactory(args.src, args.width, args.height, args.fps, configuration=data, display=args.display)
        server.serve(host=args.host, port=args.port, stream=args.stream)
  elif args.command == 'capture':
    from sciveo.media.capture.cam import CameraDaemon, ScreenDaemon, CapturePlayer
    if args.src == "screen":
      cap = ScreenDaemon(src=args.src_id, region=json.loads(args.data_json))
    elif args.src == "cam":
      cap = CameraDaemon(cam_id=args.src_id)
    elif args.src == "rpi":
      from sciveo.media.capture.rpi import RPICamera
      cap = RPICamera(cam_id=args.src_id, width=args.width, height=args.height)
    else:
      cap = CameraDaemon(cam_id=args.src_id)
    player = CapturePlayer(cap=cap, tag=args.src, fps=args.fps or 0)
    player.play()
  elif args.command == 'media-server':
    from sciveo.media.pipelines.server import __START_SCIVEO_MEDIA_SERVER__
    __START_SCIVEO_MEDIA_SERVER__()
  elif args.command == 'media-run':
    if args.processor == "audio-plot":
      from sciveo.media.pipelines.processors.audio.audio_extractor_process import plot_audio
      plot_audio(args.width, args.height, args.rate, args.input_path, args.output_path)
  elif args.command == 'watchdog':
    daemons = []
    if args.execute is not None:
      if args.src is None or args.src.startswith("mem"):
        from sciveo.monitoring.watchdog.base import MemoryWatchDogDaemon
        daemons.append(MemoryWatchDogDaemon(threshold_percent=args.threshold, period=args.period, command=args.execute))
      elif args.src.startswith("disk") and args.input_path is not None:
        from sciveo.monitoring.watchdog.base import DiskWatchDogDaemon
        daemons.append(DiskWatchDogDaemon(path=args.input_path, threshold_percent=args.threshold, period=args.period, command=args.execute))
      elif args.src.startswith("process"):
        from sciveo.monitoring.watchdog.process import ProcessWatchDogDaemon
        daemons.append(ProcessWatchDogDaemon(pid=args.pid, process_cmd=args.dst, period=args.period, command=args.execute, thread_inactive_threshold=args.threshold))
    for daemon in daemons:
      daemon.start()
    while(True):
      time.sleep(3600)
  elif args.command == 'predictors-server':
    GlobalConfiguration.set("API_PREDICTORS", None)
    from sciveo.api.server import WebServerDaemon
    daemons = [
      WebServerDaemon(port=args.port)
    ]
    for daemon in daemons:
      debug("starting", type(daemon).__name__)
      daemon.start()
    while(True):
      time.sleep(3600)
  else:
    warning(args.command, "not implemented")

if __name__ == '__main__':
    main()