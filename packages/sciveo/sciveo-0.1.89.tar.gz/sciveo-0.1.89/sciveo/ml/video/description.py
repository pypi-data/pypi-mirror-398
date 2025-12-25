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
import cv2
import gc
from PIL import Image

import torch
from transformers import AutoProcessor, AutoModelForCausalLM

from sciveo.tools.common import *
from sciveo.ml.images.description import ImageToText


class VideoToText(ImageToText):
  def __init__(self, model_id, max_length=64, cache_dir=None, device=None) -> None:
    super().__init__(model_id, max_length, cache_dir, device)

  def read_video_frame(self, video_path):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
    ret, frame = cap.read()
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    cap.release()
    return frame

  def predict(self, X):
    frames = []
    for x in X:
      frames.append(self.read_video_frame(x))
    predictions = super().predict(frames)
    return predictions
