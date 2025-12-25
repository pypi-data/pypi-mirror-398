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
import time
from sciveo.tools.logger import *


class FilePathQueue:
  def __init__(self, path, period=5):
    self.path = path
    self.period = period

  def filter(self, file_name, file_path):
    return True

  def pop(self):
    while(True):
      files = [f for f in os.listdir(self.path) if os.path.isfile(os.path.join(self.path, f))]
      for file_name in files:
        file_path = os.path.join(self.path, file_name)
        if self.filter(file_name, file_path):
          return file_name, file_path
      time.sleep(self.period)


class TouchedFilePathQueue(FilePathQueue):
  def __init__(self, path, period, touched_timeout):
    super().__init__(path, period)
    self.touched_timeout = touched_timeout

  def filter(self, file_name, file_path):
    return self.touched(file_path) > self.touched_timeout

  def touched(self, path):
    try:
      last_touched = time.time() - os.path.getmtime(path)
    except Exception:
      last_touched = sys.maxsize
    return last_touched