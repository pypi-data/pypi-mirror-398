#
# Pavlin Georgiev, Softel Labs
#
# This is a proprietary file and may not be copied,
# distributed, or modified without express permission
# from the owner. For licensing inquiries, please
# contact pavlin@softel.bg.
#
# 2023
#

import io
import base64
import numpy as np
from PIL import Image

from sciveo.tools.logger import *
from sciveo.tools.configuration import GlobalConfiguration
from sciveo.ml.base import BaseML


class BaseImageML(BaseML):
  def __init__(self, model_name=1, cache_dir=None, device=None) -> None:
    super().__init__(model_name, cache_dir, device)

  def load_image(self, x):
    if isinstance(x, Image.Image) or isinstance(x, np.ndarray):
      image = x
    elif isinstance(x, dict):
      image = Image.open(x["local_path"])
    elif isinstance(x, str):
      if x.startswith("data:image"): # Base64 encoded?
        image = Image.open(io.BytesIO(base64.b64decode(image)))
      else:
        image = Image.open(x)
    else:
      warning("unknown image format")
      image = x
    return image

  def load(self, X):
    images = []
    for x in X:
      images.append(self.load_image(x))
    return images

  def predict_one(self, x):
    return self.predict([x])[0]
