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
from diffusers import StableDiffusionPipeline, LMSDiscreteScheduler
from diffusers import StableDiffusionInstructPix2PixPipeline, EulerAncestralDiscreteScheduler
from transformers import AutoProcessor, AutoModelForCausalLM
from transformers import Blip2Processor, Blip2ForConditionalGeneration

from sciveo.tools.logger import *
from sciveo.tools.common import *
from sciveo.ml.images.base import BaseImageML


class ImageToText(BaseImageML):
  def __init__(self, model_id, max_length=64, cache_dir=None, device=None) -> None:
    super().__init__(model_id, cache_dir, device)
    self.max_length = max_length

    self.models = [
      ["GIT", "softel/git-base-v1.0", "auto"],
      ["GIT", "softel/git-large-v1.0", "auto"],
      ["BLIP2", "softel/blip2-opt-2.7b-v1.0", torch.float16],
      # ["BLIP2", "softel/blip2-opt-6.7b-v1.0", torch.float16],
    ]

    model_config = self.models[model_id]
    self.dtype = model_config[2]

    if model_config[0] == "GIT":
      self.pipe = AutoProcessor.from_pretrained(model_config[1], cache_dir=self.cache_dir)
      self.model = AutoModelForCausalLM.from_pretrained(model_config[1], torch_dtype=self.dtype, cache_dir=self.cache_dir).to(self.device)
    elif model_config[0] == "BLIP2":
      self.pipe = Blip2Processor.from_pretrained(model_config[1], cache_dir=self.cache_dir)
      self.model = Blip2ForConditionalGeneration.from_pretrained(model_config[1], torch_dtype=self.dtype, device_map="auto", cache_dir=self.cache_dir)

    debug("model name", model_config[1], "on device", self.device, "dtype", self.dtype, self.model.dtype)
    self.dtype = self.model.dtype

  def predict(self, images):
    images = self.load(images)

    pixel_values = self.pipe(images=images, return_tensors="pt").pixel_values.to(self.device, self.dtype)
    ids = self.model.generate(pixel_values=pixel_values, max_length=self.max_length)
    prediction = self.pipe.batch_decode(ids, skip_special_tokens=True)

    del ids
    del pixel_values

    # debug("image description", prediction)
    return prediction
