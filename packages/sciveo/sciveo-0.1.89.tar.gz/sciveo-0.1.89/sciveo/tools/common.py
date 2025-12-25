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

import re
import datetime
import os
import os.path
import json
import cv2
import skvideo.io

from sciveo.tools.logger import *


def get_resize_resoulution(FH, FW, max_dim):
  if FH <= max_dim:
    debug("get_resize_resoulution", [FH, FW], max_dim)
    return FH, FW
  h = max_dim
  w = int(FW * h / FH)
  if w % 2 == 1:
    w += 1
  return h, w

def get_frame_resolution_max_dim(frame, max_dim):
  FH = frame.shape[0]
  FW = frame.shape[1]

  if FH > FW:
    return get_resize_resoulution(FH, FW, max_dim)
  else:
    w, h = get_resize_resoulution(FW, FH, max_dim)
    return h, w

def get_frame_resolution(frame, h):
  FH = frame.shape[0]
  FW = frame.shape[1]
  return get_resize_resoulution(FH, FW, h)


class VideoWriterBase:
  def __init__(self, local_video_path, w=640):
    self.local_video_path = local_video_path
    self.w = w
    self.draw_frame = True

  def use_frame_draw(self):
    return self.draw_frame

  def write(self, frame, detections=None):
    pass

  def close(self):
    pass

class VideoWriterDummy(VideoWriterBase):
  def __init__(self, local_video_path, w=640):
    super().__init__(local_video_path, w)
    debug("init", self.local_video_path)

  def write(self, frame, detections=None):
    pass

  def close(self):
    debug("close", self.local_video_path)
    pass

class VideoWriterFFMPEG(VideoWriterBase):
  def __init__(self, local_video_path, w=640, crf='35', aux_params={}):
    super().__init__(local_video_path, w)

    output_params = {'-vcodec':'libx264', '-crf':crf, '-preset':'medium', '-vf':'format=yuv420p', '-profile:v':'baseline', '-level':'3.0'}
    output_params = {**output_params, **aux_params}
    info(self.local_video_path, output_params)
    self.out = skvideo.io.FFmpegWriter(self.local_video_path, outputdict=output_params)

  def write(self, frame, detections=None):
    self.out.writeFrame(frame[:,:,::-1])

  def close(self):
    self.out.close()
    debug("closed", self.local_video_path)

  @staticmethod
  def new(local_video_path, w=640, crf='35'):
    if int(os.environ.setdefault('PRODUCTION_MODE', "1")):
      result = VideoWriterFFMPEG(local_video_path, w, crf)
    else:
      result = VideoWriterDummy(local_video_path, w)
    return result
