#
# Pavlin Georgiev, Softel Labs
#
# This is a proprietary file and may not be copied,
# distributed, or modified without express permission
# from the owner. For licensing inquiries, please
# contact pavlin@softel.bg.
#
# 2023
#

import os
import datetime
import uuid
import random
import string

from sciveo.tools.logger import *
from sciveo.tools.formating import format_memory_size


def new_guid_uuid():
  return datetime.datetime.now().strftime("%Y%m%d%H%M%S") + "-" + str(uuid.uuid4()).replace("-", "")

def random_token(num_characters):
  characters = string.ascii_letters + string.digits
  return ''.join(random.choices(characters, k=num_characters))

def new_guid(num_characters=32):
  return datetime.datetime.now().strftime("%Y%m%d%H%M%S") + "-" + random_token(num_characters)


class HardwareInfo:
  def __init__(self):
    self.data = {}

    self.get_cpu()
    self.get_ram()

  def __call__(self):
    return self.data

  def get_ram(self):
    try:
      self.data["RAM"] = format_memory_size(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES'))
    except Exception:
      pass

  def get_cpu(self):
    list_keys = ["model name", "stepping", "cpu MHz", "cache size", "siblings", "cpu cores", "bogomips"]
    try:
      self.data["CPU"] = {"count": os.cpu_count()}

      cpu_info = {}
      with open('/proc/cpuinfo', 'r') as file:
        lines = file.readlines()

      for line in lines:
        if ':' in line:
          key, value = map(str.strip, line.split(':', 1))
          if key in list_keys:
            cpu_info[key] = value

      self.data["CPU"]["info"] = cpu_info
    except Exception:
      return
