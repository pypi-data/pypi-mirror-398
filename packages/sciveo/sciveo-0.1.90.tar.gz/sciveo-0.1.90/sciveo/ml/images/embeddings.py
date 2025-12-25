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
import io
import base64
from PIL import Image

import torch
from torchvision import models, transforms

import numpy as np
import pandas as pd

from transformers import AutoTokenizer, AutoModel

from sciveo.tools.logger import *
from sciveo.ml.images.base import BaseImageML


class ImageEmbedding(BaseImageML):
  def __init__(self, model_id=1, cache_dir=None, device=None) -> None:
    super().__init__(model_id, cache_dir=cache_dir, device=device)

  def init_models(self):
    self.model_name = [
      "softel-resnet18-embedding.pth",
      "softel-resnet34-embedding.pth",
      "softel-resnet50-embedding.pth",
      "softel-resnet101-embedding.pth",
      "softel-resnet152-embedding.pth",
    ][int(self.model_name)]
    self.model_path = os.path.join(self.cache_dir, self.model_name)
    if os.path.isfile(self.model_path):
      debug(self.model_name, "available", self.model_path)
    else:
      debug("DWN", self.model_name)
      s3 = boto3.client('s3')
      s3.download_file("sciveo-model", self.model_name, self.model_path)

    self.preprocessor = transforms.Compose([
      transforms.Lambda(lambda img: img.convert("RGB") if img.mode != "RGB" else img),
      transforms.Resize(256),
      transforms.CenterCrop(224),
      transforms.ToTensor(),
      transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    self.model = None

  def load_model(self):
    debug("loading model", self.model_name, self.model_path)
    self.model = torch.load(self.model_path).to(self.device)
    self.model.eval()

  def init(self):
    if self.model is None:
      self.load_model()
      self.post_init()

  def embed(self, image):
    image_tensor = self.preprocessor(image).unsqueeze(0).to(self.device)
    with torch.no_grad():
      embedding = self.model(image_tensor).to("cpu")
    return embedding.squeeze().numpy()

  def read_image(self, x):
    if isinstance(x, dict):
      if "local_path" in x:
        return Image.open(x["local_path"])
      elif "guid" in x:
        debug("not implemented guid", x["guid"])
      else:
        debug("not implemented", x)
    else:
      return Image.open(io.BytesIO(base64.b64decode(x)))

  # TODO: should conform to the BaseImageML.predict_one() on image input
  def predict_one(self, x):
    self.init()
    image = self.read_image(x)
    embedding = self.embed(image)
    if not isinstance(embedding, list):
      embedding = embedding.tolist()
    return embedding

  def predict(self, X):
    self.init()
    predictions = []
    for current_x in X:
      embedding = self.predict_one(current_x)
      if not isinstance(embedding, list):
        embedding = embedding.tolist()
      predictions.append(embedding)
    return predictions
