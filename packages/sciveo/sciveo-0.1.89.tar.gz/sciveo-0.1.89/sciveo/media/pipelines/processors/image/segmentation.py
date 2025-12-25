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

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import os
import cv2
import numpy as np
from PIL import Image

from transformers import pipeline

from sciveo.tools.common import *
from sciveo.media.pipelines.processors.tpu_base import *


class ImageSegmentation(TPUBaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)
    self.default.update({
      "num_segments": 5
    })

    self.num_segments = self.get("num_segments", 2, 20)

    TPU = {
      "cpu": "cpu",
      "cuda": "cuda:0" # TODO: fixed cuda:0?
    }[os.environ.get("MEDIA_PROCESSING_BACKEND", "cpu")]

    self.pipe = pipeline("mask-generation", model="facebook/sam-vit-huge", device=TPU)
    self.progress_per_media = self.max_progress

  def draw_mask(self, mask, ax):
    color = np.concatenate([np.random.random(3), np.array([0.6])], axis=0)
    h, w = mask.shape[-2:]
    mask_image = mask.reshape(h, w, 1) * color.reshape(1, 1, -1)
    ax.imshow(mask_image)

  def draw_masks(self, image, masks, image_local_path):
    plt.imshow(image)
    ax = plt.gca()
    ax.set_autoscale_on(False)
    for mask in masks:
      self.draw_mask(mask, ax)
    plt.axis("off")
    plt.show()
    plt.savefig(image_local_path)

  def process(self, media):
    try:
      tag = f"ISEGM"
      self.media = media
      self.local_path = self.media["local_path"]
      image_local_path = self.add_suffix_to_filename(self.local_path, tag)

      frame = cv2.imread(self.local_path)
      image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

      outputs = self.pipe(image, points_per_batch=64)

      masks = outputs["masks"][:self.num_segments] # Masks ordered by confidence score. TODO: Consider also optional confidence threshold
      self.draw_masks(frame, masks, image_local_path)

      del masks
      del outputs

      self.next_content(self.media, tag, image_local_path, w=frame.shape[1], h=frame.shape[0], name=f"segments {self.num_segments}")
    except Exception as e:
      exception(e, self.media)
    return self.media

  def content_type(self):
    return "image"

  def name(self):
    return "image-segmentation"
