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
import sys
import time
from sciveo.tools.logger import *

def mkdirs(path):
  if not os.path.exists(path):
    os.makedirs(path)
  # else:
  #   debug("mkdirs", path, "exists")

def file_makedirs(file_path):
  return mkdirs(os.path.dirname(file_path))

def touched(path):
  try:
    last_touched = time.time() - os.path.getmtime(path)
  except Exception:
    last_touched = sys.maxsize
  return last_touched

def rm_file(local_path, tag=""):
  try:
    os.remove(local_path)
    debug(tag, "RM", local_path)
  except FileNotFoundError as e:
    exception(e, tag, local_path)
  except Exception as e:
    exception(e, tag, local_path)

def file_name_split(file_path):
  directory, file_name = os.path.split(file_path)
  name, extension = os.path.splitext(file_name)
  return name, extension

def add_suffix_to_filename(file_path, siffix):
  directory, file_name = os.path.split(file_path)
  name, extension = os.path.splitext(file_name)
  new_file_name = f"{name}-{siffix}{extension}"
  new_file_path = os.path.join(directory, new_file_name)
  return new_file_path

def replace_extension_to_filename(file_path, new_ext):
  directory, file_name = os.path.split(file_path)
  name, extension = os.path.splitext(file_name)
  new_file_name = f"{name}.{new_ext}"
  new_file_path = os.path.join(directory, new_file_name)
  return new_file_path

def run_system_cmd(cmd):
  try:
    debug("SYSTEM start [", cmd, "]")
    os.system(cmd)
    debug("SYSTEM finished [", cmd, "]")
  except Exception as e:
    exception(e, "SYSTEM FAILED [", cmd, "]")