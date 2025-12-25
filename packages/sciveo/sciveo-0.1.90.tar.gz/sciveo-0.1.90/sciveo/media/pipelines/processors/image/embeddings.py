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
import boto3
import cv2
from PIL import Image

import torch
from torchvision import models, transforms

from sciveo.tools.logger import *
from sciveo.tools.common import *
from sciveo.media.pipelines.processors.tpu_base import *
from sciveo.media.pipelines.base import ApiContent
from sciveo.ml.images.embeddings import ImageEmbedding


class ImageEmbeddingProcessor(TPUBaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)

    self.default.update({
      "model_id": 1,
      "output": False
    })

    self.predictor = ImageEmbedding(self['model_id'])
    self.api = ApiContent()

  def process(self, media):
    debug("process", media['guid'])
    embedding = self.predictor.predict_one(media)
    self.api.update(media, {"embedding_resnet_512": list(embedding)})
    return media

  def content_type(self):
    return "image"

  def name(self):
    return "image-embedding"
