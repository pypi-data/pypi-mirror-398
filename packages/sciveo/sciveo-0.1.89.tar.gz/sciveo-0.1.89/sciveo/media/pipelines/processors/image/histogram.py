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

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import cv2

from sciveo.tools.common import *
from sciveo.media.pipelines.processors.base import *


class ImageHistogram(BaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)
    self.default.update({"width": 640, "height": 480})

  def draw(self, frame, image_local_path, w, h):
    dpi = 100
    fig = plt.figure(figsize=(int(w)/dpi, int(h)/dpi), dpi=dpi)

    ax1 = fig.add_subplot(2, 1, 1)
    ax2 = fig.add_subplot(2, 1, 2)

    color = ('b','g','r')
    for i,col in enumerate(color):
      ax1.plot(cv2.calcHist([frame], [i], None, [256], [0, 258]), color=col)

    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # ax2.plot(cv2.calcHist([gray_frame], [0], None, [256], [0, 256]))
    ax2.hist(gray_frame.ravel(), 256, [0, 258])

    ax1.set_title("RGB Histogram")
    ax1.axis(xmin=0, xmax=256)
    ax2.set_title("Gray Histogram")
    ax2.axis(xmin=0, xmax=258)

    plt.subplots_adjust(hspace=0.5)
    plt.savefig(image_local_path, dpi=dpi, bbox_inches='tight', pad_inches=0)

  def process(self, media):
    try:
      self.media = media
      self.local_path = media["local_path"]

      tag = "HIST"
      image_local_path = self.add_suffix_to_filename(self.local_path, tag)

      w, h = self["width"], self["height"]

      frame = cv2.imread(self.local_path)
      self.draw(frame, image_local_path, w, h)
      self.next_content(self.media, tag, image_local_path, w=w, h=h)

    except Exception as e:
      exception(e, self.media)
    return self.media

  def content_type(self):
    return "image"

  def name(self):
    return "image-histogram"
