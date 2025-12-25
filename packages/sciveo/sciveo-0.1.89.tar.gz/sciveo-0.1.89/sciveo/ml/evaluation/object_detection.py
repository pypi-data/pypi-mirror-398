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

import time
import math
import numpy as np

from sciveo.tools.logger import *
from sciveo.ml.images.object_detection import *


def compute_iou_xyxy(box1, box2):
  """
    box1, box2: [x1, y1, x2, y2] format.
    Returns the IoU between the two boxes.
  """
  x1_inter = max(box1[0], box2[0])
  y1_inter = max(box1[1], box2[1])
  x2_inter = min(box1[2], box2[2])
  y2_inter = min(box1[3], box2[3])

  inter_area = max(0, x2_inter - x1_inter) * max(0, y2_inter - y1_inter)
  box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
  box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
  union_area = box1_area + box2_area - inter_area

  if union_area == 0:
    return 0.0

  return inter_area / union_area



"""

Object Detection Evaluation

Using AP and FP for object detector evaluation.
Need to define max allowed false positives (for example 0.03).
Usually max AP has relatively high FP rate, so maxing FP is on lower AP.

"""
class EvalObjectDetection:
  def __init__(self, predictions, labels, class_names):
    self.predictions = predictions
    self.labels = labels
    self.class_names = class_names

  # Convert from yolo predictions
  def from_yolo(self):
    self.converted_predictions = []
    for predicted in self.predictions:
      boxes = predicted.boxes
      class_names = predicted.names

      """
        Converted predictions of type [{"class 1": [x1,y1,x2,y2, confidence]}, ...]
        Boxes of type xyxyn + confidence
      """
      converted_prediction = {}
      for i in range(len(boxes)):
        class_id = int(boxes.cls[i].item())
        label_class = class_names[class_id]
        if label_class not in self.class_names:
          continue
        box = boxes.xyxyn[i].tolist()
        confidence = boxes.conf[i].item()
        box_confidence = box + [confidence]

        converted_prediction.setdefault(label_class, [])
        converted_prediction[label_class].append(box_confidence)
      self.converted_predictions.append(converted_prediction)

    self._convert_labels_dict()

  """
    Labels of type [ {"class 1": [ ['x1':x1,'y1':y1,'x2':x2,'y2':y2] ... ], "class 2": [ ['x1':x1,'y1':y1,'x2':x2,'y2':y2] ... ]} ... ]
    Converted Labels of type [{"class 1": [[x1,y1,x2,y2],...], "class 2": [[], [],...]...}]
    Boxes of type xyxyn
  """
  def _convert_labels_dict(self):
    self.converted_labels = []
    for label in self.labels:
      converted_label = {}
      for class_name, class_boxes in label.items():
        converted_label[class_name] = []
        for box in class_boxes:
          converted_label[class_name].append([box['x1'], box['y1'], box['x2'], box['y2']])
      self.converted_labels.append(converted_label)

  def compute_ap(self, class_name, confidence_threshold=0.0):
    """
    Calculate the Average Precision based on IoU and confidence scores.
    Returns the AP for the current class.
    """

    count_labels = 0
    true_positives = []
    false_positives = []

    for i, prediction in enumerate(self.converted_predictions):
      current_predictions = prediction.get(class_name, [])
      current_labels = self.converted_labels[i].get(class_name, [])

      count_labels += len(current_labels)

      detected = set()

      for prediction_box in current_predictions:
        if prediction_box[4] < confidence_threshold:
          continue

        max_iou = 0
        gt_match = None

        for label_box in current_labels:
          iou = compute_iou_xyxy(prediction_box[:4], label_box)
          if iou > 0.5 and iou >= max_iou:
            max_iou = iou
            gt_match = label_box

        gt_match_key = tuple([round(x, 6) for x in gt_match]) if gt_match is not None else None

        if gt_match is not None and gt_match_key not in detected:
          true_positives.append(1)
          false_positives.append(0)
          detected.add(gt_match_key)
        else:
          true_positives.append(0)
          false_positives.append(1)

    tp_cumsum = np.cumsum(true_positives)
    fp_cumsum = np.cumsum(false_positives)

    recall = tp_cumsum / (count_labels + 1e-20)
    precision = tp_cumsum / (tp_cumsum + fp_cumsum + 1e-20)

    FP = np.sum(false_positives) / (count_labels + 1e-20)

    # Compute AP using the trapezoidal rule (integrating precision over recall)
    order = np.argsort(recall)
    try:
      ap = np.trapezoid(precision[order], recall[order])
    except AttributeError:
      ap = np.trapz(precision[order], recall[order])
    return ap, FP

  # TODO: Use simple gradient-based threshold optimisation instead of current grid search.
  def calc_thresholds(self, class_name):
    list_ap = []
    list_FP = []
    list_thresholds = np.linspace(0.0, 1.0, 101).tolist()
    for i, threshold in enumerate(list_thresholds):
      ap, FP = self.compute_ap(class_name, threshold)
      list_ap.append(ap)
      list_FP.append(FP)
      if i % 10 == 0:
        debug(class_name, "threshold", threshold, "ap", ap, "FP", FP)
    return list_thresholds, list_ap, list_FP

  def threshold(self, class_name, list_thresholds, list_ap, list_FP, max_fp=0.05):
    idx = list_ap.index(max(list_ap))
    if list_FP[idx] <= max_fp:
      return list_thresholds[idx]

    for i in range(len(list_thresholds)):
      if list_FP[i] <= max_fp:
        debug("Threshold", class_name, list_thresholds[i], "AP", list_ap[i], "max_fp", max_fp, "FP", list_FP[i])
        idx = i
        break

    return list_thresholds[idx]

  def thresholds(self):
    """
      Calculate best confidence thresholds for every class.
      Predictions should be non-thresholded.
      Thresholds precission is 1/100.
    """

    result = {}
    list_thresholds = {}
    list_ap = {}
    list_FP = {}

    for class_name in self.class_names:
      list_thresholds[class_name], list_ap[class_name], list_FP[class_name] = self.calc_thresholds(class_name)
      idx = list_ap[class_name].index(max(list_ap[class_name]))
      debug("Threshold", class_name, list_thresholds[class_name][idx], "max AP", list_ap[class_name][idx])

    for max_fp in [0.01, 0.03, 0.05, 0.1]:
      result[max_fp] = {"default": 0.5}
      for class_name in self.class_names:
        class_threshold = self.threshold(class_name, list_thresholds[class_name], list_ap[class_name], list_FP[class_name], max_fp)
        result[max_fp][class_name] = class_threshold

    return result

  def evaluate(self, confidence_thresholds={"default": 0.0}):
    """
    Non-classical AP-related FP-constrained AP@IoU=0.5 calculation
    """

    aps = []
    class_ap = {}
    class_FP = {}

    info("Evaluating non-classical FP-constrained AP@IoU=0.5")

    for class_name in self.class_names:
      ap, FP = self.compute_ap(class_name, confidence_thresholds.get(class_name, confidence_thresholds["default"]))
      aps.append(ap)
      class_ap[class_name] = ap
      class_FP[class_name] = FP

    mAP = np.mean(aps)
    return {'mAP': mAP, 'AP per class': class_ap, "FP per class": class_FP}
