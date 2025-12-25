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
import shutil
import subprocess as sp
import time
import re
import json
import cv2
import datetime

from sciveo.tools.logger import *
from sciveo.tools.daemon import DaemonBase
from sciveo.tools.queue import TouchedFilePathQueue
from sciveo.tools.simple_counter import RunCounter
from sciveo.tools.timers import FPSCounter
from sciveo.media.capture.motion_detection import MotionDetectorDaemon


class VideoCameraCaptureDaemon(DaemonBase):
  def __init__(self, cam_id, url, dst_path, max_video_len=60, transport="tcp", max_timeout=30):
    super().__init__()
    self.cam_id = cam_id
    self.url = url
    self.dst_path = dst_path
    self.max_video_len = max_video_len
    self.max_timeout = max_timeout
    self.transport = transport
    self.cmd = [
      "ffmpeg",
      "-rtsp_transport", self.transport,
      "-i", self.url,
      "-c", "copy",
      "-acodec", "aac",
      "-f", "segment",
      "-segment_time", f"{self.max_video_len}",
      "-reset_timestamps", "1",
      "-strftime", "1",
      f"{self.dst_path}/{self.cam_id}___%Y-%m-%d___%H-%M-%S.mp4"
    ]

  def clear(self):
    os.system(f"pgrep -f \"{self.url}\" |xargs kill -9")

    files = [f for f in os.listdir(self.dst_path) if os.path.isfile(os.path.join(self.dst_path, f))]
    for file_name in files:
      if file_name.startswith(f"{self.cam_id}___"):
        file_path = os.path.join(self.dst_path, file_name)
        info("RM", file_path)
        os.remove(file_path)

  def get_current_files(self):
    current_files = [f for f in os.listdir(self.dst_path) if f.startswith(f"{self.cam_id}___") and f.endswith(".mp4")]
    current_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.dst_path, x)), reverse=True)
    return current_files

  def loop(self):
    info("start", self.cam_id)

    while True:
      self.clear()

      try:
        last_known_file = None
        last_mod_time = None
        last_progress_time = time.time()

        p = sp.Popen(self.cmd, stdout=sp.DEVNULL, stderr=sp.DEVNULL)

        while True:
          time.sleep(5)

          if p.poll() is not None:
            break

          current_files = self.get_current_files()

          if len(current_files) > 0:
            newest_file = os.path.join(self.dst_path, current_files[0])

            mod_time = os.path.getmtime(newest_file)
            if newest_file == last_known_file:
              if mod_time > last_mod_time:
                last_progress_time = time.time()
              elif time.time() - last_progress_time > self.max_timeout:
                warning(self.cam_id, f"No file update for over {self.max_timeout} seconds, killing ffmpeg...")
                p.kill()
                break
            else:
              last_known_file = newest_file
              last_mod_time = mod_time
              last_progress_time = time.time()

          else:
            time.sleep(1)
            current_files = self.get_current_files()
            if len(current_files) == 0:
              p.kill()
              break

      except Exception as e:
        exception(e)

      self.clear()
      warning(self.cam_id, "streaming interrupted, wait to retry...")
      time.sleep(5)


class VideoRecorder:
  def __init__(self, path_configuration):
    with open(path_configuration, 'r') as fp:
      self.configuration = json.load(fp)
    self.daemons = []

    for cam_id, cam_config in self.configuration["cam"].items():
      cam = VideoCameraCaptureDaemon(
        cam_id, cam_config["url"],
        self.configuration["path"]["tmp"],
        self.configuration.get("max_video_len", 60),
        self.configuration.get("transport", "tcp")
      )
      self.daemons.append(cam)

    if "motion" in self.configuration:
      self.daemons.append(MotionDetectorDaemon(configuration=self.configuration["motion"]))

    self.queue = TouchedFilePathQueue(self.configuration["path"]["tmp"], period=5, touched_timeout=5)
    self.cleaner_timer = RunCounter(1000, self.clean_old_videos)

  def start(self):
    for d in self.daemons:
      d.start()

    time.sleep(10)

    while(True):
      try:
        file_name, file_path = self.queue.pop()
        debug("pop", file_name, file_path)
        self.process_file(file_name, file_path)
        self.cleaner_timer.run()
      except Exception as e:
        exception(e)
        time.sleep(1)

  def process_file(self, file_name, file_path):
    split = file_name.split("___")
    if len(split) == 3:
      cam_id = split[0]
      video_date = split[1]
      video_file_name = split[2]
    else:
      warning("wrong file format, removing", file_name, file_path)
      os.remove(file_path)

    match = re.match(r"(\d{2})\-(\d{2})\-(\d{2})\.mp4", video_file_name)
    if not match:
      warning("Invalid filename format")
      video_file_name_split = video_file_name.split(".")
      video_file_name = f"{video_file_name_split[0]}-{video_file_name_split[0]}.{video_file_name_split[1]}"
    else:
      hh, mm, ss = map(int, match.groups())
      start_time = datetime.datetime(2000, 1, 1, hh, mm, ss)
      end_time = start_time + datetime.timedelta(seconds=self.configuration["max_video_len"])
      video_file_name = f"{start_time.strftime('%H.%M.%S')}-{end_time.strftime('%H.%M.%S')}.mp4"

    video_base_path = os.path.join(self.configuration["path"]["video"], cam_id, video_date)
    video_file_path = os.path.join(video_base_path, video_file_name)

    os.makedirs(video_base_path, exist_ok=True)
    shutil.copy(file_path, video_file_path)
    debug("CP", file_path, "=>", video_file_path)

    if "motion" in self.configuration and cam_id in self.configuration["motion"]:
      motion_file_path = os.path.join(self.configuration["motion"]["src"], f"{cam_id}___{video_date}___{video_file_name}")
      shutil.move(file_path, motion_file_path)
      debug("MV", file_path, "=>", motion_file_path)
    else:
      os.remove(file_path)
      debug("RM", file_path)

  def clean_old_videos(self):
    try:
      days = self.configuration.get("video_retention_period", 7)
      cmd = "find {} -mtime +{} -type f -delete".format(self.configuration["path"]["video"], days)
      debug("cmd", cmd)
      os.system(cmd)
    except Exception as e:
      exception(e, cmd)


class RTSPVideoPlayer:
  def __init__(self, rtsp_url, name=None):
    self.rtsp_url = rtsp_url
    if name is None:
      name = rtsp_url
    self.name = name
    self.cap = None
    self.is_running = False
    self.fps = FPSCounter(period=10, tag=f"{name}", printer=info, round_value=1)

  def open(self):
    info("Opening...", self.rtsp_url)
    self.cap = cv2.VideoCapture(self.rtsp_url)
    if not self.cap.isOpened():
      error("Failed to open RTSP URL", self.rtsp_url)
      self.cap = None
    else:
      info("Opened", self.rtsp_url)

  def close(self):
    if self.cap:
      info("Closing RTSP", self.rtsp_url)
      try:
        self.cap.release()
      except:
        pass
      self.cap = None
    try:
      cv2.destroyWindow(self.window_name)
    except:
      pass

  def run(self):
    self.is_running = True
    while(self.is_running):
      self.loop()

  def loop(self):
    if self.cap is None:
      self.open()
      if self.cap is None:
        time.sleep(1)
        return

    ret, frame = self.cap.read()
    if not ret or frame is None:
      error("Failed to read frame, reconnecting...")
      self.close()
      time.sleep(1)
      return

    cv2.imshow(self.name, frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
      info("Quit key pressed, stopping player")
      self.close()
      self.is_running = False
    self.fps.update()

  def finalise(self):
    self.close()


if __name__ == '__main__':
  VideoRecorder("./cams.json").start()