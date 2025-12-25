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
import requests

import numpy as np
import pandas as pd

import torch
from transformers import pipeline, AutoTokenizer, AutoModel
from transformers import AutoModelForSeq2SeqLM

from annoy import AnnoyIndex
from sciveo.tools.logger import *

from sciveo.media.pipelines.base import ApiContent


class SearchTrainer:
  def __init__(self, name) -> None:
    self.name = name
    self.api = ApiContent()

    dataset_path = os.environ.get("MEDIA_DATASETS_BASE_PATH", "data")
    self.db_path = os.path.join(dataset_path, f"{self.name}.vdb")
    self.data_path = os.path.join(dataset_path, f"{self.name}.csv")

  def init(self):
    cache_dir = os.path.join(os.environ['MEDIA_MODELS_BASE_PATH'], "models/")
    self.pipe = AutoModel.from_pretrained(
      'softel/mpnet-base-v0.3',
      cache_dir=cache_dir, resume_download=True
    )
    self.tokenizer = AutoTokenizer.from_pretrained(
      'softel/mpnet-base-v0.3',
      cache_dir=cache_dir, resume_download=True
    )
    self.vdb = AnnoyIndex(768, 'euclidean')

  def api_load(self):
    fields = "fields=['guid','content_type,'owner','description','name','parent','processors']"
    url_postfix = f"content_type=image&content_type=video&~description=&{fields}"
    self.data = self.api.read(url_postfix, limit=10)
    url_postfix = f"content_type=image&processors=image-diffusion&{fields}"
    self.data += self.api.read(url_postfix, limit=10)

  def embed(self, text):
    inputs = self.tokenizer.encode_plus(text, return_tensors='pt')
    outputs = self.pipe(**inputs)
    sequence_output = outputs[0]
    input_mask_expanded = inputs['attention_mask'].unsqueeze(-1).expand(sequence_output.size()).float()
    embeddings = torch.sum(sequence_output * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    return embeddings.detach().numpy()[0]

  def train(self):
    self.api_load()


if __name__ == '__main__':
  trainer = SearchTrainer("content_search")
  trainer.api_load()
