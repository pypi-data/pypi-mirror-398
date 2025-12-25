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

import numpy as np
import pandas as pd

import torch
from transformers import pipeline, AutoTokenizer, AutoModel
from transformers import AutoModelForSeq2SeqLM

from annoy import AnnoyIndex

from sciveo.tools.logger import *
from sciveo.media.pipelines.processors.tpu_base import *
from sciveo.media.pipelines.queues import MediaJobState
from sciveo.media.pipelines.base import ApiContent


class AddressStandard(TPUBaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)

    self.api = ApiContent()

    cache_dir = os.path.join(os.environ['MEDIA_MODELS_BASE_PATH'], "models/")

    self.pipe = AutoModelForSeq2SeqLM.from_pretrained(
      "Hnabil/t5-address-standardizer", cache_dir=cache_dir)#.to(os.environ.get("MEDIA_PROCESSING_BACKEND", "cpu"))
    self.tokenizer = AutoTokenizer.from_pretrained("Hnabil/t5-address-standardizer", cache_dir=cache_dir)#.to(os.environ.get("MEDIA_PROCESSING_BACKEND", "cpu"))

    self.default.update({
      "address_list": [],
      "output": False
    })

  def process(self, media):
    debug("process", media['guid'])

    address_predict = {}

    for address in self["address_list"]:
      input_tokens = self.tokenizer(address, return_tensors="pt")
      output_tokens = self.pipe.generate(**input_tokens, max_length=128)
      address_predict[address] = self.tokenizer.batch_decode(output_tokens, skip_special_tokens=True)[0]

    debug("process predict", address_predict)

    media.setdefault("next", [])
    media["next"].append({
      "guid": self.new_guid(),
      "parent": media['guid'],
      "content_type": "comment",
      "content_text": self.html_dict(address_predict),
      "owner": media["owner"],
      "name": f"address converter",
      "processor": self.name()
    })

    return media

  def html_dict(self, d):
    html = "<ul>"
    for k, v in d.items():
      html += f"<li>{k} ==> {v}</li>"
    html += f"</ul><br><br>{d}"
    return html

  def content_type(self):
    return None

  def name(self):
    return "nlp-address-standard"


class AddressGeocode(TPUBaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)

    self.api = ApiContent()

    cache_dir = os.path.join(os.environ['MEDIA_MODELS_BASE_PATH'], "models/")
    dataset_path = os.environ.get("MEDIA_DATASETS_BASE_PATH", "data")

    self.pipe = AutoModel.from_pretrained(
      'softel/mpnet-base-v0.3',
      cache_dir=cache_dir, resume_download=True
    )
    self.tokenizer = AutoTokenizer.from_pretrained(
      'softel/mpnet-base-v0.3',
      cache_dir=cache_dir, resume_download=True
    )

    self.default.update({
      "address_list": [],
      "top_n": 5,
      "max_distance": 2.2,
      "output": False
    })

    self.vdb = AnnoyIndex(768, 'euclidean')
    self.vdb.load(os.path.join(dataset_path, "train_address_1K.vdb"))
    self.df_address = pd.read_csv(os.path.join(dataset_path, "train_address_1K.csv"), delimiter=";")

  def embed(self, text):
    inputs = self.tokenizer.encode_plus(text, return_tensors='pt')
    outputs = self.pipe(**inputs)
    sequence_output = outputs[0]
    input_mask_expanded = inputs['attention_mask'].unsqueeze(-1).expand(sequence_output.size()).float()
    embeddings = torch.sum(sequence_output * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    return embeddings.detach().numpy()[0]

  def process(self, media):
    debug("process", media['guid'])

    media.setdefault("next", [])
    progress_per_element = self.max_progress / max(1, len(self["address_list"])) / 2

    for address in self["address_list"]:
      address_embedding = self.embed(address)
      idx, d = self.vdb.get_nns_by_vector(address_embedding, self["top_n"], search_k=-1, include_distances=True)
      address_prediction = []
      for i, j in enumerate(idx):
        if d[i] < self["max_distance"]: # Threshold should be evaluated
          address_prediction.append([list(dict(self.df_address[['siteName', 'address', 'scan_lat', 'scan_lng']].iloc[j]).values()), d[i]])

      media["next"].append({
        "guid": self.new_guid(),
        "parent": media['guid'],
        "content_type": "comment",
        "content_text": self.html_dict(address, address_prediction),
        "owner": media["owner"],
        "name": f"address geocoding",
        "processor": self.name()
      })

      MediaJobState.queue().inc_progress(self.job_id, progress_per_element)

    return media

  def html_dict(self, address, prediction):
    html = f"<H3>{address}</H3>"
    for p in prediction:
      html += f"<H5>{p}</H5>"
    return html

  def content_type(self):
    return None

  def name(self):
    return "nlp-address-geocode"
