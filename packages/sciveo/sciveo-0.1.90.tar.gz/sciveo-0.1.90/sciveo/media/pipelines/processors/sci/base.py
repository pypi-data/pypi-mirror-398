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
import boto3
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd
import tensorflow as tf

from sciveo.tools.os import mkdirs
from sciveo.tools.logger import *
from sciveo.tools.common import *
from sciveo.media.pipelines.processors.base import *


class SciBaseProcessor(BaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)
    self.s3 = boto3.client('s3')

  def df_to_html(self, df):
    return df.to_html(classes='table table-striped table-bordered table-hover').replace("\n", "")

  def describe_df(self, df):
    return self.df_to_html(df.describe().transpose()[["count", "min", "max", "mean", "std", "25%", "50%", "75%"]])

  # TODO: Move all plots to separate Plot (perhaps in engine) component(s)
  def plot_df(self, df, image_local_path, name="", dpi=100, width=640, height=480):
    plt.figure(dpi=dpi)
    ax = df.plot(figsize=((int(width)/dpi, int(height)/dpi)))
    ax.set_xlabel(df.index.name)
    ax.set_ylabel('amplitude')
    ax.set_title(name)
    ax.legend(title=name, loc='upper left')

    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig(image_local_path, format='png', dpi=dpi, bbox_inches='tight', pad_inches=0)
    plt.close()

  def download_content(self, job, base_path):
    for content in job['content']:
      if "bucket" in content and "key" in content:
        # TODO: AUTH on s3 remote path, pipeline job should provide the authorized user guids list!!!
        remote_path, local_path, local_file_name = self.content_path(content, base_path)
        if os.path.isfile(local_path):
          debug("SKIP", local_path)
        else:
          debug("S3 DWN", content["bucket"], remote_path, local_path)
          self.s3.download_file(content["bucket"], remote_path, local_path)

  def content_path(self, content, base_path):
    remote_path = f"{content['owner']}/{content['key']}"
    local_file_name = content['key'].replace("/", "-")
    local_path = os.path.join(base_path, local_file_name)
    return remote_path, local_path, local_file_name

  def new_content(self, parent_content, content_type, name, content_fields={}):
    guid = f"{content_type}-{self.new_guid()}"
    content = {
      "name": name,
      "guid": guid,
      "content_type": content_type,
      "owner": parent_content['owner'],
      "parent": parent_content['guid'],
      "processor": self.name(),
      "layout": {"name": self.name(), **self["layout"]}
    }
    content.update(content_fields)
    return content

  def content_text(self, parent_content, name, content_text):
    return self.new_content(parent_content, "text", name, content_fields={"content_text": content_text})

  def content_image(self, content, name, base_path):
    guid = f"image-{self.new_guid()}"
    key = f"image/{guid}.png"
    image_local_path = os.path.join(base_path, key.replace("/", "-"))

    return {
      "name": f"Plot {name}",
      "guid": guid,
      "content_type": "image",
      "local_path": image_local_path,
      "key": key,
      "bucket": "smiveo-images",
      "owner": content['owner'],
      "parent": content['guid'],
      "processor": self.name(),
      "layout": {"name": self.name(), **self["layout"]},
    }

  def content_file(self, content, file_name, local_path, data={}):
    guid = f"file-{self.new_guid()}"
    key = f"file/{guid}-{file_name}"

    data.update({
      "info": {
        "size": os.path.getsize(local_path)
      }
    })

    return {
      "name": file_name,
      "guid": guid,
      "content_type": "file",
      "local_path": local_path,
      "key": key,
      "bucket": "smiveo-file",
      "owner": content['owner'],
      "parent": content['guid'],
      "processor": self.name(),
      "layout": {"name": self.name(), **self["layout"]},
      "data": data
    }

  def content_next_df_plot(self, content, df, y_col, base_path, name=""):
    columns_str = '-'.join(y_col)
    next_content = self.content_image(content, columns_str, base_path)
    self.plot_df(df[y_col], next_content["local_path"], name=name)
    content.setdefault("next", [])
    content["next"].append(next_content)
    return content

  def content_next_df_fft(self, content, df, y_col, base_path, dpi=100, width=640, height=480):
    columns_str = '-'.join(y_col)
    next_content = self.content_image(content, columns_str, base_path)

    fft = tf.signal.rfft(df[y_col])
    f_per_dataset = np.arange(0, len(fft))
    n_samples_h = len(df[y_col])
    hours_per_year = 24 * 365.2524
    years_per_dataset = n_samples_h / (hours_per_year)
    f_per_year = f_per_dataset / years_per_dataset

    plt.figure(figsize=((int(width)/dpi, int(height)/dpi)), dpi=dpi)
    plt.step(f_per_year, np.abs(fft))
    plt.xscale('log')
    plt.ylim([0.0, 0.5 * max(plt.ylim())])
    plt.xlim([0.1, max(plt.xlim())])
    plt.xticks([1, 365.2524], labels=['1/Year', '1/day'])
    plt.xlabel('Frequency (log scale)')
    plt.legend(title=y_col, loc='upper left')

    plt.savefig(next_content["local_path"], format='png', dpi=dpi, bbox_inches='tight', pad_inches=0)
    plt.close()

    content.setdefault("next", [])
    content["next"].append(next_content)
    return content

  def content_type(self):
    return None