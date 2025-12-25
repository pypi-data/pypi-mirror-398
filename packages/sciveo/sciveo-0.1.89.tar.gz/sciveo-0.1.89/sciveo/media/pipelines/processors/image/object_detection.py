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
from sciveo.tools.simple_counter import Timer
from sciveo.tools.common import *
from sciveo.ml.images.object_detection import ObjectDetectorYOLO
from sciveo.media.pipelines.processors.base import *


class ImageObjectDetectionProcessor(BaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)
    self.default.update({"JPEG_QUALITY": 80, "min_confidence": 0.5, "model_type": 0, "height": 720})

  def init_run(self):
    self.predictor = ObjectDetectorYOLO(model_path=[
      "yolo11x.pt", "yolo11l.pt", "yolo11m.pt", "yolo11s.pt", "yolo11n.pt",
      'softel-surveillance-yolo11X.pt', 'softel-surveillance-yolo11L.pt', 'softel-surveillance-yolo11M.pt',
      'softel-surveillance-yolo11S.pt', 'softel-surveillance-yolo11N.pt',
    ][self["model_type"]])

  def process(self, media):
    try:
      self.media = media
      self.local_path = media["local_path"]

      tag = "object-detections"
      image = self.predictor.load(self.local_path)

      image_resized = self.predictor.resize(image)
      detections = self.predictor.predict_one([image_resized], confidence_threshold=self["min_confidence"])

      image_resized = self.predictor.resize(image, h=self["height"])
      image_resized = cv2.cvtColor(image_resized, cv2.COLOR_RGB2BGR)
      self.predictor.draw(image_resized, detections[0])
      result_image_local_path = self.add_suffix_to_filename(self.local_path, tag)
      cv2.imwrite(result_image_local_path, image_resized, [cv2.IMWRITE_JPEG_QUALITY, self["JPEG_QUALITY"]])

      self.next_content(self.media, tag, result_image_local_path, w=image_resized.shape[1], h=image_resized.shape[0])
      self.next_comment(detections[0])
    except Exception as e:
      exception(e, self.media)
    return self.media

  def next_comment(self, detections):
    boxes = detections.boxes
    class_names = detections.names
    detections_json = {}
    for i, box in enumerate(boxes):
      confidence = box.conf[0].item()
      class_id = int(box.cls[0].item())
      label = class_names[class_id]
      detections_json.setdefault(label, 0)
      detections_json[label] += 1

    detections_str = ""
    for k, v in detections_json.items():
      detections_str += f"{v} {k}\n"

    self.next_content(self.media, tag="OD", content_type="comment", name=f"OD {self.predictor.model_name}", args={
      "description": detections_str,
      "content_text": f"{detections_str}\n\n{str(detections_json)}"
    })

  def content_type(self):
    return "image"

  def name(self):
    return "image-object-detection"
