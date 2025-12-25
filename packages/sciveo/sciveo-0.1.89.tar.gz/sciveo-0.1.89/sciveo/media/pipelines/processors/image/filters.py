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

from sciveo.tools.logger import *
from sciveo.tools.common import *
from sciveo.media.pipelines.processors.base import *


class Filters:
  def __init__(self):
    self.filters = {
      "custom": self.custom,
      "brightness": self.brightness,
      "contrast": self.contrast,
      "saturate": self.saturate,
      "hue-rotate": self.hue_rotate,
      "sepia": self.sepia,
      "opacity": self.opacity,
      "blur": self.blur,
      "invert": self.invert,
      "pencil": self.pencil,
      "sharpen": self.sharpen,
      "cartoonize": self.cartoonize,
      "emboss": self.emboss,
      "clahe": self.clahe,
      "equalize": self.equalize,
      "warm": self.warm,
      "cold": self.cold,
      "fill": self.fill,
    }

  def __call__(self, filter_name, frame, value):
    return self.filters.get(filter_name, self.none)(frame, value)

  def none(self, frame, value):
    return frame

  def fill(self, frame, value):
    return frame * value

  def warm(self, frame, value):
    intensity = value / 100
    yuv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
    yuv_image[:,:,2] = np.clip(yuv_image[:,:,2] * intensity, 0, 255)
    return cv2.cvtColor(yuv_image, cv2.COLOR_YUV2BGR)

  def cold(self, frame, value):
    intensity = value / 100
    yuv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
    yuv_image[:,:,1] = np.clip(yuv_image[:,:,1] * intensity, 0, 255)
    return cv2.cvtColor(yuv_image, cv2.COLOR_YUV2BGR)

  def clahe(self, frame, value):
    clahe = cv2.createCLAHE(clipLimit=value, tileGridSize=(8,8))
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
    frame[:,:,0] = clahe.apply(frame[:,:,0])
    return cv2.cvtColor(frame, cv2.COLOR_YUV2BGR)

  def equalize(self, frame, value):
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
    frame[:,:,0] = cv2.equalizeHist(frame[:,:,0])
    return cv2.cvtColor(frame, cv2.COLOR_YUV2BGR)

  def custom(self, frame, value):
    kernel = np.array(value)
    return cv2.filter2D(frame, -1, kernel)

  def brightness(self, frame, value):
    brightness_factor = (value / 100.0)
    return cv2.convertScaleAbs(frame, alpha=brightness_factor, beta=0)

  def contrast(self, frame, value):
    contrast_factor = (value / 100.0)
    # Apply the contrast adjustment using the formula: (pixel_value - mean) * contrast_factor + mean
    gray_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mean = np.mean(gray_image)
    adjusted_image = np.int16(frame)
    adjusted_image = (adjusted_image - mean) * contrast_factor + mean
    adjusted_image = np.clip(adjusted_image, 0, 255)
    adjusted_image = np.uint8(adjusted_image)
    return adjusted_image

  def saturate(self, frame, value):
    value /= 100
    hsv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv_image)
    # Scale the saturation channel
    s = np.clip(s * value, 0, 255).astype(np.uint8)
    hsv_image = cv2.merge((h, s, v))
    return cv2.cvtColor(hsv_image, cv2.COLOR_HSV2BGR)

  def sepia(self, frame, value):
    intensity = value / 100.0
    kernel = intensity * np.matrix(
      [
        [0.272, 0.543, 0.131],
        [0.349, 0.686, 0.168],
        [0.393, 0.769, 0.189]
      ]
    )

    result = np.array(frame, dtype=np.float64)
    result = np.clip(cv2.transform(result, kernel), 0, 255).astype(np.uint8)
    return result

  # def sepia2(self, frame, value):
  #   sepia_intensity = value / 100.0
  #   kernel = sepia_intensity * np.array(
  #     [
  #       [0.393, 0.769, 0.189],
  #       [0.349, 0.686, 0.168],
  #       [0.272, 0.534, 0.131]
  #     ]
  #   )

  #   # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
  #   frame = cv2.filter2D(frame, -1, kernel)

  #   # # Apply a slight desaturation effect
  #   # desaturation_factor = 0.7
  #   # sepia_image = (sepia_image * desaturation_factor).astype(np.uint8)
  #   return frame

  def invert(self, frame, value):
    return cv2.bitwise_not(frame)

  def hue_rotate(self, frame, value):
    hsv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hue_channel = hsv_image[:, :, 0]
    rotated_hue_channel = (hue_channel + value) % 180
    hsv_image[:, :, 0] = rotated_hue_channel
    return cv2.cvtColor(hsv_image, cv2.COLOR_HSV2BGR)

  def blur(self, frame, value):
    kernel_size = (value, value)
    return cv2.GaussianBlur(frame, kernel_size, 0)

  def pencil(self, frame, value):
    gray, color = cv2.pencilSketch(frame, sigma_s=60, sigma_r=0.07, shade_factor=0.1)
    return color

  def sharpen(self, frame, value):
    intensity = value / 100.0
    kernel = intensity * np.array(
      [
        [ 0, -1,  0],
        [-1,  5, -1],
        [ 0, -1,  0]
      ]
    )
    return cv2.filter2D(frame, -1, kernel)

  def emboss(self, frame, value):
    intensity = value / 100.0
    kernel = intensity * np.array(
      [
        [-2, -1, 0],
        [-1,  1, 1],
        [ 0,  1, 2]
      ]
    )
    return cv2.filter2D(frame, -1, kernel)

  def opacity(self, frame, value):
    alpha = int(value * 255)
    # Create mask with alpha channel
    mask = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
    mask[:, :, 3] = alpha
    # Apply mask to original image
    out = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
    return cv2.addWeighted(mask, value, out, 1 - value, 0)

  def cartoonize(self, frame, value):
    num_down = value.get("downsample", 2)
    num_bilateral = value.get("bilateral", 7)
    # downsample image using Gaussian pyramid
    img_color = frame
    for i in range(num_down):
      img_color = cv2.pyrDown(img_color)

    # repeatedly apply small bilateral filter instead of applying one large filter
    for i in range(num_bilateral):
      img_color = cv2.bilateralFilter(img_color, d=9, sigmaColor=9, sigmaSpace=7)

    # upsample image to original size
    for i in range(num_down):
      img_color = cv2.pyrUp(img_color)

    # convert to grayscale and apply median blur
    img_gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    img_blur = cv2.medianBlur(img_gray, 7)

    # detect and enhance edges
    edges = cv2.adaptiveThreshold(img_blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, blockSize=9, C=2)
    edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
    cartoon = cv2.bitwise_and(img_color, edges)

    return cartoon


class ImageFilters(BaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)
    self.filters = Filters()
    self.default.update({"JPEG_QUALITY": 100, "filters": {}})

  def get_filter_tag(self, filter_name, filter_value):
    tag = filter_name
    if isinstance(filter_value, dict):
      for k, v in filter_value.items():
        tag += f"{k}{v}"
    else:
      tag += f"{filter_value}"
    return tag.replace(" ", "").replace(".", "")

  def apply(self, frame, image_local_path):
    tag = "FLTR"
    for filter_name, filter_value in self["filters"].items():
      tag += self.get_filter_tag(filter_name, filter_value)
      debug("filter", filter_name, "filter_value", filter_value)
      frame = self.filters(filter_name, frame, filter_value)
    cv2.imwrite(image_local_path, frame, [cv2.IMWRITE_JPEG_QUALITY, self["JPEG_QUALITY"]])
    debug("apply tag", tag)
    return tag

  def process(self, media):
    try:
      self.media = media
      self.local_path = media["local_path"]
      frame = cv2.imread(self.local_path)

      image_local_path = self.add_suffix_to_filename(self.local_path, "FLTR")

      tag = self.apply(frame, image_local_path)
      self.next_content(self.media, tag, image_local_path, w=frame.shape[1], h=frame.shape[0])
    except Exception as e:
      exception(e, self.media)
    return self.media

  def content_type(self):
    return "image"

  def name(self):
    return "image-filters"

  def append_name(self):
    result = self.name()
    for filter_name, filter_value in self["filters"].items():
      result += f"-{self.get_filter_tag(filter_name, filter_value)}"
    return result

  def describe(self):
    d = super().describe()
    d["filters"] = []
    for k in self.filters.filters.keys():
      d["filters"].append(k)
    return d
