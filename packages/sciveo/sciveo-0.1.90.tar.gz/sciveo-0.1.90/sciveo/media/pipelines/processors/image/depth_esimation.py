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
import numpy as np

import torch
from transformers import AutoImageProcessor, AutoModelForDepthEstimation

from sciveo.tools.logger import *
from sciveo.tools.os import replace_extension_to_filename
from sciveo.tools.common import *
from sciveo.media.pipelines.processors.tpu_base import *


class ImageDepthEstimation(TPUBaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)
    self.default.update({
      "JPEG_QUALITY": 80, "height": 720,
      "model_ver": 0.9
    })

    TPU = os.environ.get("MEDIA_PROCESSING_BACKEND", "cpu")

    model_name =  f"softel/depth-anything-v{self['model_ver']}"
    cache_dir = os.path.join(os.environ['MEDIA_MODELS_BASE_PATH'], "models/")
    self.image_processor = AutoImageProcessor.from_pretrained(
      model_name,
      cache_dir=cache_dir, resume_download=True
    )
    self.model = AutoModelForDepthEstimation.from_pretrained(
      model_name,
      cache_dir=cache_dir, resume_download=True
    ).to(TPU)

  def process(self, media):
    try:
      self.media = media
      self.local_path = media["local_path"]

      tag = "DEPTH"
      image_local_path = self.add_suffix_to_filename(self.local_path, tag)
      image_local_path = replace_extension_to_filename(image_local_path, "jpg")

      image = cv2.cvtColor(cv2.imread(self.local_path), cv2.COLOR_BGR2RGB)
      h, w, c = image.shape
      h, w = get_resize_resoulution(h, w, self["height"])

      inputs = self.image_processor(images=image, return_tensors="pt")
      with torch.no_grad():
        outputs = self.model(**inputs)
        predicted_depth = outputs.predicted_depth
      prediction = torch.nn.functional.interpolate(
        predicted_depth.unsqueeze(1),
        size=(h, w),
        mode="bicubic",
        align_corners=False,
      )
      output = prediction.squeeze().cpu().numpy()
      formatted = (output * 255 / np.max(output)).astype("uint8")

      image_depth = cv2.applyColorMap(formatted, cv2.COLORMAP_JET)
      cv2.imwrite(image_local_path, image_depth, [cv2.IMWRITE_JPEG_QUALITY, self["JPEG_QUALITY"]])

      self.next_content(self.media, tag=tag, local_path=image_local_path, w=w, h=h)
    except Exception as e:
      exception(e, self.media)
    return self.media

  def content_type(self):
    return "image"

  def name(self):
    return "image-depth-estimation"
