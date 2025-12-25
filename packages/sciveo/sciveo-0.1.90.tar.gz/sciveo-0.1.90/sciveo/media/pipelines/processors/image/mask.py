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
from PIL import Image
import numpy as np

import torch
from torchvision import transforms

from sciveo.tools.os import replace_extension_to_filename
from sciveo.tools.common import *
from sciveo.media.pipelines.processors.tpu_base import *
from sciveo.media.pipelines.processors.image.filters import Filters


class ForegroundMask:
  def __init__(self):
    torch.hub.set_dir(os.path.join(os.environ['MEDIA_MODELS_BASE_PATH'], "models/"))
    self.model = torch.hub.load('pytorch/vision:v0.6.0', 'deeplabv3_resnet101', pretrained=True)
    self.model.eval().to(os.environ.get("MEDIA_PROCESSING_BACKEND", "cpu"))

  def predict(self, image):
    preprocess = transforms.Compose([
      transforms.ToTensor(),
      transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    input_tensor = preprocess(Image.fromarray(image)).to(os.environ.get("MEDIA_PROCESSING_BACKEND", "cpu"))
    input_batch = input_tensor.unsqueeze(0)

    with torch.no_grad():
      output = self.model(input_batch)['out'][0]
    output_predictions = output.argmax(0)

    # create a binary (black and white) mask of the profile foreground
    mask = output_predictions.byte().cpu().numpy()
    background = np.zeros(mask.shape)
    bin_mask = np.where(mask, 255, background).astype(np.uint8)

    if image.shape[2] > 1:
      bin_mask = np.repeat(bin_mask[:, :, np.newaxis], image.shape[2], axis=2)

    del input_tensor
    del input_batch
    del output
    del output_predictions

    return bin_mask


class ImageFGBGFilter(TPUBaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)
    self.filters = Filters()
    self.mask = ForegroundMask()
    self.default.update({"JPEG_QUALITY": 100, "height": 720, "filters": {"FG": [], "BG": []}})

  def post_process(self):
    del self.mask.model
    self.clear()

  def get_filters_groups(self):
    if isinstance(self["filters"], dict):
      return [self["filters"]]
    elif isinstance(self["filters"], list):
      return self["filters"]
    else:
      return self["filters"]

  def process(self, media):
    try:
      self.media = media
      self.local_path = media["local_path"]

      image = cv2.cvtColor(cv2.imread(self.local_path), cv2.COLOR_BGR2RGB)
      h, w = get_frame_resolution(image, self["height"])
      image = cv2.resize(image, (w, h), interpolation=cv2.INTER_AREA)

      mask = self.mask.predict(image)

      filters_groups = self.get_filters_groups()
      for filters in filters_groups:
        tag = ""
        masked = {"FG": mask & image, "BG": (~mask) & image}
        for mask_name in masked.keys():
          tag += f"{mask_name}"
          for f in filters.get(mask_name, []):
            masked[mask_name] = self.filters(f[0], masked[mask_name], f[1])
            tag += f"{f[0]}{f[1]}"

        filtered = masked["FG"] | masked["BG"]

        image_local_path = self.add_suffix_to_filename(self.local_path, tag)
        image_local_path = replace_extension_to_filename(image_local_path, "png")

        cv2.imwrite(
          image_local_path,
          cv2.cvtColor(filtered, cv2.COLOR_RGB2BGR),
          [cv2.IMWRITE_JPEG_QUALITY, self["JPEG_QUALITY"]]
        )

        self.next_content(self.media, tag, image_local_path, w=w, h=h)
    except Exception as e:
      exception(e, self.media)
    return self.media

  def content_type(self):
    return "image"

  def name(self):
    return "image-fgbg-filter"

  def append_name(self):
    result = self.name()
    filters_groups = self.get_filters_groups()
    for filters in filters_groups:
      for k, list_filters in filters.items():
        result += f"-{k}"
        for f in list_filters:
          result += f"{f[0]}{f[1]}"
    return result
