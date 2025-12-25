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
import shutil
import yaml
import json
import time
import math
import numpy as np

from sciveo.tools.logger import *
from sciveo.ml.evaluation.object_detection import *


def xcycwh_to_xyxy(bbox):
  cx, cy, w, h = bbox
  x1 = cx - w / 2
  y1 = cy - h / 2
  x2 = cx + w / 2
  y2 = cy + h / 2
  return [x1, y1, x2, y2]

def xyxy_to_xcycwh(bbox):
  x1, y1, x2, y2 = bbox
  cx = (x1 + x2) / 2
  cy = (y1 + y2) / 2
  w = x2 - x1
  h = y2 - y1
  return [cx, cy, w, h]

def bbox_from_yolo(yolo_bbox):
  yolo_bbox = [float(a) for a in yolo_bbox]
  n, cx, cy, w, h = yolo_bbox
  return xcycwh_to_xyxy([cx, cy, w, h])

def bbox_to_yolo(bbox):
  n, x1, y1, x2, y2 = bbox
  cx, cy, w, h = xyxy_to_xcycwh([x1, y1, x2, y2])
  return [n, cx, cy, w, h]


class YOLODataset:
  def __init__(self):
    self.src_path = None
    self.dst_path = None

    self.classes = {}
    self.splits = []
    self.labels = {}

  def load(self, base_path):
    self.src_path = base_path
    yaml_path = os.path.join(base_path, "data.yaml")
    if not os.path.exists(yaml_path):
      raise FileNotFoundError(f"data.yaml not found in {base_path}")

    with open(yaml_path, "r") as f:
      self.data_yaml = yaml.safe_load(f)

    self.classes = self.data_yaml.get("names", {})
    self.splits = [key for key in self.data_yaml.keys() if key not in ["names", "nc", "path"]]
    self.labels = {split: self._load_labels_for_split(base_path, split) for split in self.splits}

  def _load_labels_for_split(self, base_path, split: str):
    images_dir = self.data_yaml.get(split)
    labels_dir = images_dir.replace("images", "labels")
    if not labels_dir:
      return {}

    images_path = os.path.join(base_path, images_dir)
    labels_path = os.path.join(base_path, labels_dir)
    if not os.path.exists(labels_path):
      return {}

    annotations = {}
    for label_file in os.listdir(labels_path):
      if label_file.endswith(".txt"):
        image_id = label_file.replace(".txt", ".jpg")
        label_path = os.path.join(labels_path, label_file)

        with open(label_path, "r") as f:
          annotations[image_id] = [line.strip().split() for line in f.readlines()]

    return annotations

  def save(self, base_path, classes=[], copy_images=True):
    self.dst_path = base_path
    os.makedirs(self.dst_path, exist_ok=True)

    yaml_path = os.path.join(base_path, "data.yaml")

    if not classes:
      selected_classes = self.classes
    else:
      selected_classes = {idx: name for idx, name in self.classes.items() if name in classes}

    class_mapping = {name: new_idx for new_idx, (idx, name) in enumerate(selected_classes.items())}

    # data_yaml = {
    #   "path": "./",
    #   "names": {idx: name for idx, name in selected_classes.items()}
    # }
    # for split in self.splits:
    #   data_yaml[split] = f"images/{split}"
    # with open(yaml_path, "w") as f:
    #   yaml.dump(data_yaml, f, default_flow_style=False)

    with open(yaml_path, "w") as fp:
      fp.write("  path: ./ # dataset root dir\n")
      for split in self.splits:
        fp.write(f"  test: images/{split}\n")
      fp.write("  names:\n")
      for class_id, class_name in selected_classes.items():
        fp.write(f"    {class_id}: {class_name}\n")

    for split, images in self.labels.items():
      labels_path = os.path.join(base_path, "labels", split)
      images_path = os.path.join(base_path, "images", split)
      os.makedirs(labels_path, exist_ok=True)
      os.makedirs(images_path, exist_ok=True)

      for image_name, annotations in images.items():
        label_file_path = os.path.join(labels_path, image_name.replace(".jpg", ".txt"))

        with open(label_file_path, "w") as f:
          for annotation in annotations:
            class_id, *bbox = map(float, annotation)
            class_id = int(class_id)

            class_name = self.classes.get(class_id)
            if class_name in class_mapping:
              new_class_id = class_mapping[class_name]
              f.write(f"{new_class_id} {' '.join(map(str, bbox))}\n")

        if copy_images and self.src_path:
          src_image_path = os.path.join(self.src_path, "images", split, image_name)
          dst_image_path = os.path.join(images_path, image_name)
          if not os.path.isfile(dst_image_path):
            shutil.copy(src_image_path, dst_image_path)


"""
Object Detection Dataset

labels in splits (for example train/val/test)
every dataset split has image name as key which points to dict of classes as keys

labels[split][image_name][class_name] is a list of bounding boxes of same class
bboxes are of type nxyxy which means normalized [x1, y1, x2, y2] coordinates (upper left and down right point of the rectangle)

"""
class ObjectDetectionDataset:
  def __init__(self):
    self.classes = []
    self.splits = []
    self.labels = {}

    self.src_path = None
    self.dst_path = None

  def save(self, base_path, copy_images=True, src_path=None):
    if src_path is not None:
      self.src_path = src_path

    self.dst_path = base_path
    for split in self.splits:
      images_path = os.path.join(self.dst_path, split, "images")
      os.makedirs(images_path, exist_ok=True)

      labels_path = os.path.join(self.dst_path, split, "labels.json")
      with open(labels_path, 'w') as fp:
        json.dump(self.labels[split], fp, indent=2)

      if copy_images and self.src_path:
        src_images_path = os.path.join(self.src_path, "images", split)
        for image_path, subdirs, image_files in os.walk(src_images_path):
          for image_name in image_files:
            src_path = os.path.join(image_path, image_name)
            dst_path = os.path.join(images_path, image_name)
            if not os.path.isfile(dst_path):
              shutil.copy(src_path, dst_path)

  def from_yolo(self, base_path):
    self.src_path = base_path

    self.raw = YOLODataset()
    self.raw.load(base_path)

    self.classes = []
    for i in range(len(self.raw.classes)):
      self.classes.append(self.raw.classes[i])
    self.splits = self.raw.splits
    self.image_labels = {}
    self.labels = {}
    for split, split_labels in self.raw.labels.items():
      self.image_labels.setdefault(split, {})
      self.labels.setdefault(split, {})
      for image_id, image_labels in split_labels.items():
        self.image_labels[split].setdefault(image_id, {})
        for label in image_labels:
          class_id = int(label[0])
          class_name = self.raw.classes[class_id]
          bbox = bbox_from_yolo(label)

          self.image_labels[split][image_id].setdefault(class_name, [])
          self.image_labels[split][image_id][class_name].append(bbox)

          self.labels[split].setdefault(class_name, {})
          self.labels[split][class_name].setdefault(image_id, [])
          self.labels[split][class_name][image_id].append(bbox)

  def stats(self):
    result = {"datasets": {}, "count": {}, "distribution": {}}
    for split in self.splits:
      result["datasets"].setdefault(split, {})
      result["count"].setdefault(split, 0)
      for class_name in self.classes:
        result["datasets"][split].setdefault(class_name, 0)
        for image_name, image_labels in self.labels[split][class_name].items():
          result["count"][split] += len(image_labels)
          result["datasets"][split][class_name] += len(image_labels)

    for split in self.splits:
      result["distribution"].setdefault(split, [])
      for class_name in self.classes:
        result["distribution"][split].append({class_name: result["datasets"][split][class_name] / result["count"][split]})
      result["distribution"][split] = sorted(result["distribution"][split], key=lambda x: list(x.values())[0], reverse=True)

    return result


class EvalObjectDetectionDataset(EvalObjectDetection):
  def __init__(self, predictions, labels, split="test"):
    self.split = split
    super().__init__(predictions.image_labels[split], labels.image_labels[split], predictions.classes)
    self.from_datasets()

  """
    Converted predictions of type [{"class 1": [x1,y1,x2,y2, confidence]}, ...]
    Boxes of type xyxyn + confidence

    Converted Labels of type [{"class 1": [[x1,y1,x2,y2],...], "class 2": [[], [],...]...}]
    Boxes of type xyxyn
  """
  def from_datasets(self):
    self.converted_predictions = []
    self.converted_labels = []

    list_prediction_images = list(self.predictions.keys())
    list_prediction_images.sort()
    list_labels_images = list(self.labels.keys())
    list_labels_images.sort()
    if not all(a == b for a, b in zip(list_prediction_images, list_labels_images)):
      error("predictions and labels differ")
      return

    for image_name in list_prediction_images:
      self.converted_labels.append(self.labels[image_name])
      current_image_prediction = {}
      for class_name, class_prediction in self.predictions[image_name].items():
        current_image_prediction[class_name] = class_prediction
        for i, current_class_prediction in enumerate(current_image_prediction[class_name]):
          current_image_prediction[class_name][i].append(1.0)
      self.converted_predictions.append(current_image_prediction)
