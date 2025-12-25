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

import unittest
import json

from sciveo.ml.dataset.object_detection import *


class TestMLDatasets(unittest.TestCase):
  def test_object_detection(self):
    HOME_PATH = os.path.expanduser("~")

    # ds = YOLODataset()
    # ds.load(f"{HOME_PATH}/data/test_yolo")
    # debug("classes", ds.classes)
    # ds.save(f"{HOME_PATH}/data/tmp/yolo-out", classes=["block", "vertical"], copy_images=False)

    ds1 = ObjectDetectionDataset()
    ds1.from_yolo(f"{HOME_PATH}/data/test_yolo")
    stats = ds1.stats()
    debug("stats", stats)
    info("distribution", stats["distribution"])
    # ds.save(f"{HOME_PATH}/data/tmp/od-1", copy_images=False)

    ds2 = ObjectDetectionDataset()
    ds2.from_yolo(f"{HOME_PATH}/data/job-1")
    stats2 = ds2.stats()
    debug("stats", stats2)
    info("distribution", stats2["distribution"])

    evaluator = EvalObjectDetectionDataset(ds1, ds2)
    scores = evaluator.evaluate()
    debug("eval", scores)


if __name__ == '__main__':
  unittest.main()
