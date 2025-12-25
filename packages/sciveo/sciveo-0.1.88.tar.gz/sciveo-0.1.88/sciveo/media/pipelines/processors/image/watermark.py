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

import numpy as np
import cv2

from sciveo.tools.common import *
from sciveo.media.pipelines.processors.base import *


class ImageWatermark(BaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)
    self.default.update({"JPEG_QUALITY": 100, "watermark": "SMIVEO", "height": 480, "thickness": 10, "font_scale": 3.0, "angle": 30})

  def apply(self, frame, image_local_path):
    color = (0, 0, 255)
    thickness = self["thickness"]
    font_scale = self["font_scale"]
    angle = self["angle"]
    font = cv2.FONT_HERSHEY_TRIPLEX
    alpha = 0.7
    noise_scale = 1.0

    (text_width, text_height) = cv2.getTextSize(self["watermark"], font, fontScale=font_scale, thickness=thickness)[0]

    w = frame.shape[1]
    h = frame.shape[0]

    # Determine the position of the watermark text
    (x, y) = (int((w - text_width)/2), int(h * 0.5))

    # Create an empty overlay image with the same size as the original image
    overlay = np.zeros_like(frame)

    # Add the watermark text to the overlay image with rotation
    cv2.putText(overlay, self["watermark"], (x, y), font, fontScale=font_scale, color=color, thickness=thickness, lineType=cv2.LINE_AA)
    (overlay_height, overlay_width) = overlay.shape[:2]
    center = (overlay_width // 2, overlay_height // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1)
    overlay = cv2.warpAffine(overlay, M, (overlay_width, overlay_height))

    # Create a mask of the watermark text
    gray_overlay = cv2.cvtColor(overlay, cv2.COLOR_BGR2GRAY)
    ret, mask = cv2.threshold(gray_overlay, 0, 255, cv2.THRESH_BINARY)
    mask = cv2.merge([mask, mask, mask])

    # Add Gaussian noise to the watermark text
    noise = np.zeros_like(overlay)
    cv2.randn(noise, 0, 255 * noise_scale)
    # Apply the mask to the noise image
    noise = cv2.bitwise_and(noise, mask)
    # Blend the noise image with the overlay image
    cv2.addWeighted(overlay, 0.2, noise, 0.8, 0, overlay)

    # Add the overlay image to the original image with alpha blending
    cv2.addWeighted(overlay, alpha, frame, 1, 0, frame)
    cv2.imwrite(image_local_path, frame, [cv2.IMWRITE_JPEG_QUALITY, self["JPEG_QUALITY"]])

  def process(self, media):
    try:
      self.media = media
      self.local_path = media["local_path"]
      frame = cv2.imread(self.local_path)

      tag = "WTRMRK"
      image_local_path = self.add_suffix_to_filename(self.local_path, tag)

      h, w = get_frame_resolution(frame, self["height"])
      frame_resized = cv2.resize(frame, (w, h), interpolation=cv2.INTER_AREA)

      self.apply(frame_resized, image_local_path)
      self.next_content(self.media, tag, image_local_path, w=frame_resized.shape[1], h=frame_resized.shape[0])
    except Exception as e:
      exception(e, self.media)
    return self.media

  def content_type(self):
    return "image"

  def name(self):
    return "image-watermark"
