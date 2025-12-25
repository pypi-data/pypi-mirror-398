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
import math
import numpy as np
import cv2

from sciveo.ml.images.tools import *
from sciveo.ml.base import BaseML
from sciveo.tools.logger import *


"""
Object Detection Bounding Boxes (bbox) of type [x, y, w, h]

If need to use [x1, y1, x2, y2] need to use the inverted convertor bbox_convert_inverted().

IoU between 2 object detections: iou(bbox1, bbox2)

"""

# convert from [x, y, w, h] -> [x1, y1, x2, y2]
def bbox_convert(bbox):
  x1 = bbox[0]
  y1 = bbox[1]
  x2 = x1 + bbox[2]
  y2 = y1 + bbox[3]
  return [x1, y1, x2, y2]

# convert from [x1, y1, x2, y2] -> [x, y, w, h]
def bbox_convert_inverted(bbox):
  x = bbox[0]
  y = bbox[1]
  w = bbox[2] - x
  h = bbox[3] - y
  return [x, y, w, h]

def bbox_norm(bbox, w, h):
  return (bbox[0] / w, bbox[1] / h, bbox[2] / w, bbox[3] / h)

def bbox_denorm(bbox, w, h):
  return (int(bbox[0] * w), int(bbox[1] * h), int(bbox[2] * w), int(bbox[3] * h))

def bbox_center(bbox):
  return (int(bbox[0] + bbox[2] / 2), int(bbox[1] + bbox[3] / 2))

def bbox_area(bbox):
  return bbox[2] * bbox[3]

def iou(bbox1, bbox2):
  x1 = max(bbox1[0], bbox2[0])
  y1 = max(bbox1[1], bbox2[1])
  x2 = min(bbox1[0] + bbox1[2], bbox2[0] + bbox2[2])
  y2 = min(bbox1[1] + bbox1[3], bbox2[1] + bbox2[3])

  if x1 < x2 and y1 < y2:
    a = (x2 - x1) * (y2 - y1)
  else:
    a = 0

  a1 = bbox_area(bbox1)
  a2 = bbox_area(bbox2)
  return a / (a1 + a2 - a)

def bbox_distance(bbox1, bbox2):
  return points_distance(bbox_center(bbox1), bbox_center(bbox2))


"""

Simple Draw object detectios helpers

"""
def image_shape(image):
  return image.shape[1], image.shape[0]

# Draw label bounding boxes of type [x, y, w, h], if [x1, y1, x2, y2] then set convert=False
def draw_label_bboxes(image, bboxes, color, convert=True):
  w, h = image_shape(image)
  for bbox in bboxes:
    if convert:
      bbox = bbox_convert(bbox)
    bbox = bbox_denorm(bbox, w, h)
    cv2.rectangle(image, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2, 1)
  return image


"""

Object Detectors

"""

class ObjectDetectorBase(BaseML):
  def __init__(self, model_path, cache_dir=None, device='cpu', colors=None):
    super().__init__(model_path, cache_dir=cache_dir, device=device)
    self.model_path = model_path

    if colors is None:
      self.colors = [
        (60, 180, 75),    # Green
        (255, 255, 255),   # White
        (245, 130, 48),   # Orange
        (255, 225, 25),   # Yellow
        (0, 130, 200),    # Blue
        (230, 25, 75),    # Red
        (145, 30, 180),   # Purple
        (70, 240, 240),   # Cyan
        (240, 50, 230),   # Magenta
        (210, 245, 60),   # Lime
        (250, 190, 212),  # Pink
        (0, 128, 128),    # Teal
        (220, 190, 255),  # Lavender
        (170, 110, 40),   # Brown
        (128, 0, 0),      # Maroon
        (0, 0, 128),      # Navy
        (128, 128, 0),    # Olive
        (255, 215, 180),  # Peach
        (255, 250, 200),  # Ivory
        (170, 255, 195),  # Mint
      ]
    else:
      self.colors = colors

  def resize(self, image, h):
    ratio = max(image.shape[0], image.shape[1]) / h
    h, w = int(image.shape[0] / ratio), int(image.shape[1] / ratio)
    return cv2.resize(image, (w, h))

  def load(self, image_path):
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return image

  def read_images(self, images_paths):
    X = []
    for image_path in images_paths:
      image = self.load(image_path)
      image = self.resize(image)
      X.append(image)
    return X

  def draw_label_inverted(self, frame, label_text, x_min, y_min, color, font=cv2.FONT_HERSHEY_SIMPLEX, font_scale=0.3, font_thickness=1):
    text_size = cv2.getTextSize(label_text, font, font_scale, font_thickness)[0]
    y_offset = text_size[1] + 4
    x_offset = text_size[0] + 4
    if y_min - y_offset >= 0:
      text_background_top_left = (x_min, y_min - y_offset)
      text_background_bottom_right = (x_min + x_offset, y_min)
    else:
      text_background_top_left = (x_min, y_min)
      text_background_bottom_right = (x_min + x_offset, y_min + y_offset)

    cv2.rectangle(frame, text_background_top_left, text_background_bottom_right, color, cv2.FILLED)
    cv2.putText(frame, label_text, (x_min + 2, text_background_bottom_right[1] - 2), font, font_scale, (0,0,0), font_thickness)

  def draw_object_rectangle_xyxy(self, frame, box, label, color, alpha=0.2, filled=True):
    (x1, y1, x2, y2) = box

    if filled:
      rectangle = np.zeros((y2 - y1, x2 - x1, 3), dtype=np.uint8)
      rectangle[:] = color
      frame[y1:y2, x1:x2] = cv2.addWeighted(rectangle, alpha, frame[y1:y2, x1:x2], 1 - alpha, 0)

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness=1)

    self.draw_label_inverted(frame, label, x1, y1, color=color)

  def draw_object_rectangle_xywh(frame, box, label, color, alpha=0.2, filled=True):
    (x, y, w, h) = box
    (x1, y1, x2, y2) = x, y, x + w, y + h
    self.draw_object_rectangle_xyxy(frame, (x1, y1, x2, y2), label, color, alpha=alpha, filled=filled)


class ObjectDetectorYOLO(ObjectDetectorBase):
  def __init__(self, model_path="yolo11m.pt", cache_dir=None, device='cpu', colors=None):
    super().__init__(model_path, cache_dir=cache_dir, device=device, colors=colors)
    from ultralytics import YOLO
    if self.model_name.startswith("softel"):
      self.model_path = os.path.join(self.cache_dir, self.model_name.replace("/", "---"))
      if os.path.isfile(self.model_path):
        debug(self.model_name, "available", self.model_path)
      else:
        debug("DWN", self.model_name)
        s3 = boto3.client('s3')
        s3.download_file("sciveo-model", self.model_name, self.model_path)

    self.model = YOLO(self.model_path)

  def predict_one(self, x, confidence_threshold=0.5):
    return self.model.predict(x, device=self.device, conf=confidence_threshold, verbose=False)

  def predict(self, X, max_n=64, confidence_threshold=0.5):
    predictions = []

    num_batches = math.ceil(len(X) / max_n)

    for batch_idx in range(num_batches):
      timer = Timer()
      start_idx = batch_idx * max_n
      end_idx = min((batch_idx + 1) * max_n, len(X))

      batch_images = X[start_idx:end_idx]
      batch_predictions = self.model.predict(batch_images, device=self.device, conf=confidence_threshold, verbose=False)
      predictions.extend(batch_predictions)

      elapsed = timer.stop()
      FPS = len(batch_images) / elapsed
      debug(f"batch {batch_idx} / {num_batches}", "elapsed", elapsed, "FPS", FPS, "len", len(batch_images))

    return predictions

  def resize(self, image, h=640):
    return super().resize(image, h)

  def draw(self, image, detections, colors=None):
    if colors is None:
      colors = self.colors
    height, width = image.shape[:2]
    boxes = detections.boxes
    class_names = detections.names
    for i, box in enumerate(boxes):
      bbox = (np.array(box.xyxyn[0]) * np.array([width, height, width, height])).astype(int).tolist()

      confidence = box.conf[0].item()
      class_id = int(box.cls[0].item())
      label = class_names[class_id]
      label_text = f"{label} {int(confidence * 100)}%"

      color = colors[i % len(colors)]
      self.draw_object_rectangle_xyxy(image, bbox, label_text, color)
