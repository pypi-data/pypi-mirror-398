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

import boto3

from sciveo.tools.logger import *


class S3Tree:
  def __init__(self, bucket_name):
    self.s3 = boto3.client('s3')
    self.bucket_name = bucket_name
    self.paginator = self.s3.get_paginator('list_objects_v2')
    self.objects = []
    self.tree = {}
    self.keys = []

  def load(self, prefix=""):
    page_iterator = self.paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)
    for i, page in enumerate(page_iterator):
      if 'Contents' in page:
        debug("page", i, "read", len(page['Contents']))
        for obj in page['Contents']:
          self.add_object(obj)

  def add_object(self, obj):
    self.objects.append(obj)
    self.keys.append(obj["Key"])
    key_split = obj["Key"].split("/")
    sub_tree = self.tree
    for key_split_level in key_split:
      sub_tree.setdefault(key_split_level, {})
      sub_tree = sub_tree[key_split_level]
    sub_tree["obj"] = obj

  def delete_objects(self, object_list):
    try:
      rd = self.s3.delete_objects(Bucket=self.bucket_name, Delete={'Objects': object_list})
      info("deleted {} / {} objects".format(len(rd['Deleted']), len(object_list)))
    except Exception as e:
      error(e, "delete_objects", object_list)
