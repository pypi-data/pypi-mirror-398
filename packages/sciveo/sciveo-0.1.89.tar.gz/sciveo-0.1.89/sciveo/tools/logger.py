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
import logging
import inspect
from threading import Lock

from sciveo.tools.configuration import GlobalConfiguration


SCIVEO_LOGGER_NAME = "sciveo-log"

_sciveo_global_config = GlobalConfiguration.get()
_sciveo_log_min_level = _sciveo_global_config["SCI_LOG_LEVEL"]
_sciveo_log_lock = Lock()

def _sciveo_get_logger(name):
  logger = logging.getLogger(name)
  if not logger.hasHandlers():
    with _sciveo_log_lock:
      if not logger.hasHandlers():
        log_min_level = logging.getLevelName(_sciveo_log_min_level)
        if (isinstance(log_min_level, str) and log_min_level.startswith("Level")):
          log_min_level = "DEBUG"
        elif isinstance(log_min_level, int) and log_min_level < 10:
          log_min_level = "DEBUG"
        logger.setLevel(log_min_level)

        formatter = logging.Formatter('%(asctime)s [%(thread)d] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        logger.propagate = False
  return logger

def _sciveo_append_classname(*args):
  frame = inspect.currentframe().f_back.f_back
  class_name = frame.f_locals.get('self', None).__class__.__name__ if 'self' in frame.f_locals else None
  if class_name is not None:
    args = (class_name,) + args
  return args

def debug(*args):
  _sciveo_get_logger(SCIVEO_LOGGER_NAME).debug(_sciveo_append_classname(*args))
def info(*args):
  _sciveo_get_logger(SCIVEO_LOGGER_NAME).info(_sciveo_append_classname(*args))
def warning(*args):
  _sciveo_get_logger(SCIVEO_LOGGER_NAME).warning(_sciveo_append_classname(*args))
def error(*args):
  _sciveo_get_logger(SCIVEO_LOGGER_NAME).error(_sciveo_append_classname(*args))
def critical(*args):
  _sciveo_get_logger(SCIVEO_LOGGER_NAME).critical(_sciveo_append_classname(*args))
def exception(e, *args):
  _sciveo_get_logger(SCIVEO_LOGGER_NAME).exception(_sciveo_append_classname(*args))