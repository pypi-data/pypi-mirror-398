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
import cv2
import io
import base64
from PIL import Image

import torch
from torchvision import models, transforms

import numpy as np
import pandas as pd

from transformers import AutoTokenizer, AutoModel

from sciveo.tools.logger import *
from sciveo.ml.base import BaseML


class TextEmbedding(BaseML):
  def __init__(self, model_name='softel/sentence-base-v0.3', cache_dir=None, device=None) -> None:
    super().__init__(model_name=model_name, cache_dir=cache_dir, device=device)
    self.pipe = None
    self.tokenizer = None
    self.max_tokens = 512
    self.overlap = 128
    self.hidden = False

  def load_model(self):
    debug("loading model", self.model_name)
    self.pipe = AutoModel.from_pretrained(
        self.model_name,
        cache_dir=self.cache_dir
    )#.to(self.device)
    self.tokenizer = AutoTokenizer.from_pretrained(
      self.model_name,
      cache_dir=self.cache_dir
    )

  def init(self):
    if self.pipe is None or self.tokenizer is None:
      self.load_model()
      self.post_init()

  def get_tokens_count(self, text):
    return len(self.tokenizer(text, padding=False, truncation=False, return_tensors=None)['input_ids'])

  def chunk_text(self, text):
    tokens = self.tokenizer(text, padding=False, truncation=False, return_tensors=None)['input_ids']
    chunks = []
    for i in range(0, len(tokens), self.max_tokens - self.overlap):
      chunk = tokens[i:i + self.max_tokens]
      chunks.append(self.tokenizer.decode(chunk, skip_special_tokens=True))
      if len(chunk) < self.max_tokens:
        break
    return chunks

  def get_chuncked_embeddings(self, text):
    chunks = self.chunk_text(text)
    embeddings = []
    for chunk in chunks:
      embedding = np.array(self.get_sentence_embedding(chunk))
      embeddings.append(embedding)
    return np.mean(np.array(embeddings), axis=0)

  def get_sentence_embedding(self, text):
    while(True):
      try:
        return self.embed(text)
      except:
        text = text[:len(text) - 8]

  def get_embedding(self, text):
    total_tokens = self.get_tokens_count(text)
    if total_tokens<=self.max_tokens:
      return self.get_sentence_embedding(text).tolist()
    else:
      return self.get_chuncked_embeddings(text).tolist()

  def get_chunks_embedding(self, chunks):
    embeddings = []
    for text in chunks:
      embeddings.append(self.get_embedding(text))
    embeddings = np.array(embeddings)
    return np.mean(embeddings, axis=0).tolist()

  def embed(self, text):
    inputs = self.tokenizer.encode_plus(text, return_tensors='pt')#.to(self.device)

    if self.hidden:
      with torch.no_grad():
        last_hidden_state = self.pipe(**inputs, output_hidden_states=True).hidden_states[-1]
        weights_for_non_padding = inputs['attention_mask'] * torch.arange(start=1, end=last_hidden_state.shape[1] + 1).unsqueeze(0)
        sum_embeddings = torch.sum(last_hidden_state * weights_for_non_padding.unsqueeze(-1), dim=1)
        num_of_none_padding_tokens = torch.sum(weights_for_non_padding, dim=-1).unsqueeze(-1)
        embeddings = sum_embeddings / num_of_none_padding_tokens
    else:
      outputs = self.pipe(**inputs)
      sequence_output = outputs[0]
      input_mask_expanded = inputs['attention_mask'].unsqueeze(-1).expand(sequence_output.size()).float()
      embeddings = torch.sum(sequence_output * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    return embeddings.detach().numpy()[0]

  def predict_one(self, x):
    self.init()
    if isinstance(x, list):
      return self.get_chunks_embedding(x)
    else:
      return self.get_embedding(x)

  def predict(self, X):
    self.init()
    predictions = []
    for current_x in X:
      embedding = self.predict_one(current_x)
      if not isinstance(embedding, list):
        embedding = embedding.tolist()
      predictions.append(embedding)
    return predictions


class SentenceEmbedding(TextEmbedding):
  def __init__(self, model_name='softel/sentence-bge-v1.3', cache_dir=None, device=None) -> None:
    super().__init__(model_name=model_name, cache_dir=cache_dir, device=device)
    self.model = None
    self.max_tokens = 8192
    self.normalize_embeddings = True

  def init(self):
    if self.model is None:
      from sentence_transformers import SentenceTransformer
      self.model = SentenceTransformer(self.model_name).to(self.device)
      self.post_init()

  def predict_one(self, x):
    return self.predict([x])[0]

  def predict(self, X):
    self.init()
    predictions = self.model.encode(X, normalize_embeddings=self.normalize_embeddings)
    return predictions.tolist()