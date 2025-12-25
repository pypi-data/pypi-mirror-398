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
import copy


def split_sized(arr, chunk_size, residual=True):
  result = []
  num_sets = int(len(arr) / chunk_size)
  from_idx = 0
  to_idx = 0
  for i in range(num_sets):
    to_idx = from_idx + chunk_size
    result.append(arr[from_idx:to_idx])
    from_idx = to_idx

  if residual:
    result.append(arr[from_idx:])

  return result


def split_ratios(arr, ratios=[0.75, 0.20, 0.05]):
  if sum(ratios) != 1.0:
    raise Exception("invalid ratios sum: {}".format(sum(ratios)))

  ratios_idx = []
  current_id = 0
  for r in ratios:
    ratios_idx.append(current_id)
    current_id += int(len(arr) * r)

  result = []
  for i in range(1, len(ratios_idx)):
    result.append(arr[ratios_idx[i - 1] : ratios_idx[i]])
  result.append(arr[ratios_idx[i]:])

  return result


def split_dataset(arr, ratios={"train": 0.85, "val": 0.10, "test": 0.05}):
  ratios_keys = []
  ratios_values = []
  for k, v in ratios.items():
    ratios_keys.append(k)
    ratios_values.append(v)

  split_keys = split_ratios(arr, ratios_values)

  dataset = {}
  for i, k in enumerate(ratios_keys):
    dataset[k] = split_keys[i]
  return dataset


def copy_dict_values(src, dst, keys):
  for k in keys:
    if k in src:
      dst[k] = src[k]


"""
 Search d2 keys into d1, when found, merge these keys recursive into the section found.
"""
def merge_dicts(d1, d2):
  for k, v in d1.items():
    if k in d2:
      if isinstance(v, dict):
        merge_dicts(v, d2[k])
      else:
        d1[k] = d2[k]
    else:
      if isinstance(v, dict):
        merge_dicts(v, d2)
  return d1

def merge_dicts2(d1, d2, r={}):
  for k, v in d1.items():
    r[k] = copy.deepcopy(v)
    if k in d2:
      if isinstance(v, dict):
        merge_dicts2(v, d2[k], r[k])
      else:
        d1[k] = d2[k]
        r[k] = copy.deepcopy(d2[k])
    else:
      if isinstance(v, dict):
        merge_dicts2(v, d2, r[k])
      else:
        for k2, v2 in d2.items():
          if k2 not in d1:
            r[k2] = copy.deepcopy(v2)
  return r


def split_sized(arr, chunk_size, residual=True):
  result = []
  num_sets = int(len(arr) / chunk_size)
  from_idx = 0
  to_idx = 0
  for i in range(num_sets):
    to_idx = from_idx + chunk_size
    result.append(arr[from_idx:to_idx])
    from_idx = to_idx

  if residual:
    result.append(arr[from_idx:])

  return result

def split_ratios(arr, ratios=[0.75, 0.20, 0.05]):
  if sum(ratios) != 1.0:
    raise Exception("invalid ratios sum: {}".format(sum(ratios)))

  ratios_idx = []
  current_id = 0
  for r in ratios:
    ratios_idx.append(current_id)
    current_id += int(len(arr) * r)

  result = []
  for i in range(1, len(ratios_idx)):
    result.append(arr[ratios_idx[i - 1] : ratios_idx[i]])
  result.append(arr[ratios_idx[i]:])

  return result

def split_dataset(arr, ratios={"train": 0.85, "val": 0.10, "test": 0.05}):
  ratios_keys = []
  ratios_values = []
  for k, v in ratios.items():
    ratios_keys.append(k)
    ratios_values.append(v)

  split_keys = split_ratios(arr, ratios_values)

  dataset = {}
  for i, k in enumerate(ratios_keys):
    dataset[k] = split_keys[i]
  return dataset