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
import cv2
import threading
import numpy as np

from sciveo.tools.logger import *
from sciveo.tools.timers import FPSCounter


class BaseInteractiveVideoPlayer:
  def __init__(self, path_video, tag):
    self.path_video = path_video
    self.file_name = os.path.basename(self.path_video)
    self.file_name_base = os.path.splitext(self.file_name)[0]
    self.path_base = os.path.dirname(self.path_video)
    self.tag = tag
    self.frame_tag = f"Video {tag}"

    self.cap = None
    self.frame = None
    self.frame_id = 0
    self.result = None
    self.progress_lock = threading.Lock()
    self.frame_lock = threading.Lock()
    self.ui_video_progress_tag = "video time progress"
    self.current_mouse_pos = (0,0)

    self.fps_ui = FPSCounter(tag="ui", period=1, print_period=600)
    self.fps_read = FPSCounter(tag="read", period=1, print_period=600)

    self.stop_threads = False
    self.threads = [
      threading.Thread(target=self.read, daemon=True)
    ]

  def _mouse_callback(self, event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE:
      self.current_mouse_pos = (x, y)

  def callback_video_progress(self, x):
    # debug("callback_video_progress", x)
    with self.frame_lock:
      # self.frame_id = cv2.getTrackbarPos(self.ui_video_progress_tag, self.frame_tag)
      self.frame_id = x

  def ui_controls(self, min_val, max_val):
    cv2.createTrackbar(self.ui_video_progress_tag, self.frame_tag, min_val, max_val, self.callback_video_progress)

  def process_frame(self, frame):
    return {}

  def read(self):
    while not self.stop_threads:
      self.fps_read.update()
      with self.progress_lock:
        current_frame_id = self.frame_id
      self.cap.set(cv2.CAP_PROP_POS_FRAMES, int(current_frame_id + 1))
      ret, current_frame = self.cap.read()
      if not ret:
        break

      current_result = self.process_frame(current_frame)

      with self.frame_lock:
        self.frame = current_frame.copy()
        self.result = current_result

      with self.progress_lock:
        self.frame_id += 1
        if self.frame_id >= self.video_frame_count:
          self.frame_id = 0
        cv2.setTrackbarPos(self.ui_video_progress_tag, self.frame_tag, self.frame_id)

  def draw(self, frame, result):
    cv2.putText(frame, f"R[{result}]", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 255), 2)

  def on_key(self, key):
    pass

  def run(self, max_display_width=1024):
    cv2.namedWindow(self.frame_tag, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(self.frame_tag, self._mouse_callback)

    self.cap = cv2.VideoCapture(self.path_video)

    self.video_fps = self.cap.get(cv2.CAP_PROP_FPS)
    self.video_frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
    self.video_duration_sec = self.video_frame_count / self.video_fps
    debug("run", self.path_video, self.tag, "fps", self.video_fps, "count", self.video_frame_count, "duration", self.video_duration_sec)

    self.ui_controls(0, self.video_frame_count)

    for thread in self.threads:
      thread.start()

    while self.cap.isOpened():
      self.fps_ui.update()
      current_frame = None
      original_current_frame = None
      current_result = None
      with self.frame_lock:
        if self.frame is not None:
          current_frame = self.frame.copy()
          original_current_frame = self.frame.copy()
          current_result = self.result.copy()

      if current_frame is not None:
        cv2.putText(current_frame, f"FPS read {round(self.fps_read.value, 1)} ui {round(self.fps_ui.value, 1)} T[{self.frame_id}] {round(self.frame_id / self.video_fps, 3)}s", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 255, 0), 4)
        self.draw(current_frame, current_result)
        height, width = current_frame.shape[:2]
        if width > max_display_width:
          display_width = max_display_width
          display_height = int(height * (max_display_width / width))
          cv2.resizeWindow(self.frame_tag, display_width, display_height)
        cv2.imshow(self.frame_tag, current_frame)

      key = cv2.waitKey(1) & 0xFF
      if key == ord("q"):
        self.stop_threads = True
        for thread in self.threads:
          thread.join()
        break
      elif key == ord("p"):
        if original_current_frame is not None:
          frame_path = os.path.join(self.path_base, f"{self.file_name_base}-{self.frame_id}.png")
          cv2.imwrite(frame_path, original_current_frame)
          debug(f"saved frame {self.frame_id} to {frame_path}")
      else:
        self.on_key(key)

    self.cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
  video_player = BaseInteractiveVideoPlayer(os.environ["PATH_VIDEO_FILE"], "base video player")
  video_player.run()