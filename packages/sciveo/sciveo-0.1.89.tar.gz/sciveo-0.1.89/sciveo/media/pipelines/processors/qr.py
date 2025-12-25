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
import qrcode
from PIL import Image

from sciveo.media.pipelines.processors.base import *


class QRGenerator(BaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)
    self.default.update({
      "text": "https://smiveo.com",
      "width": 512,
      "height": 512,
      "bucket": "smiveo-images"
    })

  def run(self, job, input):
    width = self["width"]
    height = self["height"]

    list_frames = []

    parent_guid = job['content_id']
    guid = self.new_guid()
    key = f"{guid}.jpg"
    bucket = self["bucket"]

    image_local_path = os.path.join(self.base_tmp_path, key)

    qr = qrcode.QRCode(
      version=1,
      error_correction=qrcode.constants.ERROR_CORRECT_L,
      box_size=10,
      border=4,
    )
    qr.add_data(self["text"])
    qr.make(fit=True)
    qr_image = qr.make_image(fill_color="black", back_color="white")
    qr_image.save(image_local_path)

    media = {
      "guid": guid,
      "parent": parent_guid,
      "content_type": "image",
      "owner": job["owner"],
      "name": f"QR {self['text'][:8]}",
      "description": f"QR [{self['text']}]",
      "local_path": image_local_path,
      "w": width, "h": height,
      "height": height,
      "key": key,
      "bucket": bucket,
      "processor": self.name(),
      "layout": {"name": self.name(), "height": height, **self["layout"]}
    }

    if self["output"]:
      job["output"].append(media)
    if self["append-content"]:
      job["append-content"].append(media)
    return [media]

  def name(self):
    return "QR-generator"

  def is_append_processor(self):
    return False