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
from sciveo.media.pipelines.processors.tpu_base import *
from sciveo.media.pipelines.processors.image.generators import ImageToTextProcessor
from sciveo.media.pipelines.base import ApiContent
from sciveo.ml.video.description import VideoToText


class VideoToTextProcessor(ImageToTextProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)

  def process(self, media):
    debug("process", media['guid'])
    if self.predictor is None:
      self.predictor = VideoToText(self['model_id'], self['max_length'], self.cache_dir, self.device)
    prediction = self.predictor.predict_one(media["local_path"])
    return self.set_media(media, prediction)

  def content_type(self):
    return "video"

  def name(self):
    return "video-to-text"
