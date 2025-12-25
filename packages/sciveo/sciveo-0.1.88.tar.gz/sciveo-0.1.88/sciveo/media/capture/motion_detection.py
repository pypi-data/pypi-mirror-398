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
import os
import shutil
import cv2
import numpy as np

from sciveo.tools.logger import *
from sciveo.tools.daemon import DaemonBase
from sciveo.media.capture.readers import VideoReaderFFMPEG
from sciveo.tools.queue import TouchedFilePathQueue
from sciveo.tools.simple_counter import SimpleStat


class MotionDetectorGrid:
  def __init__(self, grid):
    self.grid = np.array(grid)
    self.grid_mask = None
    self.zero = False

  def init_grid(self, frame):
    self.grid_mask = np.zeros_like(frame, dtype=np.float32)

    for i in range(0, self.grid_mask.shape[0]):
      for j in range(0, self.grid_mask.shape[1]):
        gi = int(self.grid.shape[0] * i / self.grid_mask.shape[0])
        gj = int(self.grid.shape[1] * j / self.grid_mask.shape[1])

        self.grid_mask[i][j] = self.grid[gi][gj]

    self.zero = self.grid_mask.sum() <= 0.0

  def apply(self, frame):
    if self.grid_mask is None:
      self.init_grid(frame)
    result = (frame * self.grid_mask).astype(np.uint8)
    return result


class VideoMotionDetector:
  def __init__(self, source_id, configuration):
    super().__init__()
    self.source_id = source_id
    self.configuration = configuration
    self.count_motion_hold = 0
    self.detection_grid = MotionDetectorGrid(self.configuration["grid"])

    self.init()

  def init(self):
    self.fgbg = cv2.createBackgroundSubtractorMOG2(history=50, varThreshold=20, detectShadows=False)

  def apply(self, frame):
    md_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    md_frame = cv2.blur(src=md_frame, ksize=(10,10))
    md_frame = self.fgbg.apply(md_frame)
    md_frame = self.detection_grid.apply(md_frame)
    return md_frame

  def check_motion(self, fgmask):
    k_motion_level = 0.5 + 0.5 * min(self.configuration["threshold_motion_hold"], self.count_motion_hold) / self.configuration["threshold_motion_hold"]
    current_threshold = self.configuration["threshold_motion"] * k_motion_level
    motion_level = np.mean(fgmask)

    self.stat.set(motion_level)

    if motion_level > current_threshold:
      self.count_motion_hold += 1
      if self.count_motion_hold >= self.configuration["threshold_motion_hold"]:
        debug(self.source_id, "motion detected", motion_level, "threshold", current_threshold)
        return True
    else:
      self.count_motion_hold = 0
    return False

  def __call__(self, list_frames):
    self.count_motion_hold = 0
    self.stat = SimpleStat()

    if len(list_frames) > 0:
      for i in range(10):
        fgmask = self.apply(list_frames[0])

    for frame in list_frames:
      try:
        if self.detection_grid.zero:
          continue

        fgmask = self.apply(frame)

        if self.check_motion(fgmask):
          return True
      except Exception as e:
        exception(e)
        time.sleep(3)

    return False


class MotionDetectorDaemon(DaemonBase):
  def __init__(self, configuration):
    super().__init__()
    self.configuration = configuration
    self.queue = TouchedFilePathQueue(self.configuration["src"], period=3, touched_timeout=3)
    self.motion_detectors = {}

  def on_motion(self, source_id, file_name, file_path, configuration):
    debug("MOTION", source_id, file_name, configuration)
    if "dst" in self.configuration:
      file_name_split = file_name.split("___")
      if len(file_name_split) >= 3:
        cam_id = file_name_split[0]
        video_date = file_name_split[1]
        video_file_name = file_name_split[2]
        video_base_path = os.path.join(self.configuration["dst"], cam_id, video_date)
        dst_file_path = os.path.join(video_base_path, video_file_name)
        os.makedirs(video_base_path, exist_ok=True)
        shutil.copy(file_path, dst_file_path)
        debug("CP", file_path, "=>", dst_file_path)

  def run(self):
    while(self.is_running):
      try:
        file_name, file_path = self.queue.pop()
        debug("pop", file_name, file_path)

        try:
          file_name_split = file_name.split("___")
          if len(file_name_split) >= 3:
            source_id = file_name_split[0]
            if source_id in self.configuration:
              configuration = self.configuration.get(source_id, { "threshold_motion": 5, "threshold_motion_hold": 5, "grid": [[0.0]] })
              md = self.motion_detectors.get(source_id, VideoMotionDetector(source_id, configuration))
              motion = md(VideoReaderFFMPEG.read(file_path, resolution=360, RGB=False, gpu_id=-1, framestep=5))
              debug("STAT", source_id, md.stat)
              if motion:
                self.on_motion(source_id, file_name, file_path, configuration)
        except Exception as e:
          exception(e)
        os.remove(file_path)
        debug("RM", file_path)
      except Exception as e:
        exception(e)
        time.sleep(5)
